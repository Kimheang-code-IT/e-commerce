from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import CheckoutItem, Finance, Invoice, Product


def sync_finance_from_sold_products(db: Session) -> None:
    sales_rows = db.execute(
        select(
            CheckoutItem.product_id,
            func.coalesce(func.sum(CheckoutItem.quantity), 0).label("sold_qty"),
        )
        .join(Invoice, CheckoutItem.invoice_id == Invoice.id)
        .where(CheckoutItem.product_id.is_not(None), Invoice.status == "paid")
        .group_by(CheckoutItem.product_id)
    ).all()
    sold_map = {int(pid): float(qty or 0) for pid, qty in sales_rows if pid is not None}
    existing_finance = {row.product_id: row for row in db.scalars(select(Finance)).all()}
    products = {p.id: p for p in db.scalars(select(Product)).all()}
    changed = False
    for product_id, product in products.items():
        sold_qty = sold_map.get(product_id, 0.0)
        commission_total = sold_qty * float(product.commission or 0)
        finance_row = existing_finance.get(product_id)
        if finance_row is None:
            db.add(
                Finance(
                    product_id=product_id,
                    total_commission=commission_total,
                    total_sold_product=sold_qty,
                )
            )
            changed = True
            continue
        if float(finance_row.total_sold_product or 0) != sold_qty or float(finance_row.total_commission or 0) != commission_total:
            finance_row.total_sold_product = sold_qty
            finance_row.total_commission = commission_total
            changed = True
    if changed:
        db.commit()
