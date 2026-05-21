from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models import Product, User, Invoice, CheckoutItem, Category
from app.services.auth_service import get_current_user
from app.services.cache_service import PREFIX_DASHBOARD, cached_response
from app.services.data_service import apply_created_at_range

router = APIRouter(prefix="/dashboard", tags=["dashboard"], dependencies=[Depends(get_current_user)])


@router.get("/summary")
def get_dashboard_summary(
    dateFrom: str | None = Query(None),
    dateTo: str | None = Query(None),
    categoryId: str | None = Query(None),
    productId: int | None = Query(None, ge=1),
    db: Session = Depends(get_db),
):
    cache_parts = {
        "dateFrom": dateFrom,
        "dateTo": dateTo,
        "categoryId": categoryId,
        "productId": productId,
    }
    return cached_response(PREFIX_DASHBOARD, cache_parts, lambda: _dashboard_summary_body(
        db=db,
        dateFrom=dateFrom,
        dateTo=dateTo,
        categoryId=categoryId,
        productId=productId,
    ))


def _dashboard_summary_body(
    *,
    db: Session,
    dateFrom: str | None,
    dateTo: str | None,
    categoryId: str | None,
    productId: int | None,
):
    category_pk: int | None = None
    if categoryId:
        category_pk = Category.from_public_id(categoryId)

    product_filter = Product.id == productId if productId else None
    category_filter = Product.category_id == category_pk if category_pk is not None else None

    def _apply_product_scope(stmt):
        if product_filter is not None:
            stmt = stmt.where(product_filter)
        if category_filter is not None:
            stmt = stmt.where(category_filter)
        return stmt

    # Total unique products (Static)
    stmt_total_products = select(func.count(Product.id))
    stmt_total_products = _apply_product_scope(stmt_total_products)
    total_products = db.scalar(stmt_total_products) or 0
    
    # Total quantity in stock across all products (Static)
    stmt_total_in_stock = select(func.sum(Product.in_stock))
    stmt_total_in_stock = _apply_product_scope(stmt_total_in_stock)
    total_in_stock = db.scalar(stmt_total_in_stock) or 0
    
    # Count of products that are out of stock (Static)
    stmt_out_of_stock = select(func.count(Product.id)).where(Product.in_stock <= 0)
    stmt_out_of_stock = _apply_product_scope(stmt_out_of_stock)
    out_of_stock_count = db.scalar(stmt_out_of_stock) or 0
    
    # Total quantity sold across all products (Filtered by Date)
    stmt_sold = (
        select(func.sum(CheckoutItem.quantity))
        .join(Invoice, CheckoutItem.invoice_id == Invoice.id)
        .join(Product, Product.id == CheckoutItem.product_id)
    )
    stmt_sold = _apply_product_scope(stmt_sold)
    stmt_sold = apply_created_at_range(stmt_sold, dateFrom, dateTo, Invoice.created_at)
    total_sold = db.scalar(stmt_sold) or 0

    # Provincial Distribution (Total Products Sold by Province)
    stmt_dist = (
        select(Invoice.customer_address, func.sum(CheckoutItem.quantity))
        .join(CheckoutItem, Invoice.id == CheckoutItem.invoice_id)
        .join(Product, Product.id == CheckoutItem.product_id)
        .where(Invoice.customer_address != None, Invoice.customer_address != "", Invoice.customer_address != "Nothing")
        .group_by(Invoice.customer_address)
    )
    stmt_dist = _apply_product_scope(stmt_dist)
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
    stmt_top = _apply_product_scope(stmt_top)
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
    stmt_comm = _apply_product_scope(stmt_comm)
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
