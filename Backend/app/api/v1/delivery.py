from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models import Invoice
from app.services.auth_service import get_current_user, require_permission
from app.services.data_service import (
    apply_created_at_range,
    apply_sort,
    list_response,
    paginate_query,
    parse_csv,
    serialize_delivery_invoice,
)

router = APIRouter(prefix="/deliveries-view", tags=["deliveries-view"], dependencies=[Depends(get_current_user)])


@router.get("")
def list_deliveries_view(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=200),
    search: str | None = None,
    address: str | None = None,
    deliveryType: str | None = None,
    dateFrom: str | None = None,
    dateTo: str | None = None,
    sortBy: str | None = None,
    sortOrder: str | None = Query(None, pattern="^(asc|desc)$"),
    _=Depends(require_permission("delivery:view")),
    db: Session = Depends(get_db),
):
    q = select(Invoice)
    if search:
        keyword = search.strip()
        q = q.where(
            Invoice.invoice_no.ilike(f"%{keyword}%")
            | Invoice.customer_name.ilike(f"%{keyword}%")
            | Invoice.customer_address.ilike(f"%{keyword}%")
        )
    addresses = parse_csv(address)
    if addresses:
        q = q.where(Invoice.customer_address.in_(addresses))
    delivery_types = parse_csv(deliveryType)
    if delivery_types:
        q = q.where(Invoice.delivery_type.in_(delivery_types))
    q = apply_created_at_range(q, dateFrom, dateTo, Invoice.created_at)
    q = apply_sort(
        q,
        sortBy,
        sortOrder,
        {
            "id": Invoice.id,
            "invoiceId": Invoice.invoice_no,
            "address": Invoice.customer_address,
            "deliveryType": Invoice.delivery_type,
            "date": Invoice.created_at,
        },
    )
    rows, total = paginate_query(q, db, page, limit)
    data = [serialize_delivery_invoice(row[0]) for row in rows]
    return list_response(data, total)
