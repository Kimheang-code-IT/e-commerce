import logging
import time
from sqlalchemy import select, and_
from sqlalchemy.orm import Session, joinedload

from app.models import (
    Product,
    Category,
    Invoice,
    CheckoutItem,
    User,
    Role,
    Supplier,
    SupplierProduct,
    RefundRecord,
)
from app.repositories.backup_tracker_repository import backup_tracker_repo
from app.services.google_sheet_service import google_sheet_service
from app.utils.backup_errors import shorten_backup_error

logger = logging.getLogger(__name__)


class BackupService:
    def backup_all(self, db: Session, *, full_refresh: bool = True):
        """Backup every module to its Google Sheet tab."""
        tasks = [
            (self.backup_products, "products_google_sheet_backup", "Products"),
            (self.backup_categories, "categories_google_sheet_backup", "Categories"),
            (self.backup_invoices, "invoices_google_sheet_backup", "Invoices"),
            (self.backup_invoice_details, "invoice_details_google_sheet_backup", "Invoice Details"),
            (self.backup_deliveries, "deliveries_google_sheet_backup", "Deliveries"),
            (self.backup_users, "users_google_sheet_backup", "Users"),
            (self.backup_roles, "roles_google_sheet_backup", "Roles"),
            (self.backup_suppliers, "suppliers_google_sheet_backup", "Suppliers"),
            (self.backup_supplier_products, "supplier_products_google_sheet_backup", "Supplier Products"),
            (self.backup_refunds, "refunds_google_sheet_backup", "Refunds"),
        ]
        results = []
        for i, (func, name, sheet) in enumerate(tasks):
            if i > 0:
                time.sleep(3)
            try:
                res = func(db, full_refresh=full_refresh)
                results.append(
                    {
                        "backup_name": name,
                        "sheet_name": sheet,
                        "new_rows": res.get("rows_synced", res.get("rows_added", 0)),
                        "total_rows": res.get("total_rows", 0),
                        "status": res.get("status", "success"),
                    }
                )
            except Exception as e:
                logger.error("Backup failed for %s: %s", name, e)
                results.append(
                    {
                        "backup_name": name,
                        "sheet_name": sheet,
                        "new_rows": 0,
                        "total_rows": 0,
                        "status": "error",
                        "error": shorten_backup_error(e),
                    }
                )
        return results

    def _full_table_backup(
        self,
        db: Session,
        backup_name: str,
        sheet_name: str,
        headers: list[str],
        model,
        mapper_func,
        query_filter=None,
    ):
        query = select(model).order_by(model.id.asc())
        if query_filter is not None:
            query = query.where(query_filter)
        rows = db.scalars(query).all()
        values = [mapper_func(r) for r in rows]
        max_id = max((r.id for r in rows), default=0)

        try:
            synced = google_sheet_service.sync_full_table(sheet_name, headers, values)
            backup_tracker_repo.update_status(db, backup_name, max_id, "success")
            return {
                "message": f"{sheet_name} synced",
                "status": "success",
                "backup_name": backup_name,
                "sheet_name": sheet_name,
                "rows_synced": synced,
                "total_rows": synced,
                "last_backup_id": max_id,
            }
        except Exception as e:
            logger.error("Error during full backup %s: %s", backup_name, e)
            last_id = backup_tracker_repo.get_by_name(db, backup_name)
            prev = last_id.last_backup_id if last_id else 0
            try:
                backup_tracker_repo.update_status(
                    db, backup_name, prev, "error", shorten_backup_error(e)
                )
            except Exception:
                logger.exception("Could not save backup_tracker error for %s", backup_name)
            raise

    def _generic_backup(
        self,
        db: Session,
        backup_name: str,
        sheet_name: str,
        headers: list[str],
        model,
        mapper_func,
        query_filter=None,
        *,
        full_refresh: bool = True,
    ):
        if full_refresh:
            return self._full_table_backup(
                db, backup_name, sheet_name, headers, model, mapper_func, query_filter
            )

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
                "rows_synced": 0,
                "total_rows": 0,
                "last_backup_id": last_id,
            }

        google_sheet_service.ensure_tab_and_headers(sheet_name, headers)
        values = []
        max_id = last_id
        for r in rows:
            values.append(mapper_func(r))
            max_id = max(max_id, r.id)
        appended_count = google_sheet_service.append_unique_rows_by_first_column(sheet_name, values)
        backup_tracker_repo.update_status(db, backup_name, max_id, "success")
        return {
            "message": f"{sheet_name} backup completed",
            "status": "success",
            "backup_name": backup_name,
            "sheet_name": sheet_name,
            "rows_added": appended_count,
            "rows_synced": appended_count,
            "total_rows": appended_count,
            "last_backup_id": max_id,
        }

    def backup_products(self, db: Session, *, full_refresh: bool = True):
        headers = [
            "ID",
            "Name",
            "Category ID",
            "In Price",
            "Out Price",
            "Commission",
            "Total Stock",
            "In Stock",
            "Sold",
            "Status",
            "Created At",
        ]

        def mapper(p: Product):
            return [
                p.id,
                p.name,
                p.category_id,
                p.in_price,
                p.out_price,
                p.commission,
                p.total_stock,
                p.in_stock,
                p.sold,
                p.status,
                p.created_at.isoformat() if p.created_at else "",
            ]

        return self._generic_backup(
            db,
            "products_google_sheet_backup",
            "Products",
            headers,
            Product,
            mapper,
            full_refresh=full_refresh,
        )

    def backup_categories(self, db: Session, *, full_refresh: bool = True):
        headers = ["ID", "Name", "Description", "Created At"]

        def mapper(c: Category):
            return [c.id, c.name, c.description, c.created_at.isoformat() if c.created_at else ""]

        return self._generic_backup(
            db,
            "categories_google_sheet_backup",
            "Categories",
            headers,
            Category,
            mapper,
            full_refresh=full_refresh,
        )

    def backup_invoices(self, db: Session, *, full_refresh: bool = True):
        headers = [
            "ID",
            "Customer Name",
            "Phone",
            "Address",
            "Source",
            "Delivery Type",
            "Delivery Price",
            "Delivery Date",
            "Discount",
            "Payment",
            "Delivery Status",
            "Seller ID",
            "Total",
            "Created At",
        ]

        def mapper(i: Invoice):
            return [
                i.id,
                i.customer_name,
                i.customer_phone,
                i.customer_address,
                i.source,
                i.delivery_type,
                i.delivery_price,
                i.delivery_date,
                i.discount,
                i.payment_method,
                i.delivery_status,
                i.user_id,
                i.total,
                i.created_at.isoformat() if i.created_at else "",
            ]

        return self._generic_backup(
            db,
            "invoices_google_sheet_backup",
            "Invoices",
            headers,
            Invoice,
            mapper,
            full_refresh=full_refresh,
        )

    def backup_invoice_details(self, db: Session, *, full_refresh: bool = True):
        headers = ["ID", "Invoice ID", "Product ID", "Qty", "Unit Price", "Line Total"]

        def mapper(it: CheckoutItem):
            return [it.id, it.invoice_id, it.product_id, it.quantity, it.price, it.total]

        return self._generic_backup(
            db,
            "invoice_details_google_sheet_backup",
            "Invoice Details",
            headers,
            CheckoutItem,
            mapper,
            full_refresh=full_refresh,
        )

    def backup_deliveries(self, db: Session, *, full_refresh: bool = True):
        headers = [
            "ID",
            "Invoice ID",
            "Customer",
            "Phone",
            "Address",
            "Status",
            "Type",
            "Price",
            "Delivery Date",
            "Created At",
        ]

        def mapper(i: Invoice):
            return [
                i.id,
                i.id,
                i.customer_name,
                i.customer_phone,
                i.customer_address,
                i.delivery_status,
                i.delivery_type,
                i.delivery_price,
                i.delivery_date,
                i.created_at.isoformat() if i.created_at else "",
            ]

        return self._generic_backup(
            db,
            "deliveries_google_sheet_backup",
            "Deliveries",
            headers,
            Invoice,
            mapper,
            and_(Invoice.delivery_type.isnot(None), Invoice.delivery_type != ""),
            full_refresh=full_refresh,
        )

    def backup_users(self, db: Session, *, full_refresh: bool = True):
        headers = ["ID", "Name", "Email", "Role", "Page Access", "Created At"]

        def mapper(u: User):
            role_name = u.role_rel.name if u.role_rel else ""
            perms = u.role_rel.page_access if u.role_rel else ""
            return [
                u.id,
                u.name,
                u.email,
                role_name,
                perms,
                u.created_at.isoformat() if u.created_at else "",
            ]

        if full_refresh:
            query = select(User).options(joinedload(User.role_rel)).order_by(User.id.asc())
            rows = db.scalars(query).all()
            values = [mapper(r) for r in rows]
            max_id = max((r.id for r in rows), default=0)
            synced = google_sheet_service.sync_full_table("Users", headers, values)
            backup_tracker_repo.update_status(db, "users_google_sheet_backup", max_id, "success")
            return {
                "status": "success",
                "message": "Users synced",
                "rows_synced": synced,
                "total_rows": synced,
                "backup_name": "users_google_sheet_backup",
                "sheet_name": "Users",
                "last_backup_id": max_id,
            }

        return self._generic_backup(
            db,
            "users_google_sheet_backup",
            "Users",
            headers,
            User,
            mapper,
            full_refresh=False,
        )

    def backup_roles(self, db: Session, *, full_refresh: bool = True):
        headers = ["ID", "Name", "Page Access", "Created At"]

        def mapper(r: Role):
            return [r.id, r.name, r.page_access, r.created_at.isoformat() if r.created_at else ""]

        return self._generic_backup(
            db,
            "roles_google_sheet_backup",
            "Roles",
            headers,
            Role,
            mapper,
            full_refresh=full_refresh,
        )

    def backup_suppliers(self, db: Session, *, full_refresh: bool = True):
        headers = ["ID", "Name", "Gender", "Address", "Phone", "Created At"]

        def mapper(s: Supplier):
            return [
                s.id,
                s.name,
                s.gender,
                s.address,
                s.phone_number,
                s.created_at.isoformat() if s.created_at else "",
            ]

        return self._generic_backup(
            db,
            "suppliers_google_sheet_backup",
            "Suppliers",
            headers,
            Supplier,
            mapper,
            full_refresh=full_refresh,
        )

    def backup_supplier_products(self, db: Session, *, full_refresh: bool = True):
        headers = [
            "ID",
            "Supplier ID",
            "Supplier Name",
            "Product Name",
            "Qty",
            "Unit Price",
            "Amount",
            "Updated By",
            "Created At",
        ]

        def mapper(sp: SupplierProduct):
            supplier_name = sp.supplier_rel.name if sp.supplier_rel else ""
            return [
                sp.id,
                sp.supplier_id,
                supplier_name,
                sp.product_name,
                sp.qty,
                sp.unit_price,
                sp.amount,
                sp.updated_by,
                sp.created_at.isoformat() if sp.created_at else "",
            ]

        if full_refresh:
            query = (
                select(SupplierProduct)
                .options(joinedload(SupplierProduct.supplier_rel))
                .order_by(SupplierProduct.id.asc())
            )
            rows = db.scalars(query).all()
            values = [mapper(r) for r in rows]
            max_id = max((r.id for r in rows), default=0)
            synced = google_sheet_service.sync_full_table("Supplier Products", headers, values)
            backup_tracker_repo.update_status(db, "supplier_products_google_sheet_backup", max_id, "success")
            return {
                "status": "success",
                "message": "Supplier Products synced",
                "rows_synced": synced,
                "total_rows": synced,
                "backup_name": "supplier_products_google_sheet_backup",
                "sheet_name": "Supplier Products",
                "last_backup_id": max_id,
            }

        return self._generic_backup(
            db,
            "supplier_products_google_sheet_backup",
            "Supplier Products",
            headers,
            SupplierProduct,
            mapper,
            full_refresh=False,
        )

    def backup_refunds(self, db: Session, *, full_refresh: bool = True):
        headers = [
            "ID",
            "Invoice No",
            "Sale Date",
            "Customer",
            "Product",
            "Seller",
            "Source",
            "Address",
            "Amount",
            "Checkout Item ID",
            "Product ID",
            "Qty",
            "Refund Reason",
            "Refunded At",
            "Created By",
        ]

        def mapper(r: RefundRecord):
            return [
                r.id,
                r.invoice_no,
                r.sale_date,
                r.customer,
                r.product,
                r.seller,
                r.source,
                r.address,
                r.amount,
                r.checkout_item_id,
                r.product_id,
                r.qty,
                r.refund_reason,
                r.refunded_at.isoformat() if r.refunded_at else "",
                r.created_by,
            ]

        return self._generic_backup(
            db,
            "refunds_google_sheet_backup",
            "Refunds",
            headers,
            RefundRecord,
            mapper,
            full_refresh=full_refresh,
        )


backup_service = BackupService()
