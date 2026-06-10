from sqlalchemy.orm import Session
from sqlalchemy import text
import logging

logger = logging.getLogger(__name__)

class ReportRepository:
    def get_summary_price(self, db: Session, start_date=None, end_date=None):
        query = text("""
            SELECT 
                COALESCE(SUM(i.total), 0) as total_sales,
                COUNT(i.id) as total_invoices,
                COALESCE(SUM(ci.quantity), 0) as total_products_sold
            FROM invoices i
            LEFT JOIN checkout_items ci ON ci.invoice_id = i.id
            WHERE (:start_date IS NULL OR i.created_at >= :start_date)
              AND (:end_date IS NULL OR i.created_at <= :end_date)
              AND i.status = 'paid'
        """)
        result = db.execute(query, {"start_date": start_date, "end_date": end_date}).fetchone()
        return {
            "total_sales": float(result[0]),
            "total_invoices": int(result[1]),
            "total_products_sold": int(result[2])
        }

    def get_price_by_category(self, db: Session, start_date=None, end_date=None):
        query = text("""
            SELECT 
                c.name as category_name,
                COALESCE(SUM(ci.quantity * ci.price), 0) as total_sales,
                COALESCE(SUM(ci.quantity), 0) as total_qty
            FROM checkout_items ci
            JOIN invoices i ON i.id = ci.invoice_id
            JOIN products p ON p.id = ci.product_id
            JOIN categories c ON c.id = p.category_id
            WHERE (:start_date IS NULL OR i.created_at >= :start_date)
              AND (:end_date IS NULL OR i.created_at <= :end_date)
              AND i.status = 'paid'
            GROUP BY c.name
            ORDER BY total_sales DESC
        """)
        results = db.execute(query, {"start_date": start_date, "end_date": end_date}).fetchall()
        return [{"category_name": r[0], "total_sales": float(r[1]), "total_qty": int(r[2])} for r in results]

    def get_price_by_product(self, db: Session, start_date=None, end_date=None):
        query = text("""
            SELECT 
                p.name as product_name,
                COALESCE(SUM(ci.quantity * ci.price), 0) as total_sales,
                COALESCE(SUM(ci.quantity), 0) as total_qty
            FROM products p
            LEFT JOIN checkout_items ci ON ci.product_id = p.id
            LEFT JOIN invoices i ON i.id = ci.invoice_id 
                AND (:start_date IS NULL OR i.created_at >= :start_date)
                AND (:end_date IS NULL OR i.created_at <= :end_date)
                AND i.status = 'paid'
            GROUP BY p.id, p.name
            ORDER BY total_sales DESC, p.name ASC
        """)
        results = db.execute(query, {"start_date": start_date, "end_date": end_date}).fetchall()
        return [{"product_name": r[0], "total_sales": float(r[1]), "total_qty": int(r[2])} for r in results]

    def get_price_by_source(self, db: Session, start_date=None, end_date=None):
        query = text("""
            SELECT 
                COALESCE(i.source, 'Unknown') as source,
                COALESCE(SUM(i.total), 0) as total_sales,
                COUNT(i.id) as total_invoices
            FROM invoices i
            WHERE (:start_date IS NULL OR i.created_at >= :start_date)
              AND (:end_date IS NULL OR i.created_at <= :end_date)
              AND i.status = 'paid'
            GROUP BY i.source
            ORDER BY total_sales DESC
        """)
        results = db.execute(query, {"start_date": start_date, "end_date": end_date}).fetchall()
        return [{"source": r[0], "total_sales": float(r[1]), "total_invoices": int(r[2])} for r in results]

    def get_price_by_payment(self, db: Session, start_date=None, end_date=None):
        query = text("""
            SELECT 
                COALESCE(i.payment_method, 'Unknown') as payment_method,
                COALESCE(SUM(i.total), 0) as total_sales,
                COUNT(i.id) as total_invoices
            FROM invoices i
            WHERE (:start_date IS NULL OR i.created_at >= :start_date)
              AND (:end_date IS NULL OR i.created_at <= :end_date)
              AND i.status = 'paid'
            GROUP BY i.payment_method
            ORDER BY total_sales DESC
        """)
        results = db.execute(query, {"start_date": start_date, "end_date": end_date}).fetchall()
        return [{"payment_method": r[0], "total_sales": float(r[1]), "total_invoices": int(r[2])} for r in results]

    def get_commission_by_user(self, db: Session, start_date=None, end_date=None):
        query = text("""
            SELECT 
                u.name as seller_name,
                COALESCE(SUM(ci.quantity * p.commission), 0) as total_commission,
                COALESCE(SUM(ci.quantity * ci.price), 0) as total_sales,
                COALESCE(SUM(ci.quantity), 0) as total_products_sold
            FROM checkout_items ci
            JOIN invoices i ON i.id = ci.invoice_id
            JOIN products p ON p.id = ci.product_id
            LEFT JOIN users u ON u.id = i.user_id
            WHERE (:start_date IS NULL OR i.created_at >= :start_date)
              AND (:end_date IS NULL OR i.created_at <= :end_date)
              AND i.status = 'paid'
            GROUP BY u.name
            ORDER BY total_commission DESC
        """)
        results = db.execute(query, {"start_date": start_date, "end_date": end_date}).fetchall()
        return [{
            "seller_name": r[0],
            "total_commission": float(r[1]),
            "total_sales": float(r[2]),
            "total_products_sold": int(r[3])
        } for r in results]

    def get_price_by_delivery(self, db: Session, start_date=None, end_date=None):
        query = text("""
            SELECT 
                COALESCE(i.delivery_type, 'Unknown') as delivery_type,
                COALESCE(SUM(i.total), 0) as total_sales,
                COALESCE(SUM(i.delivery_price), 0) as total_delivery_fee,
                COUNT(i.id) as total_invoices
            FROM invoices i
            WHERE (:start_date IS NULL OR i.created_at >= :start_date)
              AND (:end_date IS NULL OR i.created_at <= :end_date)
              AND i.status = 'paid'
            GROUP BY i.delivery_type
            ORDER BY total_sales DESC
        """)
        results = db.execute(query, {"start_date": start_date, "end_date": end_date}).fetchall()
        return [{
            "delivery_type": r[0],
            "total_sales": float(r[1]),
            "total_delivery_fee": float(r[2]),
            "total_invoices": int(r[3])
        } for r in results]

    def get_all_products(self, db: Session):
        query = text("SELECT id, name FROM products WHERE status = 'active' ORDER BY name ASC")
        results = db.execute(query).fetchall()
        return [{"id": r[0], "name": r[1]} for r in results]

    def get_single_product_summary(self, db: Session, product_id: int, start_date=None, end_date=None):
        query = text("""
            SELECT 
                p.name,
                COALESCE(SUM(ci.quantity * ci.price), 0) as total_sales,
                COALESCE(SUM(ci.quantity), 0) as total_qty,
                COUNT(DISTINCT i.id) as total_invoices
            FROM products p
            LEFT JOIN checkout_items ci ON ci.product_id = p.id
            LEFT JOIN invoices i ON i.id = ci.invoice_id 
                AND (:start_date IS NULL OR i.created_at >= :start_date)
                AND (:end_date IS NULL OR i.created_at <= :end_date)
                AND i.status = 'paid'
            WHERE p.id = :product_id
            GROUP BY p.id, p.name
        """)
        result = db.execute(query, {"product_id": product_id, "start_date": start_date, "end_date": end_date}).fetchone()
        if not result: return None
        return {
            "name": result[0],
            "total_sales": float(result[1]),
            "total_qty": int(result[2]),
            "total_invoices": int(result[3])
        }

    def get_all_categories(self, db: Session):
        query = text("SELECT id, name FROM categories ORDER BY name ASC")
        results = db.execute(query).fetchall()
        return [{"id": r[0], "name": r[1]} for r in results]

    def get_single_category_summary(self, db: Session, category_id: int, start_date=None, end_date=None):
        query = text("""
            SELECT 
                c.name,
                COALESCE(SUM(ci.quantity * ci.price), 0) as total_sales,
                COALESCE(SUM(ci.quantity), 0) as total_qty
            FROM categories c
            LEFT JOIN products p ON p.category_id = c.id
            LEFT JOIN checkout_items ci ON ci.product_id = p.id
            LEFT JOIN invoices i ON i.id = ci.invoice_id
                AND (:start_date IS NULL OR i.created_at >= :start_date)
                AND (:end_date IS NULL OR i.created_at <= :end_date)
                AND i.status = 'paid'
            WHERE c.id = :category_id
            GROUP BY c.id, c.name
        """)
        result = db.execute(query, {"category_id": category_id, "start_date": start_date, "end_date": end_date}).fetchone()
        if not result: return None
        return {
            "name": result[0],
            "total_sales": float(result[1]),
            "total_qty": int(result[2])
        }

    def get_all_payment_methods(self, db: Session):
        query = text("""
            SELECT DISTINCT COALESCE(payment_method, 'Unknown') as payment_method
            FROM invoices
            WHERE status = 'paid'
            ORDER BY payment_method ASC
        """)
        results = db.execute(query).fetchall()
        return [{"payment_method": r[0]} for r in results]

    def get_single_payment_summary(self, db: Session, payment_method: str, start_date=None, end_date=None):
        query = text("""
            SELECT 
                COALESCE(SUM(i.total), 0) as total_sales,
                COUNT(i.id) as total_invoices
            FROM invoices i
            WHERE COALESCE(i.payment_method, 'Unknown') = :payment_method
              AND (:start_date IS NULL OR i.created_at >= :start_date)
              AND (:end_date IS NULL OR i.created_at <= :end_date)
              AND i.status = 'paid'
        """)
        result = db.execute(query, {"payment_method": payment_method, "start_date": start_date, "end_date": end_date}).fetchone()
        if not result: return None
        return {
            "payment_method": payment_method,
            "total_sales": float(result[0]),
            "total_invoices": int(result[1])
        }

    def get_all_sources(self, db: Session):
        query = text("""
            SELECT DISTINCT COALESCE(source, 'Unknown') as source
            FROM invoices
            WHERE status = 'paid'
            ORDER BY source ASC
        """)
        results = db.execute(query).fetchall()
        return [{"source": r[0]} for r in results]

    def get_single_source_summary(self, db: Session, source: str, start_date=None, end_date=None):
        query = text("""
            SELECT 
                COALESCE(SUM(i.total), 0) as total_sales,
                COUNT(i.id) as total_invoices
            FROM invoices i
            WHERE COALESCE(i.source, 'Unknown') = :source
              AND (:start_date IS NULL OR i.created_at >= :start_date)
              AND (:end_date IS NULL OR i.created_at <= :end_date)
              AND i.status = 'paid'
        """)
        result = db.execute(query, {"source": source, "start_date": start_date, "end_date": end_date}).fetchone()
        if not result: return None
        return {
            "source": source,
            "total_sales": float(result[0]),
            "total_invoices": int(result[1])
        }

    def get_all_users(self, db: Session):
        query = text("""
            SELECT id, name FROM users
            ORDER BY name ASC
        """)
        results = db.execute(query).fetchall()
        return [{"id": r[0], "name": r[1]} for r in results]

    def get_single_user_commission(self, db: Session, user_id: int, start_date=None, end_date=None):
        query = text("""
            SELECT 
                u.name,
                COALESCE(SUM(ci.quantity * ci.price * p.commission / 100), 0) as total_commission,
                COALESCE(SUM(ci.quantity * ci.price), 0) as total_sales,
                COALESCE(SUM(ci.quantity), 0) as total_qty
            FROM users u
            LEFT JOIN invoices i ON i.user_id = u.id
                AND (:start_date IS NULL OR i.created_at >= :start_date)
                AND (:end_date IS NULL OR i.created_at <= :end_date)
                AND i.status = 'paid'
            LEFT JOIN checkout_items ci ON ci.invoice_id = i.id
            LEFT JOIN products p ON p.id = ci.product_id
            WHERE u.id = :user_id
            GROUP BY u.id, u.name
        """)
        result = db.execute(query, {"user_id": user_id, "start_date": start_date, "end_date": end_date}).fetchone()
        if not result: return None
        return {
            "name": result[0],
            "total_commission": float(result[1]),
            "total_sales": float(result[2]),
            "total_qty": int(result[3])
        }

    def get_all_delivery_types(self, db: Session):
        query = text("""
            SELECT DISTINCT COALESCE(delivery_type, 'Unknown') as delivery_type
            FROM invoices
            WHERE status = 'paid'
            ORDER BY delivery_type ASC
        """)
        results = db.execute(query).fetchall()
        return [{"delivery_type": r[0]} for r in results]

    def get_single_delivery_summary(self, db: Session, delivery_type: str, start_date=None, end_date=None):
        query = text("""
            SELECT 
                COALESCE(SUM(i.total), 0) as total_sales,
                COALESCE(SUM(i.delivery_price), 0) as total_delivery_fee,
                COUNT(i.id) as total_invoices
            FROM invoices i
            WHERE COALESCE(i.delivery_type, 'Unknown') = :delivery_type
              AND (:start_date IS NULL OR i.created_at >= :start_date)
              AND (:end_date IS NULL OR i.created_at <= :end_date)
              AND i.status = 'paid'
        """)
        result = db.execute(query, {"delivery_type": delivery_type, "start_date": start_date, "end_date": end_date}).fetchone()
        if not result: return None
        return {
            "delivery_type": delivery_type,
            "total_sales": float(result[0]),
            "total_delivery_fee": float(result[1]),
            "total_invoices": int(result[2])
        }

    def get_daily_sales_lines(self, db: Session, start_date=None, end_date=None):
        """Paid checkout lines in range (excludes refunded lines), grouped by product + unit price."""
        query = text("""
            SELECT
                ci.product_name,
                COALESCE(ci.price, 0) AS unit_price,
                COALESCE(SUM(ci.quantity), 0) AS qty,
                COALESCE(SUM(ci.total), 0) AS line_total
            FROM checkout_items ci
            INNER JOIN invoices i ON i.id = ci.invoice_id
            WHERE i.status = 'paid'
              AND (:start_date IS NULL OR i.created_at >= :start_date)
              AND (:end_date IS NULL OR i.created_at <= :end_date)
              AND ci.id NOT IN (
                  SELECT checkout_item_id FROM refund_records
                  WHERE checkout_item_id IS NOT NULL
              )
            GROUP BY ci.product_name, ci.price
            HAVING COALESCE(SUM(ci.quantity), 0) > 0
            ORDER BY line_total DESC, ci.product_name ASC, unit_price ASC
        """)
        rows = db.execute(query, {"start_date": start_date, "end_date": end_date}).fetchall()
        return [
            {
                "product_name": r[0] or "",
                "unit_price": float(r[1] or 0),
                "qty": int(r[2] or 0),
                "line_total": float(r[3] or 0),
            }
            for r in rows
        ]

    def get_period_product_report_rows(self, db: Session, start_date=None, end_date=None):
        """Per-product stats for Telegram period reports (sales, refunds, stock, damage)."""
        query = text("""
            WITH sold AS (
                SELECT
                    ci.product_id,
                    MAX(ci.product_name) AS product_name,
                    COALESCE(SUM(ci.quantity), 0) AS sold_qty,
                    COALESCE(SUM(ci.total), 0) AS sale_total
                FROM checkout_items ci
                INNER JOIN invoices i ON i.id = ci.invoice_id
                WHERE i.status = 'paid'
                  AND (:start_date IS NULL OR i.created_at >= :start_date)
                  AND (:end_date IS NULL OR i.created_at <= :end_date)
                  AND ci.id NOT IN (
                      SELECT checkout_item_id FROM refund_records
                      WHERE checkout_item_id IS NOT NULL
                  )
                GROUP BY ci.product_id
            ),
            refunds AS (
                SELECT
                    product_id,
                    COALESCE(SUM(qty), 0) AS refund_qty,
                    COALESCE(SUM(amount), 0) AS refund_amount
                FROM refund_records
                WHERE product_id IS NOT NULL
                  AND (:start_date IS NULL OR refunded_at >= :start_date)
                  AND (:end_date IS NULL OR refunded_at <= :end_date)
                GROUP BY product_id
            ),
            additions AS (
                SELECT
                    product_id,
                    COALESCE(SUM(qty), 0) AS added_qty,
                    COALESCE(SUM(qty * in_price), 0) AS added_price
                FROM product_stock_additions
                WHERE (:start_date IS NULL OR created_at >= :start_date)
                  AND (:end_date IS NULL OR created_at <= :end_date)
                GROUP BY product_id
            ),
            damages AS (
                SELECT
                    pd.product_id,
                    COALESCE(SUM(pd.qty), 0) AS damaged_qty,
                    COALESCE(SUM(pd.qty * COALESCE(p.in_price, 0)), 0) AS damaged_price
                FROM product_damages pd
                LEFT JOIN products p ON p.id = pd.product_id
                WHERE (:start_date IS NULL OR pd.created_at >= :start_date)
                  AND (:end_date IS NULL OR pd.created_at <= :end_date)
                GROUP BY pd.product_id
            )
            SELECT
                p.id,
                COALESCE(NULLIF(TRIM(p.name), ''), sold.product_name, '—') AS name,
                COALESCE(p.in_stock, 0) AS current_stock,
                COALESCE(sold.sold_qty, 0) AS sold_qty,
                COALESCE(sold.sale_total, 0) AS sale_total,
                COALESCE(refunds.refund_qty, 0) AS refund_qty,
                COALESCE(refunds.refund_amount, 0) AS refund_amount,
                COALESCE(additions.added_qty, 0) AS added_qty,
                COALESCE(additions.added_price, 0) AS added_price,
                COALESCE(damages.damaged_qty, 0) AS damaged_qty,
                COALESCE(damages.damaged_price, 0) AS damaged_price
            FROM products p
            LEFT JOIN sold ON sold.product_id = p.id
            LEFT JOIN refunds ON refunds.product_id = p.id
            LEFT JOIN additions ON additions.product_id = p.id
            LEFT JOIN damages ON damages.product_id = p.id
            WHERE COALESCE(sold.sold_qty, 0) > 0
               OR COALESCE(refunds.refund_qty, 0) > 0
               OR COALESCE(additions.added_qty, 0) > 0
               OR COALESCE(damages.damaged_qty, 0) > 0
            ORDER BY sale_total DESC, name ASC
        """)
        rows = db.execute(query, {"start_date": start_date, "end_date": end_date}).fetchall()
        return [
            {
                "product_id": int(r[0]),
                "name": r[1] or "—",
                "current_stock": int(r[2] or 0),
                "sold_qty": int(r[3] or 0),
                "sale_total": float(r[4] or 0),
                "refund_qty": int(r[5] or 0),
                "refund_amount": float(r[6] or 0),
                "added_qty": int(r[7] or 0),
                "added_price": float(r[8] or 0),
                "damaged_qty": int(r[9] or 0),
                "damaged_price": float(r[10] or 0),
            }
            for r in rows
        ]

    def get_daily_product_report_rows(self, db: Session, start_date=None, end_date=None):
        return self.get_period_product_report_rows(db, start_date, end_date)

    def get_period_category_report_rows(self, db: Session, start_date=None, end_date=None):
        query = text("""
            WITH sold AS (
                SELECT
                    p.category_id,
                    COALESCE(SUM(ci.quantity), 0) AS sold_qty,
                    COALESCE(SUM(ci.total), 0) AS sale_total,
                    COUNT(DISTINCT p.id) AS products_sold
                FROM checkout_items ci
                INNER JOIN invoices i ON i.id = ci.invoice_id
                INNER JOIN products p ON p.id = ci.product_id
                WHERE i.status = 'paid'
                  AND (:start_date IS NULL OR i.created_at >= :start_date)
                  AND (:end_date IS NULL OR i.created_at <= :end_date)
                  AND ci.id NOT IN (
                      SELECT checkout_item_id FROM refund_records
                      WHERE checkout_item_id IS NOT NULL
                  )
                GROUP BY p.category_id
            ),
            refunds AS (
                SELECT
                    p.category_id,
                    COALESCE(SUM(rr.qty), 0) AS refund_qty,
                    COALESCE(SUM(rr.amount), 0) AS refund_amount
                FROM refund_records rr
                INNER JOIN products p ON p.id = rr.product_id
                WHERE rr.product_id IS NOT NULL
                  AND (:start_date IS NULL OR rr.refunded_at >= :start_date)
                  AND (:end_date IS NULL OR rr.refunded_at <= :end_date)
                GROUP BY p.category_id
            )
            SELECT
                COALESCE(c.name, 'Uncategorized') AS name,
                COALESCE(sold.sold_qty, 0) AS sold_qty,
                COALESCE(sold.sale_total, 0) AS sale_total,
                COALESCE(sold.products_sold, 0) AS products_sold,
                COALESCE(refunds.refund_qty, 0) AS refund_qty,
                COALESCE(refunds.refund_amount, 0) AS refund_amount
            FROM sold
            LEFT JOIN categories c ON c.id = sold.category_id
            LEFT JOIN refunds ON refunds.category_id = sold.category_id
            WHERE COALESCE(sold.sold_qty, 0) > 0
               OR COALESCE(refunds.refund_qty, 0) > 0
            ORDER BY sale_total DESC, name ASC
        """)
        rows = db.execute(query, {"start_date": start_date, "end_date": end_date}).fetchall()
        return [
            {
                "name": r[0] or "Uncategorized",
                "sold_qty": int(r[1] or 0),
                "sale_total": float(r[2] or 0),
                "products_sold": int(r[3] or 0),
                "refund_qty": int(r[4] or 0),
                "refund_amount": float(r[5] or 0),
            }
            for r in rows
        ]

    def get_period_commission_report_rows(self, db: Session, start_date=None, end_date=None):
        query = text("""
            SELECT
                COALESCE(NULLIF(TRIM(u.name), ''), 'Unknown') AS seller_name,
                COALESCE(SUM(ci.quantity * p.commission), 0) AS total_commission,
                COALESCE(SUM(ci.total), 0) AS total_sales,
                COALESCE(SUM(ci.quantity), 0) AS sold_qty
            FROM checkout_items ci
            INNER JOIN invoices i ON i.id = ci.invoice_id
            INNER JOIN products p ON p.id = ci.product_id
            LEFT JOIN users u ON u.id = i.user_id
            WHERE i.status = 'paid'
              AND (:start_date IS NULL OR i.created_at >= :start_date)
              AND (:end_date IS NULL OR i.created_at <= :end_date)
              AND ci.id NOT IN (
                  SELECT checkout_item_id FROM refund_records
                  WHERE checkout_item_id IS NOT NULL
              )
            GROUP BY u.name
            HAVING COALESCE(SUM(ci.quantity), 0) > 0
            ORDER BY total_commission DESC, total_sales DESC, seller_name ASC
        """)
        rows = db.execute(query, {"start_date": start_date, "end_date": end_date}).fetchall()
        return [
            {
                "seller_name": r[0] or "Unknown",
                "total_commission": float(r[1] or 0),
                "total_sales": float(r[2] or 0),
                "sold_qty": int(r[3] or 0),
            }
            for r in rows
        ]

    def get_daily_expense_total(self, db: Session, start_date=None, end_date=None) -> float:
        """Cost of goods sold + commission for non-refunded sales in range."""
        query = text("""
            SELECT
                COALESCE(SUM(ci.quantity * COALESCE(p.in_price, 0)), 0) AS cogs,
                COALESCE(SUM(ci.quantity * COALESCE(p.commission, 0)), 0) AS commission
            FROM checkout_items ci
            INNER JOIN invoices i ON i.id = ci.invoice_id
            LEFT JOIN products p ON p.id = ci.product_id
            WHERE i.status = 'paid'
              AND (:start_date IS NULL OR i.created_at >= :start_date)
              AND (:end_date IS NULL OR i.created_at <= :end_date)
              AND ci.id NOT IN (
                  SELECT checkout_item_id FROM refund_records
                  WHERE checkout_item_id IS NOT NULL
              )
        """)
        row = db.execute(query, {"start_date": start_date, "end_date": end_date}).fetchone()
        if not row:
            return 0.0
        return float(row[0] or 0) + float(row[1] or 0)

    def get_daily_sales_totals(self, db: Session, start_date=None, end_date=None):
        """Invoice totals for paid invoices with at least one non-refunded line in range."""
        query = text("""
            SELECT
                COALESCE(SUM(inv.subtotal), 0) AS subtotal,
                COALESCE(SUM(inv.delivery_price), 0) AS delivery_total,
                COALESCE(SUM(inv.discount), 0) AS discount_total,
                COALESCE(SUM(inv.total), 0) AS grand_total
            FROM (
                SELECT DISTINCT
                    i.id,
                    i.subtotal,
                    i.delivery_price,
                    i.discount,
                    i.total
                FROM invoices i
                INNER JOIN checkout_items ci ON ci.invoice_id = i.id
                WHERE i.status = 'paid'
                  AND (:start_date IS NULL OR i.created_at >= :start_date)
                  AND (:end_date IS NULL OR i.created_at <= :end_date)
                  AND ci.id NOT IN (
                      SELECT checkout_item_id FROM refund_records
                      WHERE checkout_item_id IS NOT NULL
                  )
            ) inv
        """)
        row = db.execute(query, {"start_date": start_date, "end_date": end_date}).fetchone()
        if not row:
            return {
                "subtotal": 0.0,
                "delivery_total": 0.0,
                "discount_total": 0.0,
                "grand_total": 0.0,
            }
        return {
            "subtotal": float(row[0] or 0),
            "delivery_total": float(row[1] or 0),
            "discount_total": float(row[2] or 0),
            "grand_total": float(row[3] or 0),
        }

    def get_product_report_rows(self, db: Session):
        # Sold $ = sold_qty × unit price × invoice discount share (proportional to line subtotal).
        # Excludes delivery; uses (subtotal - discount) / subtotal per paid invoice.
        query = text("""
            SELECT
                p.id,
                p.name,
                COALESCE(sold.sold_qty, 0) AS sold_qty,
                COALESCE(sold.total_price_sold, 0) AS total_price_sold,
                COALESCE(sold.total_price_sold_gross, 0) AS total_price_sold_gross,
                COALESCE(p.in_stock, 0) AS stock_qty,
                COALESCE(p.in_stock, 0) * COALESCE(p.out_price, 0) AS total_price_in_stock
            FROM products p
            LEFT JOIN (
                SELECT
                    ci.product_id,
                    SUM(ci.quantity) AS sold_qty,
                    SUM(
                        ci.quantity * COALESCE(ci.price, 0)
                        * CASE
                            WHEN COALESCE(i.subtotal, 0) > 0
                            THEN (COALESCE(i.subtotal, 0) - COALESCE(i.discount, 0))
                                 / COALESCE(i.subtotal, 0)
                            ELSE 1
                          END
                    ) AS total_price_sold,
                    SUM(ci.quantity * COALESCE(ci.price, 0)) AS total_price_sold_gross
                FROM checkout_items ci
                INNER JOIN invoices i ON i.id = ci.invoice_id
                    AND i.status = 'paid'
                GROUP BY ci.product_id
            ) sold ON sold.product_id = p.id
            WHERE COALESCE(sold.sold_qty, 0) > 0 OR COALESCE(p.in_stock, 0) > 0
            ORDER BY total_price_sold DESC, p.name ASC
        """)
        results = db.execute(query).fetchall()
        return [
            {
                "id": int(r[0]),
                "name": r[1],
                "sold_qty": int(r[2]),
                "total_price_sold": float(r[3]),
                "total_price_sold_gross": float(r[4]),
                "stock_qty": int(r[5]),
                "total_price_in_stock": float(r[6]),
            }
            for r in results
        ]

report_repo = ReportRepository()
