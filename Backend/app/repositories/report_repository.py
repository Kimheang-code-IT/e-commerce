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

report_repo = ReportRepository()
