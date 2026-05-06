from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models import CheckoutItem, Invoice, User
from app.services.auth_service import get_current_user, require_permission
from app.services.data_service import (
    apply_created_at_range,
    apply_sort,
    export_payload,
    list_response,
    paginate_query,
    parse_csv,
    serialize_report_row,
)

router = APIRouter(prefix="/reports-view", tags=["reports-view"], dependencies=[Depends(get_current_user)])


def _base_report_query():
    return (
        select(CheckoutItem, Invoice, User)
        .join(Invoice, CheckoutItem.invoice_id == Invoice.id)
        .outerjoin(User, Invoice.user_id == User.id)
    )


@router.get("")
def list_reports_view(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=200),
    search: str | None = None,
    product: str | None = None,
    dateFrom: str | None = None,
    dateTo: str | None = None,
    sortBy: str | None = None,
    sortOrder: str | None = Query(None, pattern="^(asc|desc)$"),
    _=Depends(require_permission("report:view")),
    db: Session = Depends(get_db),
):
    q = _base_report_query()
    if search:
        keyword = search.strip()
        q = q.where(
            Invoice.invoice_no.ilike(f"%{keyword}%")
            | Invoice.customer_name.ilike(f"%{keyword}%")
            | CheckoutItem.product_name.ilike(f"%{keyword}%")
            | User.name.ilike(f"%{keyword}%")
        )
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
            "invoiceNo": Invoice.invoice_no,
            "date": Invoice.created_at,
            "product": CheckoutItem.product_name,
            "seller": User.name,
            "amount": CheckoutItem.total,
        },
    )
    rows, total = paginate_query(q, db, page, limit)
    result = [serialize_report_row(ci, inv, seller) for ci, inv, seller in rows]
    return list_response(result, total)


@router.get("/export")
def export_reports_view(
    search: str | None = None,
    product: str | None = None,
    dateFrom: str | None = None,
    dateTo: str | None = None,
    _=Depends(require_permission("report:view")),
    db: Session = Depends(get_db),
):
    q = _base_report_query()
    if search:
        keyword = search.strip()
        q = q.where(
            Invoice.invoice_no.ilike(f"%{keyword}%")
            | Invoice.customer_name.ilike(f"%{keyword}%")
            | CheckoutItem.product_name.ilike(f"%{keyword}%")
            | User.name.ilike(f"%{keyword}%")
        )
    products = parse_csv(product)
    if products:
        q = q.where(CheckoutItem.product_name.in_(products))
    q = apply_created_at_range(q, dateFrom, dateTo, Invoice.created_at)
    pairs = db.execute(q).all()
    result = [serialize_report_row(ci, inv, seller) for ci, inv, seller in pairs]
    return export_payload(result, "reports-view")
