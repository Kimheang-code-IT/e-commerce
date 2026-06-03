from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models import Product, ProductDamage, ProductStockAddition, User
from app.schemas.common import (
    ListQuery,
    ProductCreatePayload,
    ProductStockAdjustPayload,
    ProductUpdatePayload,
    StockAdditionUpdatePayload,
    StockDamageUpdatePayload,
)
from app.services.auth_service import get_current_user, require_permission
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
from app.services.product_stock_adjust_service import adjust_product_stock_service
from app.services.product_stock_history_service import (
    update_stock_addition_service,
    update_stock_damage_service,
)
from app.services.cache_service import PREFIX_STOCK, cached_response
from app.services.product_stock_status import stock_status_tier

router = APIRouter()


@router.get("/products/stock-status")
def get_product_stock_status(
    inStock: int = Query(..., ge=0, description="Current on-hand quantity"),
    _: User = Depends(require_permission("product:view")),
):
    """Returns stock tier for UI labels (`aLot` / `lower` / `out`). Same rules as `stockStatus` on product payloads."""
    return cached_response(
        PREFIX_STOCK,
        {"inStock": inStock},
        lambda: {"data": {"stockStatus": stock_status_tier(inStock)}},
    )


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
    current_user: User = Depends(get_current_user),
    _: User = Depends(require_permission("product:create")),
    db: Session = Depends(get_db),
):
    return create_product_service(db=db, body=body, user_id=current_user.id)


@router.post("/products/{item_id}/stock-adjust")
def adjust_product_stock(
    item_id: int,
    body: ProductStockAdjustPayload,
    current_user: User = Depends(get_current_user),
    _: User = Depends(require_permission("product:adjust-stock")),
    db: Session = Depends(get_db),
):
    return adjust_product_stock_service(db=db, item_id=item_id, body=body, user_id=current_user.id)


@router.put("/products/{item_id}")
def update_product(
    item_id: int,
    body: ProductUpdatePayload,
    current_user: User = Depends(get_current_user),
    _: User = Depends(require_permission("product:update")),
    db: Session = Depends(get_db),
):
    return update_product_service(db=db, item_id=item_id, body=body, user_id=current_user.id)


@router.delete("/products/{item_id}")
def delete_product(
    item_id: int,
    current_user: User = Depends(get_current_user),
    _: User = Depends(require_permission("product:delete")),
    db: Session = Depends(get_db),
):
    return delete_product_service(db=db, item_id=item_id, user_id=current_user.id)


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
                "qtyRemaining": r[0].qty_remaining,
                "inPrice": r[0].in_price,
                "outPrice": r[0].out_price,
                "note": r[0].note,
                "createdAt": r[0].created_at.isoformat(),
            }
            for r in rows
        ],
        total,
    )


@router.patch("/products/{item_id}/stock-additions/{record_id}")
def update_product_stock_addition(
    item_id: int,
    record_id: int,
    body: StockAdditionUpdatePayload,
    current_user: User = Depends(get_current_user),
    _: User = Depends(require_permission("product:adjust-stock")),
    db: Session = Depends(get_db),
):
    return update_stock_addition_service(
        db=db,
        product_id=item_id,
        record_id=record_id,
        body=body,
        user_id=current_user.id,
    )


@router.patch("/products/{item_id}/damages/{record_id}")
def update_product_damage(
    item_id: int,
    record_id: int,
    body: StockDamageUpdatePayload,
    current_user: User = Depends(get_current_user),
    _: User = Depends(require_permission("product:adjust-stock")),
    db: Session = Depends(get_db),
):
    return update_stock_damage_service(
        db=db,
        product_id=item_id,
        record_id=record_id,
        body=body,
        user_id=current_user.id,
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
