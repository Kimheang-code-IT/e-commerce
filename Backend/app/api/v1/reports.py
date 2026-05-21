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
from app.services.filter_options_service import report_filter_options

router = APIRouter(prefix="/reports-view", tags=["reports-view"], dependencies=[Depends(get_current_user)])


from sqlalchemy import or_

def _base_report_query():
    return (
        select(Invoice, User)
        .outerjoin(User, Invoice.user_id == User.id)
    )


@router.get("")
def list_reports_view(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=200),
    search: str | None = None,
    product: str | None = None,
    source: str | None = None,
    province: str | None = None,
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
            | Invoice.product_name.ilike(f"%{keyword}%")
            | User.name.ilike(f"%{keyword}%")
        )
    products = parse_csv(product)
    if products:
        conditions = [Invoice.product_name.ilike(f"%{p}%") for p in products]
        q = q.where(or_(*conditions))

    sources = parse_csv(source)
    if sources:
        q = q.where(or_(*[Invoice.source == s for s in sources]))

    provinces = parse_csv(province)
    if provinces:
        q = q.where(or_(*[Invoice.customer_address == p for p in provinces]))

    q = apply_created_at_range(q, dateFrom, dateTo, Invoice.created_at)
    q = apply_sort(
        q,
        sortBy,
        sortOrder,
        {
            "id": Invoice.id,
            "invoiceNo": Invoice.invoice_no,
            "date": Invoice.created_at,
            "product": Invoice.product_name,
            "seller": User.name,
            "amount": Invoice.total,
        },
    )
    rows, total = paginate_query(q, db, page, limit)
    result = [serialize_report_row(None, inv, seller) for inv, seller in rows]
    return list_response(result, total)


@router.get("/export")
def export_reports_view(
    search: str | None = None,
    product: str | None = None,
    source: str | None = None,
    province: str | None = None,
    dateFrom: str | None = None,
    dateTo: str | None = None,
    format: str = Query("json", pattern="^(json|csv)$"),
    _=Depends(require_permission("report:view")),
    db: Session = Depends(get_db),
):
    q = _base_report_query()
    if search:
        keyword = search.strip()
        q = q.where(
            Invoice.invoice_no.ilike(f"%{keyword}%")
            | Invoice.customer_name.ilike(f"%{keyword}%")
            | Invoice.product_name.ilike(f"%{keyword}%")
            | User.name.ilike(f"%{keyword}%")
        )
    products = parse_csv(product)
    if products:
        conditions = [Invoice.product_name.ilike(f"%{p}%") for p in products]
        q = q.where(or_(*conditions))

    sources = parse_csv(source)
    if sources:
        q = q.where(or_(*[Invoice.source == s for s in sources]))

    provinces = parse_csv(province)
    if provinces:
        q = q.where(or_(*[Invoice.customer_address == p for p in provinces]))

    q = apply_created_at_range(q, dateFrom, dateTo, Invoice.created_at)
    pairs = db.execute(q).all()
    result = [serialize_report_row(None, inv, seller) for inv, seller in pairs]
    return export_payload(result, "reports-view", format)


@router.get("/filter-options")
def reports_filter_options(
    dateFrom: str | None = None,
    dateTo: str | None = None,
    _=Depends(require_permission("report:view")),
    db: Session = Depends(get_db),
):
    return {"data": report_filter_options(db, date_from=dateFrom, date_to=dateTo)}
