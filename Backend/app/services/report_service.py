"""Reports list: one row per paid invoice with products grouped together."""

from __future__ import annotations

from datetime import date, datetime, time

from sqlalchemy import exists, or_, select
from sqlalchemy.orm import Session

from app.services.data_service import parse_iso_date
from app.utils.timezone import format_report_period_date_label

from app.models import CheckoutItem, Invoice, RefundRecord, User
from app.services.data_service import (
    apply_created_at_range,
    apply_sort,
    paginate_query,
    parse_csv,
    to_iso,
)


def _refunded_checkout_item_ids_subquery():
    return select(RefundRecord.checkout_item_id).where(RefundRecord.checkout_item_id.isnot(None))


def _active_line_exists(product_filter: list[str] | None = None):
    """Invoice has at least one checkout line that is not fully refunded."""
    refunded_ids = _refunded_checkout_item_ids_subquery()
    predicates = [
        CheckoutItem.invoice_id == Invoice.id,
        ~CheckoutItem.id.in_(refunded_ids),
    ]
    if product_filter:
        predicates.append(
            or_(*[CheckoutItem.product_name.ilike(f"%{p}%") for p in product_filter])
        )
    return exists(select(CheckoutItem.id).where(*predicates))


def build_report_invoices_query(
    *,
    search: str | None = None,
    products: list[str] | None = None,
    provinces: list[str] | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
):
    q = (
        select(Invoice, User)
        .outerjoin(User, Invoice.user_id == User.id)
        .where(Invoice.status == "paid")
        .where(_active_line_exists(products if products else None))
    )

    if search:
        keyword = search.strip()
        q = q.where(
            Invoice.invoice_no.ilike(f"%{keyword}%")
            | Invoice.customer_name.ilike(f"%{keyword}%")
            | Invoice.product_name.ilike(f"%{keyword}%")
            | User.name.ilike(f"%{keyword}%")
            | exists(
                select(CheckoutItem.id).where(
                    CheckoutItem.invoice_id == Invoice.id,
                    CheckoutItem.product_name.ilike(f"%{keyword}%"),
                )
            )
        )

    if provinces:
        q = q.where(or_(*[Invoice.customer_address == p for p in provinces]))

    q = apply_created_at_range(q, date_from, date_to, Invoice.created_at)
    return q


def serialize_report_invoice(inv: Invoice, seller: User | None = None) -> dict:
    """One report row per checkout with all products grouped in the product column."""
    return {
        "id": inv.id,
        "invoiceId": inv.id,
        "invoiceNo": inv.invoice_no,
        "date": to_iso(inv.created_at),
        "product": (inv.product_name or "").strip(),
        "productId": 0,
        "qty": 0,
        "price": 0,
        "customer": inv.customer_name or "",
        "phoneCustomer": inv.customer_phone or "",
        "seller": seller.name if seller else "",
        "phoneSaler": "",
        "address": inv.customer_address or "",
        "deliveryType": inv.delivery_type or "",
        "deliveryPrice": float(inv.delivery_price or 0),
        "discount": float(inv.discount or 0),
        "amount": float(inv.subtotal or 0),
    }


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

    q = build_report_invoices_query(
        search=search,
        products=products,
        provinces=provinces,
        date_from=date_from,
        date_to=date_to,
    )

    sort_map = {
        "id": Invoice.id,
        "invoiceNo": Invoice.invoice_no,
        "date": Invoice.created_at,
        "product": Invoice.product_name,
        "seller": User.name,
        "amount": Invoice.subtotal,
    }
    q = apply_sort(q, sort_by, sort_order, sort_map)
    if not sort_by:
        q = q.order_by(Invoice.created_at.desc(), Invoice.id.desc())

    rows, total = paginate_query(q, db, page, limit)
    result = [serialize_report_invoice(inv, seller) for inv, seller in rows]
    return result, total


EXPORT_MAX_ROWS = 10_000


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

    q = build_report_invoices_query(
        search=search,
        products=products,
        provinces=provinces,
        date_from=date_from,
        date_to=date_to,
    )
    q = q.order_by(Invoice.created_at.desc(), Invoice.id.desc()).limit(EXPORT_MAX_ROWS)
    rows = db.execute(q).all()
    return [serialize_report_invoice(inv, seller) for inv, seller in rows]


# Telegram / scheduled product reports (unchanged; uses report_repository).
from app.repositories.report_repository import report_repo  # noqa: E402


