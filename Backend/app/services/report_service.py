"""Reports list: one row per non-refunded checkout line (sale total per product line)."""

from __future__ import annotations

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.models import CheckoutItem, Invoice, RefundRecord, User
from app.services.data_service import (
    apply_created_at_range,
    apply_sort,
    paginate_query,
    parse_csv,
    serialize_report_row,
)


def _refunded_checkout_item_ids_subquery():
    return select(RefundRecord.checkout_item_id).where(RefundRecord.checkout_item_id.isnot(None))


def build_report_items_query(
    *,
    search: str | None = None,
    products: list[str] | None = None,
    provinces: list[str] | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
):
    refunded_ids = _refunded_checkout_item_ids_subquery()
    q = (
        select(CheckoutItem, Invoice, User)
        .join(Invoice, CheckoutItem.invoice_id == Invoice.id)
        .outerjoin(User, Invoice.user_id == User.id)
        .where(Invoice.status == "paid")
        .where(~CheckoutItem.id.in_(refunded_ids))
    )

    if search:
        keyword = search.strip()
        q = q.where(
            Invoice.invoice_no.ilike(f"%{keyword}%")
            | Invoice.customer_name.ilike(f"%{keyword}%")
            | CheckoutItem.product_name.ilike(f"%{keyword}%")
            | User.name.ilike(f"%{keyword}%")
        )

    if products:
        q = q.where(CheckoutItem.product_name.in_(products))

    if provinces:
        q = q.where(or_(*[Invoice.customer_address == p for p in provinces]))

    q = apply_created_at_range(q, date_from, date_to, Invoice.created_at)
    return q


def list_report_invoices(
    db: Session,
    *,
    page: int,
    limit: int,
    search: str | None = None,
    product: str | None = None,
    province: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    sort_by: str | None = None,
    sort_order: str | None = None,
):
    products = parse_csv(product)
    provinces = parse_csv(province)

    q = build_report_items_query(
        search=search,
        products=products,
        provinces=provinces,
        date_from=date_from,
        date_to=date_to,
    )

    sort_map = {
        "id": CheckoutItem.id,
        "invoiceNo": Invoice.invoice_no,
        "date": Invoice.created_at,
        "product": CheckoutItem.product_name,
        "seller": User.name,
        "amount": CheckoutItem.total,
    }
    q = apply_sort(q, sort_by, sort_order, sort_map)
    if not sort_by:
        q = q.order_by(Invoice.created_at.desc(), CheckoutItem.id.desc())

    rows, total = paginate_query(q, db, page, limit)
    result = [serialize_report_row(ci, inv, seller) for ci, inv, seller in rows]
    return result, total


def export_report_invoices(
    db: Session,
    *,
    search: str | None = None,
    product: str | None = None,
    province: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
):
    products = parse_csv(product)
    provinces = parse_csv(province)

    q = build_report_items_query(
        search=search,
        products=products,
        provinces=provinces,
        date_from=date_from,
        date_to=date_to,
    )
    q = q.order_by(Invoice.created_at.desc(), CheckoutItem.id.desc())
    rows = db.execute(q).all()
    return [serialize_report_row(ci, inv, seller) for ci, inv, seller in rows]


# Telegram / scheduled product reports (unchanged; uses report_repository).
from app.repositories.report_repository import report_repo  # noqa: E402


