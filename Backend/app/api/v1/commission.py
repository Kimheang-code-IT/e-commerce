from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models import CheckoutItem, Invoice, Product, Role, User
from app.services.auth_service import get_current_user, require_permission
from app.services.data_service import (
    apply_created_at_range,
    apply_sort,
    export_payload,
    list_response,
    paginate_query,
    parse_csv,
    serialize_commission_row,
)

router = APIRouter(prefix="/commission-view", tags=["commission-view"], dependencies=[Depends(get_current_user)])


def _base_query():
    return (
        select(CheckoutItem, Invoice, User, Product)
        .join(Invoice, CheckoutItem.invoice_id == Invoice.id)
        .join(User, Invoice.user_id == User.id)
        .outerjoin(Product, CheckoutItem.product_id == Product.id)
        .where(Invoice.status == "paid")
    )


@router.get("")
def list_commission_view(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=200),
    search: str | None = None,
    product: str | None = None,
    dateFrom: str | None = None,
    dateTo: str | None = None,
    sortBy: str | None = None,
    sortOrder: str | None = Query(None, pattern="^(asc|desc)$"),
    _=Depends(require_permission("commission:view")),
    db: Session = Depends(get_db),
):
    q = _base_query()
    if search:
        keyword = search.strip()
        q = q.where(User.name.ilike(f"%{keyword}%") | Invoice.invoice_no.ilike(f"%{keyword}%"))
    products = parse_csv(product)
    if products:
        q = q.where(CheckoutItem.product_name.in_(products))
    q = apply_created_at_range(q, dateFrom, dateTo, Invoice.created_at)
    q = apply_sort(
        q,
        sortBy,
        sortOrder,
        {
            "id": CheckoutItem.id,
            "seller": User.name,
            "date": Invoice.created_at,
            "amount": CheckoutItem.total,
        },
    )
    rows, total = paginate_query(q, db, page, limit)
    data = [serialize_commission_row(ci, inv, seller, prod) for ci, inv, seller, prod in rows]
    return list_response(data, total)


@router.get("/export")
def export_commission_view(
    search: str | None = None,
    product: str | None = None,
    dateFrom: str | None = None,
    dateTo: str | None = None,
    _=Depends(require_permission("commission:view")),
    db: Session = Depends(get_db),
):
    q = _base_query()
    if search:
        keyword = search.strip()
        q = q.where(User.name.ilike(f"%{keyword}%") | Invoice.invoice_no.ilike(f"%{keyword}%"))
    products = parse_csv(product)
    if products:
        q = q.where(CheckoutItem.product_name.in_(products))
    q = apply_created_at_range(q, dateFrom, dateTo, Invoice.created_at)
    rows = db.execute(q).all()
    data = [serialize_commission_row(ci, inv, seller, prod) for ci, inv, seller, prod in rows]
    return export_payload(data, "commission-view")
