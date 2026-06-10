from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models import Invoice, User
from app.schemas.common import DeliveryUpdatePayload
from app.security import user_has_role
from app.services.auth_service import get_current_user, require_permission
from app.services.cache_service import invalidate_after_checkout
from app.services.data_service import (
    apply_created_at_range,
    apply_sort,
    list_response,
    paginate_query,
    parse_csv,
    record_history,
    serialize_delivery_invoice,
)
from app.services.filter_options_service import delivery_filter_options
from app.shared.pagination_constants import MAX_LIST_PAGE_SIZE

router = APIRouter(prefix="/deliveries-view", tags=["deliveries-view"], dependencies=[Depends(get_current_user)])


def _delivery_scope_user_id(user: User) -> int | None:
    """Admins see all deliveries; everyone else sees only their own checkouts."""
    if user_has_role(user, "admin"):
        return None
    return user.id


def _base_query(*, seller_user_id: int | None = None):
    q = select(Invoice, User).join(User, Invoice.user_id == User.id)
    if seller_user_id is not None:
        q = q.where(Invoice.user_id == seller_user_id)
    return q


@router.get("")
def list_deliveries_view(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=MAX_LIST_PAGE_SIZE),
    search: str | None = None,
    address: str | None = None,
    deliveryType: str | None = None,
    deliveryStatus: str | None = None,
    dateFrom: str | None = None,
    dateTo: str | None = None,
    sortBy: str | None = None,
    sortOrder: str | None = Query(None, pattern="^(asc|desc)$"),
    current_user=Depends(require_permission("delivery:view")),
    db: Session = Depends(get_db),
):
    q = _base_query(seller_user_id=_delivery_scope_user_id(current_user))
    if search:
        keyword = search.strip()
        q = q.where(
            Invoice.invoice_no.ilike(f"%{keyword}%")
            | Invoice.customer_name.ilike(f"%{keyword}%")
            | Invoice.customer_address.ilike(f"%{keyword}%")
            | User.name.ilike(f"%{keyword}%")
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
            "seller": User.name,
            "address": Invoice.customer_address,
            "deliveryType": Invoice.delivery_type,
            "deliveryPrice": Invoice.delivery_price,
            "total": Invoice.total,
            "date": Invoice.created_at,
        },
    )
    rows, total = paginate_query(q, db, page, limit)
    data = [serialize_delivery_invoice(inv, seller=seller.name) for inv, seller in rows]
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

    scope_user_id = _delivery_scope_user_id(current_user)
    if scope_user_id is not None and inv.user_id != scope_user_id:
        raise HTTPException(status_code=403, detail="Not allowed to update this delivery")

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
    db.commit()
    invalidate_after_checkout()

    return serialize_delivery_invoice(inv)


@router.get("/filter-options")
def deliveries_filter_options(
    dateFrom: str | None = None,
    dateTo: str | None = None,
    current_user=Depends(require_permission("delivery:view")),
    db: Session = Depends(get_db),
):
    scope_user_id = _delivery_scope_user_id(current_user)
    return {
        "data": delivery_filter_options(
            db,
            date_from=dateFrom,
            date_to=dateTo,
            seller_user_id=scope_user_id,
        )
    }
