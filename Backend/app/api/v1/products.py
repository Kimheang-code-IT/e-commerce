from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models import Product, ProductDamage, ProductStockAddition, User
from app.schemas.common import ListQuery, ProductCreatePayload, ProductUpdatePayload
from app.services.auth_service import require_permission
from app.services.data_service import (
    apply_created_at_range,
    list_response,
    paginate_query,
)
from app.dependencies.common import list_query_dependency
from app.services.product_service import (
    create_product_service,
    delete_product_service,
    list_products_service,
    update_product_service,
)
from app.services.product_stock_status import stock_status_tier

router = APIRouter()


@router.get("/products/stock-status")
def get_product_stock_status(
    inStock: int = Query(..., ge=0, description="Current on-hand quantity"),
    _: User = Depends(require_permission("product:view")),
):
    """Returns stock tier for UI labels (`aLot` / `lower` / `out`). Same rules as `stockStatus` on product payloads."""
    return {"data": {"stockStatus": stock_status_tier(inStock)}}


@router.get("/products")
def list_products(
    query: ListQuery = Depends(list_query_dependency),
    category: str | None = None,
    _: User = Depends(require_permission("product:view")),
    db: Session = Depends(get_db),
):
    return list_products_service(db=db, query=query, category=category)


@router.get("/products-view")
def list_products_view(
    query: ListQuery = Depends(list_query_dependency),
    category: str | None = None,
    _: User = Depends(require_permission("product:view")),
    db: Session = Depends(get_db),
):
    """Aligned with SQL view `products_view` (implemented via aggregates + product rows)."""
    return list_products_service(db=db, query=query, category=category)


@router.post("/products")
def create_product(
    body: ProductCreatePayload,
    _: User = Depends(require_permission("product:create")),
    db: Session = Depends(get_db),
):
    return create_product_service(db=db, body=body)


@router.put("/products/{item_id}")
def update_product(
    item_id: int,
    body: ProductUpdatePayload,
    _: User = Depends(require_permission("product:update")),
    db: Session = Depends(get_db),
):
    return update_product_service(db=db, item_id=item_id, body=body)


@router.delete("/products/{item_id}")
def delete_product(
    item_id: int,
    _: User = Depends(require_permission("product:delete")),
    db: Session = Depends(get_db),
):
    return delete_product_service(db=db, item_id=item_id)


@router.get("/products/{item_id}/stock-additions")
def list_product_stock_additions(
    item_id: int,
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=200),
    dateFrom: str | None = None,
    dateTo: str | None = None,
    _: User = Depends(require_permission("product:view")),
    db: Session = Depends(get_db),
):
    q = select(ProductStockAddition).where(ProductStockAddition.product_id == item_id)
    q = apply_created_at_range(q, dateFrom, dateTo, ProductStockAddition.created_at)
    q = q.order_by(ProductStockAddition.created_at.desc())
    rows, total = paginate_query(q, db, page, limit)
    return list_response(
        [
            {
                "id": r[0].id,
                "qty": r[0].qty,
                "note": r[0].note,
                "createdAt": r[0].created_at.isoformat(),
            }
            for r in rows
        ],
        total,
    )


@router.get("/products/{item_id}/damages")
def list_product_damages(
    item_id: int,
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=200),
    dateFrom: str | None = None,
    dateTo: str | None = None,
    _: User = Depends(require_permission("product:view")),
    db: Session = Depends(get_db),
):
    q = select(ProductDamage).where(ProductDamage.product_id == item_id)
    q = apply_created_at_range(q, dateFrom, dateTo, ProductDamage.created_at)
    q = q.order_by(ProductDamage.created_at.desc())
    rows, total = paginate_query(q, db, page, limit)
    return list_response(
        [
            {
                "id": r[0].id,
                "qty": r[0].qty,
                "note": r[0].note,
                "createdAt": r[0].created_at.isoformat(),
            }
            for r in rows
        ],
        total,
    )