class ReportService:
    TELEGRAM_MAX_MESSAGE_LEN = 4096
    TELEGRAM_SAFE_MESSAGE_LEN = 3500

    @staticmethod
    def _normalize_period_bounds(start_date, end_date):
        def _to_start(value):
            if value is None:
                return None
            if isinstance(value, str):
                return parse_iso_date(value[:10], end_of_day=False)
            if isinstance(value, date) and not isinstance(value, datetime):
                return datetime.combine(value, time.min)
            return value

        def _to_end(value):
            if value is None:
                return None
            if isinstance(value, str):
                return parse_iso_date(value[:10], end_of_day=True)
            if isinstance(value, date) and not isinstance(value, datetime):
                return datetime.combine(value, time(23, 59, 59))
            return value

        return _to_start(start_date), _to_end(end_date)

    @staticmethod
    def _format_refund_label(refund_qty: int, refund_amount: float) -> str:
        if refund_qty > 0:
            return f"{refund_qty} (${refund_amount:.2f})"
        return "0"

    def _format_period_product_block(
        self,
        row: dict,
        *,
        escape,
        sold_qty_label: str = "total sale stock",
    ) -> str:
        name = escape((row.get("name") or "").strip() or "—")
        refund_label = self._format_refund_label(
            int(row.get("refund_qty") or 0),
            float(row.get("refund_amount") or 0),
        )
        return (
            f"+ Product Name : {name}\n"
            f"- total stock currently stock : {int(row.get('current_stock') or 0)}\n"
            f"- {sold_qty_label} : {int(row.get('sold_qty') or 0)}\n"
            f"- total product refund : {refund_label}\n"
            f"- Total add to stock : {int(row.get('added_qty') or 0)}\n"
            f"- total price sale today : ${float(row.get('sale_total') or 0):.2f}\n"
            f"- total add Stock : {int(row.get('added_qty') or 0)}\n"
            f"- Total price add stock : ${float(row.get('added_price') or 0):.2f}\n"
            f"- Total Damanaged Stock : {int(row.get('damaged_qty') or 0)}\n"
            f"- Total Price Damaged : ${float(row.get('damaged_price') or 0):.2f}\n"
        )

    def _format_period_product_footer(
        self,
        totals: dict,
        *,
        expense_total: float,
        add_price_total: float,
        damaged_price_total: float,
    ) -> str:
        return (
            "\n-------------------------------------------\n"
            f"Subtotal : ${float(totals.get('subtotal') or 0):.2f}\n"
            f"Delivery total : ${float(totals.get('delivery_total') or 0):.2f}\n"
            f"Discount Total : ${float(totals.get('discount_total') or 0):.2f}\n"
            f"Total Add price : ${add_price_total:.2f}\n"
            f"Total Damaged : ${damaged_price_total:.2f}\n"
            f"Total Income : ${float(totals.get('grand_total') or 0):.2f}\n"
            f"Total Expense : ${expense_total:.2f}\n"
        )

    def _period_report_header(self, title: str, start_date, end_date, escape) -> str:
        start_label = format_report_period_date_label(start_date)
        end_label = format_report_period_date_label(end_date)
        return (
            f"📊 <b>{escape(title)}</b>\n\n"
            f"Start Date : {escape(start_label)}\n"
            f"End Date : {escape(end_label)}\n\n"
        )

    def _format_category_block(self, row: dict, *, escape) -> str:
        name = escape((row.get("name") or "").strip() or "—")
        refund_label = self._format_refund_label(
            int(row.get("refund_qty") or 0),
            float(row.get("refund_amount") or 0),
        )
        return (
            f"+ Category Name : {name}\n"
            f"- total sale stock : {int(row.get('sold_qty') or 0)}\n"
            f"- total product refund : {refund_label}\n"
            f"- total price sale : ${float(row.get('sale_total') or 0):.2f}\n"
            f"- products sold : {int(row.get('products_sold') or 0)}\n"
        )

    def _format_commission_block(self, row: dict, *, escape) -> str:
        name = escape((row.get("seller_name") or "").strip() or "Unknown")
        return (
            f"+ Seller Name : {name}\n"
            f"- total sale stock : {int(row.get('sold_qty') or 0)}\n"
            f"- total price sale : ${float(row.get('total_sales') or 0):.2f}\n"
            f"- total commission : ${float(row.get('total_commission') or 0):.2f}\n"
        )

    def _format_payment_block(self, row: dict, *, escape) -> str:
        name = escape((row.get("payment_method") or "").strip() or "Unknown")
        return (
            f"+ Payment Method : {name}\n"
            f"- total invoices : {int(row.get('total_invoices') or 0)}\n"
            f"- subtotal : ${float(row.get('subtotal') or 0):.2f}\n"
            f"- delivery total : ${float(row.get('delivery_total') or 0):.2f}\n"
            f"- discount total : ${float(row.get('discount_total') or 0):.2f}\n"
            f"- total income : ${float(row.get('grand_total') or 0):.2f}\n"
        )

    def _scoped_category_footer(self, rows: list[dict], expense_total: float) -> str:
        sale_total = sum(float(row.get("sale_total") or 0) for row in rows)
        return (
            "\n-------------------------------------------\n"
            f"Total price sale : ${sale_total:.2f}\n"
            f"Total Expense : ${expense_total:.2f}\n"
        )

    def _scoped_commission_footer(self, rows: list[dict]) -> str:
        total_sales = sum(float(row.get("total_sales") or 0) for row in rows)
        total_commission = sum(float(row.get("total_commission") or 0) for row in rows)
        return (
            "\n-------------------------------------------\n"
            f"Total Sales : ${total_sales:.2f}\n"
            f"Total Commission : ${total_commission:.2f}\n"
        )

    def _scoped_payment_footer(self, rows: list[dict]) -> str:
        subtotal = sum(float(row.get("subtotal") or 0) for row in rows)
        delivery_total = sum(float(row.get("delivery_total") or 0) for row in rows)
        discount_total = sum(float(row.get("discount_total") or 0) for row in rows)
        grand_total = sum(float(row.get("grand_total") or 0) for row in rows)
        return (
            "\n-------------------------------------------\n"
            f"Subtotal : ${subtotal:.2f}\n"
            f"Delivery total : ${delivery_total:.2f}\n"
            f"Discount Total : ${discount_total:.2f}\n"
            f"Total Income : ${grand_total:.2f}\n"
        )

    def format_category_report_messages(
        self,
        db: Session,
        start_date=None,
        end_date=None,
        *,
        category_id: int | None = None,
    ) -> list[str]:
        from app.services.alert_service import _escape_telegram_html

        start, end = self._normalize_period_bounds(start_date, end_date)
        categories = report_repo.get_period_category_report_rows(
            db, start, end, category_id=category_id
        )
        scoped = category_id is not None
        totals = report_repo.get_daily_sales_totals(db, start, end)
        expense_total = report_repo.get_daily_expense_total(db, start, end)

        header = self._period_report_header("Category Report", start_date, end_date, _escape_telegram_html)
        blocks: list[str] = []
        if not categories:
            blocks.append("<i>No category activity in this period.</i>\n")
        else:
            for row in categories:
                blocks.append(self._format_category_block(row, escape=_escape_telegram_html))

        if scoped:
            footer = self._scoped_category_footer(categories, expense_total=0)
        else:
            footer = (
                "\n-------------------------------------------\n"
                f"Subtotal : ${float(totals.get('subtotal') or 0):.2f}\n"
                f"Delivery total : ${float(totals.get('delivery_total') or 0):.2f}\n"
                f"Discount Total : ${float(totals.get('discount_total') or 0):.2f}\n"
                f"Total Income : ${float(totals.get('grand_total') or 0):.2f}\n"
                f"Total Expense : ${expense_total:.2f}\n"
            )
        return self._chunk_report_lines(header, blocks, footer)

    def format_commission_report_messages(
        self,
        db: Session,
        start_date=None,
        end_date=None,
        *,
        user_id: int | None = None,
    ) -> list[str]:
        from app.services.alert_service import _escape_telegram_html

        start, end = self._normalize_period_bounds(start_date, end_date)
        sellers = report_repo.get_period_commission_report_rows(db, start, end, user_id=user_id)
        scoped = user_id is not None
        totals = report_repo.get_daily_sales_totals(db, start, end)
        total_commission = sum(float(row.get("total_commission") or 0) for row in sellers)
        total_sales = sum(float(row.get("total_sales") or 0) for row in sellers)

        header = self._period_report_header("Commission Report", start_date, end_date, _escape_telegram_html)
        blocks: list[str] = []
        if not sellers:
            blocks.append("<i>No commission activity in this period.</i>\n")
        else:
            for row in sellers:
                blocks.append(self._format_commission_block(row, escape=_escape_telegram_html))

        if scoped:
            footer = self._scoped_commission_footer(sellers)
        else:
            footer = (
                "\n-------------------------------------------\n"
                f"Subtotal : ${float(totals.get('subtotal') or 0):.2f}\n"
                f"Delivery total : ${float(totals.get('delivery_total') or 0):.2f}\n"
                f"Discount Total : ${float(totals.get('discount_total') or 0):.2f}\n"
                f"Total Sales : ${total_sales:.2f}\n"
                f"Total Commission : ${total_commission:.2f}\n"
                f"Total Income : ${float(totals.get('grand_total') or 0):.2f}\n"
            )
        return self._chunk_report_lines(header, blocks, footer)

    def format_payment_report_messages(
        self,
        db: Session,
        start_date=None,
        end_date=None,
        *,
        payment_method: str | None = None,
    ) -> list[str]:
        from app.services.alert_service import _escape_telegram_html

        start, end = self._normalize_period_bounds(start_date, end_date)
        payments = report_repo.get_period_payment_report_rows(
            db, start, end, payment_method=payment_method
        )

        header = self._period_report_header("Payment Report", start_date, end_date, _escape_telegram_html)
        blocks: list[str] = []
        if not payments:
            blocks.append("<i>No payment activity in this period.</i>\n")
        else:
            for row in payments:
                blocks.append(self._format_payment_block(row, escape=_escape_telegram_html))

        footer = self._scoped_payment_footer(payments)
        return self._chunk_report_lines(header, blocks, footer)

    def format_period_product_report_messages(
        self,
        db: Session,
        start_date=None,
        end_date=None,
        *,
        title: str = "Product Report",
        sold_qty_label: str = "total sale stock",
        product_id: int | None = None,
    ) -> list[str]:
        from app.services.alert_service import _escape_telegram_html

        start, end = self._normalize_period_bounds(start_date, end_date)
        products = report_repo.get_period_product_report_rows(
            db, start, end, product_id=product_id
        )
        scoped = product_id is not None
        totals = report_repo.get_daily_sales_totals(db, start, end)
        expense_total = report_repo.get_daily_expense_total(db, start, end)
        add_price_total = sum(float(row.get("added_price") or 0) for row in products)
        damaged_price_total = sum(float(row.get("damaged_price") or 0) for row in products)
        sale_total = sum(float(row.get("sale_total") or 0) for row in products)

        header = self._period_report_header(title, start_date, end_date, _escape_telegram_html)

        product_blocks: list[str] = []
        if not products:
            product_blocks.append("<i>No product activity in this period.</i>\n")
        else:
            for row in products:
                product_blocks.append(
                    self._format_period_product_block(
                        row,
                        escape=_escape_telegram_html,
                        sold_qty_label=sold_qty_label,
                    )
                )

        if scoped:
            footer = (
                "\n-------------------------------------------\n"
                f"total price sale : ${sale_total:.2f}\n"
                f"Total Add price : ${add_price_total:.2f}\n"
                f"Total Damaged : ${damaged_price_total:.2f}\n"
            )
        else:
            footer = self._format_period_product_footer(
                totals,
                expense_total=expense_total,
                add_price_total=add_price_total,
                damaged_price_total=damaged_price_total,
            )
        return self._chunk_report_lines(header, product_blocks, footer)

    def format_daily_sales_summary(
        self,
        db: Session,
        start_date=None,
        end_date=None,
        *,
        date_label: str,
        time_label: str | None = None,
    ) -> list[str]:
        from app.services.alert_service import _escape_telegram_html

        start, end = self._normalize_period_bounds(start_date, end_date)
        products = report_repo.get_period_product_report_rows(db, start, end)
        totals = report_repo.get_daily_sales_totals(db, start, end)
        expense_total = report_repo.get_daily_expense_total(db, start, end)
        add_price_total = sum(float(row.get("added_price") or 0) for row in products)
        damaged_price_total = sum(float(row.get("damaged_price") or 0) for row in products)

        header = f"📊 <b>Report Today</b> : ({_escape_telegram_html(date_label)})\n\n"
        if time_label:
            header += f"<i>{_escape_telegram_html(time_label)}</i>\n\n"

        product_blocks: list[str] = []
        if not products:
            product_blocks.append("<i>No product activity in this period.</i>\n")
        else:
            for row in products:
                product_blocks.append(
                    self._format_period_product_block(
                        row,
                        escape=_escape_telegram_html,
                        sold_qty_label="total sale stock today",
                    )
                )

        footer = self._format_period_product_footer(
            totals,
            expense_total=expense_total,
            add_price_total=add_price_total,
            damaged_price_total=damaged_price_total,
        )
        return self._chunk_report_lines(header, product_blocks, footer)

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

    def format_product_report_messages(
        self,
        db: Session,
        start_date=None,
        end_date=None,
        *,
        title: str = "Product Report",
        product_id: int | None = None,
    ) -> list[str]:
        return self.format_period_product_report_messages(
            db,
            start_date,
            end_date,
            title=title,
            sold_qty_label="total sale stock",
            product_id=product_id,
        )

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