class ReportService:
    TELEGRAM_MAX_MESSAGE_LEN = 4096
    TELEGRAM_SAFE_MESSAGE_LEN = 3500

    def format_daily_sales_summary(
        self,
        db: Session,
        start_date=None,
        end_date=None,
        *,
        date_label: str,
        time_label: str = "7:00AM-7:00PM",
    ) -> str:
        from app.services.alert_service import _escape_telegram_html

        lines = report_repo.get_daily_sales_lines(db, start_date, end_date)
        totals = report_repo.get_daily_sales_totals(db, start_date, end_date)

        msg = f"📊 <b>Report Today</b> ({_escape_telegram_html(date_label)} : {time_label})\n\n"
        if not lines:
            msg += "<i>No sales in this period.</i>\n"
        else:
            for row in lines:
                name = _escape_telegram_html((row.get("product_name") or "").strip() or "—")
                qty = int(row.get("qty") or 0)
                unit = float(row.get("unit_price") or 0)
                line_total = float(row.get("line_total") or 0)
                msg += f". {name} : {qty} * ${unit:.2f} = ${line_total:.2f}\n"

        msg += (
            "\n-------------------------------------------\n"
            f". subtotal : ${float(totals.get('subtotal') or 0):.2f}\n"
            f". Delivery total : ${float(totals.get('delivery_total') or 0):.2f}\n"
            f". discount Total : ${float(totals.get('discount_total') or 0):.2f}\n"
            f". Total Price : ${float(totals.get('grand_total') or 0):.2f}\n"
        )
        return msg.rstrip()

    def format_summary_price(self, db: Session, start_date=None, end_date=None, label="Today") -> str:
        data = report_repo.get_summary_price(db, start_date, end_date)
        msg = f"💰 <b>Summary Price</b>\n"
        msg += f"Period: {label}\n\n"
        msg += f"Total Sales: ${data['total_sales']:.2f}\n"
        msg += f"Total Invoices: {data['total_invoices']}\n"
        msg += f"Products Sold: {data['total_products_sold']}\n"
        return msg

    def format_category_price(self, db: Session, start_date=None, end_date=None, label="Today") -> str:
        data = report_repo.get_price_by_category(db, start_date, end_date)
        msg = f"📁 <b>Summary Price by Category</b>\n"
        msg += f"Period: {label}\n\n"
        if not data:
            return msg + "No data found."
        for i, row in enumerate(data, 1):
            msg += f"{i}. {row['category_name']}\n"
            msg += f"Sales: ${row['total_sales']:.2f}\n"
            msg += f"Qty: {row['total_qty']}\n\n"
        return msg

    def format_product_price(self, db: Session, start_date=None, end_date=None, label="Today") -> str:
        data = report_repo.get_price_by_product(db, start_date, end_date)
        msg = f"📦 <b>Summary Price by Product</b>\n"
        msg += f"Period: {label}\n\n"
        if not data:
            return msg + "No data found."
        for i, row in enumerate(data, 1):
            msg += f"{i}. {row['product_name']}\n"
            msg += f"Sales: ${row['total_sales']:.2f}\n"
            msg += f"Qty: {row['total_qty']}\n\n"
        return msg

    def format_source_price(self, db: Session, start_date=None, end_date=None, label="Today") -> str:
        data = report_repo.get_price_by_source(db, start_date, end_date)
        msg = f"📍 <b>Summary Price by Source</b>\n"
        msg += f"Period: {label}\n\n"
        if not data:
            return msg + "No data found."
        for i, row in enumerate(data, 1):
            msg += f"{i}. {row['source']}\n"
            msg += f"Sales: ${row['total_sales']:.2f}\n"
            msg += f"Invoices: {row['total_invoices']}\n\n"
        return msg

    def format_payment_price(self, db: Session, start_date=None, end_date=None, label="Today") -> str:
        data = report_repo.get_price_by_payment(db, start_date, end_date)
        msg = f"💳 <b>Summary Price by Payment Method</b>\n"
        msg += f"Period: {label}\n\n"
        if not data:
            return msg + "No data found."
        for i, row in enumerate(data, 1):
            msg += f"{i}. {row['payment_method']}\n"
            msg += f"Sales: ${row['total_sales']:.2f}\n"
            msg += f"Invoices: {row['total_invoices']}\n\n"
        return msg

    def format_commission_user(self, db: Session, start_date=None, end_date=None, label="Today") -> str:
        data = report_repo.get_commission_by_user(db, start_date, end_date)
        msg = f"👤 <b>Commission by User Sold Product</b>\n"
        msg += f"Period: {label}\n\n"
        if not data:
            return msg + "No data found."
        for i, row in enumerate(data, 1):
            msg += f"{i}. {row['seller_name'] or 'Unknown'}\n"
            msg += f"Commission: ${row['total_commission']:.2f}\n"
            msg += f"Sales: ${row['total_sales']:.2f}\n"
            msg += f"Products Sold: {row['total_products_sold']}\n\n"
        return msg

    def format_delivery_type_price(self, db: Session, start_date=None, end_date=None, label="Today") -> str:
        data = report_repo.get_price_by_delivery(db, start_date, end_date)
        msg = f"🚚 <b>Summary Price by Delivery Type</b>\n"
        msg += f"Period: {label}\n\n"
        if not data:
            return msg + "No data found."
        for i, row in enumerate(data, 1):
            msg += f"{i}. {row['delivery_type']}\n"
            msg += f"Sales: ${row['total_sales']:.2f}\n"
            msg += f"Delivery Fee: ${row['total_delivery_fee']:.2f}\n"
            msg += f"Invoices: {row['total_invoices']}\n\n"
        return msg

    def format_product_report_messages(self, db: Session) -> list[str]:
        rows = report_repo.get_product_report_rows(db)
        header = "📦 <b>Product Report</b>\n\n"
        if not rows:
            return [header + "No sold or in-stock products found."]

        lines: list[str] = []
        grand_gross = 0.0
        grand_net = 0.0
        grand_total_in_stock = 0.0

        for i, row in enumerate(rows, 1):
            sold_qty = int(row["sold_qty"])
            line_net = float(row["total_price_sold"])
            line_gross = float(row.get("total_price_sold_gross") or line_net)
            grand_gross += line_gross
            grand_net += line_net
            grand_total_in_stock += row["total_price_in_stock"]
            lines.append(
                f"{i}. {row['name']}\n"
                f"Sold Qty: {sold_qty}\n"
                f"Total Price Sold: ${line_net:.2f}\n"
                f"Stock Qty: {row['stock_qty']}\n"
                f"Total Price In Stock: ${row['total_price_in_stock']:.2f}\n"
            )

        discount_usd = max(0.0, grand_gross - grand_net)
        discount_pct = (discount_usd / grand_gross * 100.0) if grand_gross > 0 else 0.0
        footer = (
            "============================\n\n"
            f"Grand Total Sold: ${grand_gross:.2f}\n"
            f"Discount USD: ${discount_usd:.2f} ({discount_pct:.2f}%)\n"
            f"Grand Total In Stock: ${grand_total_in_stock:.2f}\n\n"
        )
        return self._chunk_report_lines(header, lines, footer)

    def _chunk_report_lines(self, header: str, lines: list[str], footer: str) -> list[str]:
        chunks: list[str] = []
        current = header

        for block in lines:
            if len(current) + len(block) + 2 > self.TELEGRAM_SAFE_MESSAGE_LEN:
                chunks.append(current.rstrip())
                current = header + block
            else:
                current += block + "\n"

        if len(current) + len(footer) + 2 > self.TELEGRAM_SAFE_MESSAGE_LEN:
            chunks.append(current.rstrip())
            current = header + footer
        else:
            current += footer
        chunks.append(current.rstrip())

        return chunks


report_service = ReportService()
