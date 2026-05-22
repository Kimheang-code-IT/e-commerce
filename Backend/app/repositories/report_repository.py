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
