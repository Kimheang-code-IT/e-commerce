from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.core.database import get_db
from app.models import CheckoutItem, Finance, Invoice, Product
from app.services.auth_service import get_current_user, require_permission
from app.services.finance_service import sync_finance_from_sold_products
from app.shared.api_response import error_response
from app.services.data_service import (
    apply_created_at_range,
    apply_sort,
    export_payload,
    list_response,
    paginate_query,
    serialize_finance_view,
)

router = APIRouter(prefix="/finance-view", tags=["finance-view"], dependencies=[Depends(get_current_user)])


class FinanceUpdatePayload(BaseModel):
    facebook: float | None = None
    other: float | None = None


@router.get("")
def list_finance_view(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=200),
    search: str | None = None,
    dateFrom: str | None = None,
    dateTo: str | None = None,
    sortBy: str | None = None,
    sortOrder: str | None = Query(None, pattern="^(asc|desc)$"),
    _=Depends(require_permission("finance:view")),
    db: Session = Depends(get_db),
):
    sync_finance_from_sold_products(db)

    q = select(Finance, Product).join(Product, Finance.product_id == Product.id)
    if search:
        keyword = search.strip()
        q = q.where(Product.name.ilike(f"%{keyword}%"))
    q = apply_created_at_range(q, dateFrom, dateTo, Finance.created_at)
    q = apply_sort(
        q,
        sortBy,
        sortOrder,
        {
            "id": Finance.id,
            "productName": Product.name,
            "createdAt": Finance.created_at,
        },
    )
    rows, total = paginate_query(q, db, page, limit)
    return list_response([serialize_finance_view(f, p) for f, p in rows], total)


@router.get("/export")
def export_finance_view(
    search: str | None = None,
    dateFrom: str | None = None,
    dateTo: str | None = None,
    _=Depends(require_permission("finance:view")),
    db: Session = Depends(get_db),
):
    sync_finance_from_sold_products(db)
    q = select(Finance, Product).join(Product, Finance.product_id == Product.id)
    if search:
        keyword = search.strip()
        q = q.where(Product.name.ilike(f"%{keyword}%"))
    q = apply_created_at_range(q, dateFrom, dateTo, Finance.created_at)
    rows = db.execute(q).all()
    return export_payload([serialize_finance_view(f, p) for f, p in rows], "finance-view")


@router.put("/{item_id}")
def update_finance(
    item_id: int,
    body: FinanceUpdatePayload,
    _=Depends(require_permission("finance:update")),
    db: Session = Depends(get_db),
):
    row = db.get(Finance, item_id)
    if not row:
        return error_response(status.HTTP_404_NOT_FOUND, "Not found", "NOT_FOUND")

    if body.facebook is not None:
        row.facebook = body.facebook
    if body.other is not None:
        row.other = body.other

    db.commit()
    db.refresh(row)

    # Return the full serialized view
    product = db.get(Product, row.product_id)
    return {"data": serialize_finance_view(row, product)}
