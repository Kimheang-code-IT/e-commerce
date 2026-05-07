from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models import Product, User, Invoice, CheckoutItem
from app.services.auth_service import get_current_user
from app.services.data_service import apply_created_at_range

router = APIRouter(prefix="/dashboard", tags=["dashboard"], dependencies=[Depends(get_current_user)])


@router.get("/summary")
def get_dashboard_summary(
    dateFrom: str | None = Query(None),
    dateTo: str | None = Query(None),
    db: Session = Depends(get_db)
):
    # Total unique products (Static)
    total_products = db.scalar(select(func.count(Product.id))) or 0
    
    # Total quantity in stock across all products (Static)
    total_in_stock = db.scalar(select(func.sum(Product.in_stock))) or 0
    
    # Count of products that are out of stock (Static)
    out_of_stock_count = db.scalar(select(func.count(Product.id)).where(Product.in_stock <= 0)) or 0
    
    # Total quantity sold across all products (Filtered by Date)
    stmt_sold = select(func.sum(CheckoutItem.quantity)).join(Invoice, CheckoutItem.invoice_id == Invoice.id)
    stmt_sold = apply_created_at_range(stmt_sold, dateFrom, dateTo, Invoice.created_at)
    total_sold = db.scalar(stmt_sold) or 0

    # Provincial Distribution (Total Products Sold by Province)
    stmt_dist = (
        select(Invoice.customer_address, func.sum(CheckoutItem.quantity))
        .join(CheckoutItem, Invoice.id == CheckoutItem.invoice_id)
        .where(Invoice.customer_address != None, Invoice.customer_address != "", Invoice.customer_address != "Nothing")
        .group_by(Invoice.customer_address)
    )
    stmt_dist = apply_created_at_range(stmt_dist, dateFrom, dateTo, Invoice.created_at)
    dist = db.execute(stmt_dist).all()
    provincial_distribution = [{"name": row[0], "value": int(row[1] or 0)} for row in dist]

    # Top Selling Products (Filtered by Date)
    stmt_top = (
        select(Product.name, func.sum(CheckoutItem.quantity))
        .join(CheckoutItem, Product.id == CheckoutItem.product_id)
        .join(Invoice, CheckoutItem.invoice_id == Invoice.id)
        .group_by(Product.name)
        .order_by(func.sum(CheckoutItem.quantity).desc())
        .limit(10)
    )
    stmt_top = apply_created_at_range(stmt_top, dateFrom, dateTo, Invoice.created_at)
    top_rows = db.execute(stmt_top).all()
    top_products = [{"name": row[0], "value": int(row[1] or 0)} for row in top_rows]

    # User Commission Distribution
    stmt_comm = (
        select(User.name, func.sum(CheckoutItem.quantity * Product.commission))
        .join(Invoice, User.id == Invoice.user_id)
        .join(CheckoutItem, Invoice.id == CheckoutItem.invoice_id)
        .join(Product, CheckoutItem.product_id == Product.id)
        .group_by(User.name)
    )
    stmt_comm = apply_created_at_range(stmt_comm, dateFrom, dateTo, Invoice.created_at)
    comm_rows = db.execute(stmt_comm).all()
    user_commissions = [{"name": row[0], "value": float(row[1] or 0)} for row in comm_rows]

    return {
        "data": {
            "totalProducts": int(total_products),
            "productsInStock": int(total_in_stock),
            "productsOutOfStock": int(out_of_stock_count),
            "soldProducts": int(total_sold),
            "provincialDistribution": provincial_distribution,
            "topProducts": top_products,
            "userCommissions": user_commissions
        }
    }
