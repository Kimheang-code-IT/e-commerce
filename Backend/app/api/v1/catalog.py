from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models import Category, Product
from app.repositories.product_repository import list_products_query
from app.shared.pagination_constants import MAX_LIST_PAGE_SIZE
from app.services.data_service import (
    list_response,
    paginate_query,
    serialize_catalog_category,
    serialize_catalog_product,
)

router = APIRouter()


@router.get("/catalog/categories")
def list_public_categories(
    page: int = Query(1, ge=1),
    limit: int = Query(100, ge=1, le=MAX_LIST_PAGE_SIZE),
    db: Session = Depends(get_db),
):
    """Categories that have at least one active catalog product."""
    q = (
        select(Category, func.count(Product.id).label("active_product_count"))
        .join(Product, Product.category_id == Category.id)
        .where(Product.status == "active", Product.show_on_website.is_(True))
        .group_by(Category.id)
        .order_by(Category.name.asc())
    )
    rows, total = paginate_query(q, db, page, limit)
    return list_response(
        [
            serialize_catalog_category(row[0], product_count=int(row[1] or 0))
            for row in rows
        ],
        total,
    )


@router.get("/catalog/products")
def list_public_products(
    page: int = Query(1, ge=1),
    limit: int = Query(200, ge=1, le=MAX_LIST_PAGE_SIZE),
    search: str | None = None,
    category: str | None = None,
    db: Session = Depends(get_db),
):
    q = list_products_query(db, search=search, category=category)
    q = q.where(
        Product.status == "active",
        Product.show_on_website.is_(True),
    ).order_by(Product.id.desc())
    rows, total = paginate_query(q, db, page, limit)
    products = [row[0] for row in rows]
    return list_response([serialize_catalog_product(row) for row in products], total)
