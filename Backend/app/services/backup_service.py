import logging
from datetime import datetime
from sqlalchemy import select, or_
from sqlalchemy.orm import Session, joinedload

from app.models import Product, Category, Invoice, CheckoutItem, User, Role
from app.repositories.backup_tracker_repository import backup_tracker_repo
from app.services.google_sheet_service import google_sheet_service

logger = logging.getLogger(__name__)

class BackupService:
    def backup_all(self, db: Session):
        results = []
        # List of backup tasks: (method, backup_name, sheet_name)
        tasks = [
            (self.backup_products, "products_google_sheet_backup", "Products Backup"),
            (self.backup_categories, "categories_google_sheet_backup", "Categories Backup"),
            (self.backup_invoices, "invoices_google_sheet_backup", "Invoices Backup"),
            (self.backup_invoice_details, "invoice_details_google_sheet_backup", "Invoice Details Backup"),
            (self.backup_deliveries, "deliveries_google_sheet_backup", "Deliveries Backup"),
            (self.backup_users, "users_google_sheet_backup", "Users Backup"),
            (self.backup_roles, "roles_google_sheet_backup", "Roles Backup"),
        ]
        
        for func, name, sheet in tasks:
            try:
                res = func(db)
                results.append({
                    "backup_name": name,
                    "sheet_name": sheet,
                    "new_rows": res.get("rows_added", 0),
                    "status": res.get("status", "success")
                })
            except Exception as e:
                logger.error(f"Backup failed for {name}: {e}")
                results.append({
                    "backup_name": name,
                    "sheet_name": sheet,
                    "new_rows": 0,
                    "status": "error",
                    "error": str(e)
                })
        
        return results

    def _generic_backup(self, db: Session, backup_name: str, sheet_name: str, headers: list[str], model, mapper_func, query_filter=None):
        tracker = backup_tracker_repo.get_by_name(db, backup_name)
        last_id = tracker.last_backup_id if tracker else 0
        
        query = select(model).where(model.id > last_id).order_by(model.id.asc())
        if query_filter is not None:
            query = query.where(query_filter)
            
        rows = db.scalars(query).all()
        
        if not rows:
            backup_tracker_repo.update_status(db, backup_name, last_id, "success")
            return {
                "message": "No new data to backup",
                "status": "success", 
                "backup_name": backup_name,
                "sheet_name": sheet_name,
                "rows_added": 0, 
                "last_backup_id": last_id
            }

        try:
            google_sheet_service.ensure_tab_and_headers(sheet_name, headers)
            
            values = []
            max_id = last_id
            for r in rows:
                values.append(mapper_func(r))
                max_id = max(max_id, r.id)
            
            google_sheet_service.append_rows(sheet_name, values)
            backup_tracker_repo.update_status(db, backup_name, max_id, "success")
            
            return {
                "message": f"{sheet_name.split(' ')[0]} backup completed",
                "status": "success",
                "backup_name": backup_name,
                "sheet_name": sheet_name,
                "rows_added": len(rows),
                "last_backup_id_before": last_id,
                "last_backup_id_after": max_id
            }
        except Exception as e:
            logger.error(f"Error during backup {backup_name}: {e}")
            backup_tracker_repo.update_status(db, backup_name, last_id, "error", str(e))
            raise

    # Mappers and individual backup methods
    def backup_products(self, db: Session):
        headers = ["ID", "Name", "Category ID", "In Price", "Out Price", "Commission", "Total Stock", "In Stock", "Sold", "Added", "Damaged", "Status", "Stock Note", "Created At", "Updated At"]
        def mapper(p: Product):
            return [
                p.id, p.name, p.category_id, p.in_price, p.out_price, p.commission, 
                p.total_stock, p.in_stock, p.sold, 0, 0, p.status, "", 
                p.created_at.isoformat() if p.created_at else "", ""
            ]
        return self._generic_backup(db, "products_google_sheet_backup", "Products Backup", headers, Product, mapper)

    def backup_categories(self, db: Session):
        headers = ["ID", "Name", "Description", "Created At", "Updated At"]
        def mapper(c: Category):
            return [c.id, c.name, c.description, c.created_at.isoformat() if c.created_at else "", ""]
        return self._generic_backup(db, "categories_google_sheet_backup", "Categories Backup", headers, Category, mapper)

    def backup_invoices(self, db: Session):
        headers = ["ID", "Customer Name", "Customer Phone", "Customer Address", "Source", "Delivery Type", "Delivery Price", "Delivery Date", "Discount Percent", "Payment Method", "Delivery Status", "Seller ID", "Total Amount", "Created At", "Updated At"]
        def mapper(i: Invoice):
            return [
                i.id, i.customer_name, i.customer_phone, i.customer_address, i.source, 
                i.delivery_type, i.delivery_price, i.delivery_date, i.discount, 
                i.payment_method, i.delivery_status, i.user_id, i.total, 
                i.created_at.isoformat() if i.created_at else "", ""
            ]
        return self._generic_backup(db, "invoices_google_sheet_backup", "Invoices Backup", headers, Invoice, mapper)

    def backup_invoice_details(self, db: Session):
        headers = ["ID", "Invoice ID", "Product ID", "Quantity", "Unit Price", "Subtotal", "Created At"]
        def mapper(it: CheckoutItem):
            return [it.id, it.invoice_id, it.product_id, it.quantity, it.price, it.total, ""]
        return self._generic_backup(db, "invoice_details_google_sheet_backup", "Invoice Details Backup", headers, CheckoutItem, mapper)

    def backup_deliveries(self, db: Session):
        headers = ["ID", "Invoice ID", "Customer Name", "Customer Phone", "Customer Address", "Delivery Status", "Delivery Type", "Delivery Price", "Delivery Date", "Created At", "Updated At"]
        def mapper(i: Invoice):
            return [
                i.id, i.id, i.customer_name, i.customer_phone, i.customer_address, 
                i.delivery_status, i.delivery_type, i.delivery_price, i.delivery_date, 
                i.created_at.isoformat() if i.created_at else "", ""
            ]
        return self._generic_backup(db, "deliveries_google_sheet_backup", "Deliveries Backup", headers, Invoice, mapper, or_(Invoice.delivery_type != "", Invoice.delivery_type != None))

    def backup_users(self, db: Session):
        headers = ["ID", "Name", "Email", "Role", "Permissions", "Created At", "Updated At"]
        def mapper(u: User):
            role_name = u.role_rel.name if u.role_rel else ""
            perms = u.role_rel.page_access if u.role_rel else ""
            return [u.id, u.name, u.email, role_name, perms, u.created_at.isoformat() if u.created_at else "", ""]
        
        backup_name = "users_google_sheet_backup"
        sheet_name = "Users Backup"
        tracker = backup_tracker_repo.get_by_name(db, backup_name)
        last_id = tracker.last_backup_id if tracker else 0
        rows = db.scalars(select(User).where(User.id > last_id).options(joinedload(User.role_rel)).order_by(User.id.asc())).all()
        
        if not rows:
            return {"status": "success", "message": "No new data to backup", "rows_added": 0, "last_id": last_id, "backup_name": backup_name, "sheet_name": sheet_name}
        
        google_sheet_service.ensure_tab_and_headers(sheet_name, headers)
        values = [mapper(r) for r in rows]
        google_sheet_service.append_rows(sheet_name, values)
        max_id = max(r.id for r in rows)
        backup_tracker_repo.update_status(db, backup_name, max_id, "success")
        return {
            "status": "success", "message": "Users backup completed", "rows_added": len(rows), 
            "last_backup_id_before": last_id, "last_backup_id_after": max_id,
            "backup_name": backup_name, "sheet_name": sheet_name
        }

    def backup_roles(self, db: Session):
        headers = ["ID", "Name", "Page Access", "Created At", "Updated At"]
        def mapper(r: Role):
            return [r.id, r.name, r.page_access, r.created_at.isoformat() if r.created_at else "", ""]
        return self._generic_backup(db, "roles_google_sheet_backup", "Roles Backup", headers, Role, mapper)

backup_service = BackupService()
