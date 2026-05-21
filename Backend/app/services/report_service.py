from sqlalchemy.orm import Session
from app.repositories.report_repository import report_repo

class ReportService:
    TELEGRAM_MAX_MESSAGE_LEN = 4096
    TELEGRAM_SAFE_MESSAGE_LEN = 3500

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
        if not data: return msg + "No data found."
        for i, row in enumerate(data, 1):
            msg += f"{i}. {row['category_name']}\n"
            msg += f"Sales: ${row['total_sales']:.2f}\n"
            msg += f"Qty: {row['total_qty']}\n\n"
        return msg

    def format_product_price(self, db: Session, start_date=None, end_date=None, label="Today") -> str:
        data = report_repo.get_price_by_product(db, start_date, end_date)
        msg = f"📦 <b>Summary Price by Product</b>\n"
        msg += f"Period: {label}\n\n"
        if not data: return msg + "No data found."
        for i, row in enumerate(data, 1):
            msg += f"{i}. {row['product_name']}\n"
            msg += f"Sales: ${row['total_sales']:.2f}\n"
            msg += f"Qty: {row['total_qty']}\n\n"
        return msg

    def format_source_price(self, db: Session, start_date=None, end_date=None, label="Today") -> str:
        data = report_repo.get_price_by_source(db, start_date, end_date)
        msg = f"📍 <b>Summary Price by Source</b>\n"
        msg += f"Period: {label}\n\n"
        if not data: return msg + "No data found."
        for i, row in enumerate(data, 1):
            msg += f"{i}. {row['source']}\n"
            msg += f"Sales: ${row['total_sales']:.2f}\n"
            msg += f"Invoices: {row['total_invoices']}\n\n"
        return msg

    def format_payment_price(self, db: Session, start_date=None, end_date=None, label="Today") -> str:
        data = report_repo.get_price_by_payment(db, start_date, end_date)
        msg = f"💳 <b>Summary Price by Payment Method</b>\n"
        msg += f"Period: {label}\n\n"
        if not data: return msg + "No data found."
        for i, row in enumerate(data, 1):
            msg += f"{i}. {row['payment_method']}\n"
            msg += f"Sales: ${row['total_sales']:.2f}\n"
            msg += f"Invoices: {row['total_invoices']}\n\n"
        return msg

    def format_commission_user(self, db: Session, start_date=None, end_date=None, label="Today") -> str:
        data = report_repo.get_commission_by_user(db, start_date, end_date)
        msg = f"👤 <b>Commission by User Sold Product</b>\n"
        msg += f"Period: {label}\n\n"
        if not data: return msg + "No data found."
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
        if not data: return msg + "No data found."
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
        grand_total_sold = 0.0
        grand_total_in_stock = 0.0

        for i, row in enumerate(rows, 1):
            grand_total_sold += row["total_price_sold"]
            grand_total_in_stock += row["total_price_in_stock"]
            lines.append(
                f"{i}. {row['name']}\n"
                f"Sold Qty: {row['sold_qty']}\n"
                f"Total Price Sold: ${row['total_price_sold']:.2f}\n"
                f"Stock Qty: {row['stock_qty']}\n"
                f"Total Price In Stock: ${row['total_price_in_stock']:.2f}\n"
            )

        footer = (
            "============================\n\n"
            f"Grand Total Sold: ${grand_total_sold:.2f}\n"
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

        # Ensure footer always exists in the last chunk.
        if len(current) + len(footer) + 2 > self.TELEGRAM_SAFE_MESSAGE_LEN:
            chunks.append(current.rstrip())
            current = header + footer
        else:
            current += footer
        chunks.append(current.rstrip())

        return chunks

report_service = ReportService()
