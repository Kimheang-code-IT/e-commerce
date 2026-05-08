from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models import Invoice
from app.schemas.common import DeliveryUpdatePayload
from app.services.auth_service import get_current_user, require_permission
from app.services.data_service import (
    apply_created_at_range,
    apply_sort,
    list_response,
    paginate_query,
    parse_csv,
    record_history,
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
    deliveryStatus: str | None = None,
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
    statuses = parse_csv(deliveryStatus)
    if statuses:
        q = q.where(Invoice.delivery_status.in_(statuses))
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


@router.put("/{invoice_no}")
def update_delivery_status(
    invoice_no: str,
    payload: DeliveryUpdatePayload,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    _=Depends(require_permission("delivery:update")),
):
    inv = db.scalar(select(Invoice).where(Invoice.invoice_no == invoice_no))
    if not inv:
        raise HTTPException(status_code=404, detail="Invoice not found")

    old_status = inv.delivery_status
    inv.delivery_status = payload.deliveryStatus
    db.commit()
    db.refresh(inv)

    record_history(
        db,
        current_user.id,
        "Update",
        f"Updated delivery status for invoice {invoice_no} from {old_status} to {payload.deliveryStatus}",
    )

    return serialize_delivery_invoice(inv)
