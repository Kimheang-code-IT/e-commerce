from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.dependencies.common import list_query_dependency
from app.models import CheckoutItem, Invoice, Product, RefundRecord, User
from app.schemas.common import ListQuery, RefundCreatePayload
from app.services.auth_service import get_current_user, require_permission
from app.services.cache_service import invalidate_after_checkout
from app.services.data_service import (
    apply_created_at_range,
    apply_sort,
    list_response,
    paginate_query,
    parse_csv,
    record_history,
    serialize_report_row,
)
from app.services.stock_fifo_service import allocate_fifo, return_fifo_stock
from app.shared.api_response import error_response

router = APIRouter(prefix="/refunds", tags=["refunds"], dependencies=[Depends(get_current_user)])


def serialize_refund(row: RefundRecord) -> dict:
    return {
        "id": row.id,
        "invoiceNo": row.invoice_no,
        "date": row.sale_date,
        "product": row.product,
        "customer": row.customer,
        "seller": row.seller,
        "source": row.source,
        "address": row.address,
        "amount": float(row.amount or 0),
        "productId": row.product_id,
        "qty": int(row.qty or 0),
        "checkoutItemId": row.checkout_item_id,
        "refundedAt": row.refunded_at.isoformat(),
        "refundReason": row.refund_reason or "",
    }


def _refunded_checkout_item_ids_subquery():
    return select(RefundRecord.checkout_item_id).where(RefundRecord.checkout_item_id.isnot(None))


@router.get("")
def list_refunds(
    query: ListQuery = Depends(list_query_dependency),
    product: str | None = None,
    source: str | None = None,
    province: str | None = None,
    _: User = Depends(require_permission("refund:view")),
    db: Session = Depends(get_db),
):
    q = select(RefundRecord)
    if query.search:
        keyword = query.search.strip()
        q = q.where(
            RefundRecord.invoice_no.ilike(f"%{keyword}%")
            | RefundRecord.customer.ilike(f"%{keyword}%")
            | RefundRecord.product.ilike(f"%{keyword}%")
            | RefundRecord.seller.ilike(f"%{keyword}%")
        )
    products = parse_csv(product)
    if products:
        q = q.where(or_(*[RefundRecord.product.ilike(f"%{name}%") for name in products]))
    sources = parse_csv(source)
    if sources:
        q = q.where(RefundRecord.source.in_(sources))
    provinces = parse_csv(province)
    if provinces:
        q = q.where(RefundRecord.address.in_(provinces))

    q = apply_created_at_range(q, query.dateFrom, query.dateTo, RefundRecord.refunded_at)
    q = apply_sort(
        q,
        query.sortBy,
        query.sortOrder,
        {
            "id": RefundRecord.id,
            "invoiceNo": RefundRecord.invoice_no,
            "amount": RefundRecord.amount,
            "refundedAt": RefundRecord.refunded_at,
            "date": RefundRecord.sale_date,
            "product": RefundRecord.product,
            "seller": RefundRecord.seller,
            "source": RefundRecord.source,
        },
    )
    q = q.order_by(RefundRecord.refunded_at.desc())
    rows, total = paginate_query(q, db, query.page, query.limit)
    return list_response([serialize_refund(row[0]) for row in rows], total)


@router.get("/search-invoices")
def search_refund_invoices(
    invoiceNo: str = Query("", min_length=1),
    exact: bool = Query(True),
    _: User = Depends(require_permission("refund:view")),
    db: Session = Depends(get_db),
):
    keyword = invoiceNo.strip()
    if not keyword:
        return list_response([], 0)

    refunded_ids = _refunded_checkout_item_ids_subquery()
    q = (
        select(CheckoutItem, Invoice, User)
        .join(Invoice, CheckoutItem.invoice_id == Invoice.id)
        .outerjoin(User, Invoice.user_id == User.id)
        .where(Invoice.status == "paid")
        .where(~CheckoutItem.id.in_(refunded_ids))
    )
    if exact:
        q = q.where(Invoice.invoice_no == keyword)
    else:
        q = q.where(Invoice.invoice_no.ilike(f"%{keyword}%"))

    q = q.order_by(Invoice.created_at.desc(), CheckoutItem.id.asc())
    rows = db.execute(q.limit(300)).all()
    result = [serialize_report_row(ci, inv, seller) for ci, inv, seller in rows]

    if not result and exact:
        exists = db.execute(select(Invoice.id).where(Invoice.invoice_no == keyword).limit(1)).scalar_one_or_none()
        if exists is not None:
            return error_response(
                status.HTTP_409_CONFLICT,
                "All line items for this invoice are already refunded",
                "ALL_REFUNDED",
            )

    return list_response(result, len(result))


def _resolve_checkout_items(db: Session, item) -> list[CheckoutItem]:
    """Report rows use invoice id; legacy rows use checkout_item id."""
    invoice = db.execute(
        select(Invoice).where(Invoice.invoice_no == item.invoiceNo).limit(1)
    ).scalar_one_or_none()
    if not invoice:
        return []

    refunded_ids = _refunded_checkout_item_ids_subquery()
    if int(item.id or 0) == int(invoice.id):
        return list(
            db.scalars(
                select(CheckoutItem)
                .where(
                    CheckoutItem.invoice_id == invoice.id,
                    ~CheckoutItem.id.in_(refunded_ids),
                )
                .order_by(CheckoutItem.id.asc())
            ).all()
        )

    checkout_item_id = int(item.id or 0)
    if checkout_item_id > 0:
        row = db.execute(
            select(CheckoutItem)
            .where(
                CheckoutItem.id == checkout_item_id,
                CheckoutItem.invoice_id == invoice.id,
            )
            .limit(1)
        ).scalar_one_or_none()
        if not row:
            return []
        already = db.execute(
            select(RefundRecord.id).where(RefundRecord.checkout_item_id == row.id).limit(1)
        ).scalar_one_or_none()
        return [] if already else [row]

    q = (
        select(CheckoutItem)
        .where(
            CheckoutItem.invoice_id == invoice.id,
            CheckoutItem.product_name == item.product,
            CheckoutItem.total == float(item.amount),
            ~CheckoutItem.id.in_(refunded_ids),
        )
        .order_by(CheckoutItem.id.asc())
    )
    product_id = int(item.productId or 0)
    if product_id > 0:
        q = q.where(CheckoutItem.product_id == product_id)
    one = db.execute(q.limit(1)).scalar_one_or_none()
    return [one] if one else []


def _resolve_checkout_item(db: Session, item) -> CheckoutItem | None:
    rows = _resolve_checkout_items(db, item)
    return rows[0] if rows else None


def _return_refund_stock(db: Session, *, checkout_item: CheckoutItem | None, item) -> tuple[int | None, int, int | None]:
    product_id = int(item.productId or 0)
    qty = int(item.qty or 0)
    sale_price = float(item.price or 0)
    checkout_item_id = int(item.id or 0) or None

    if checkout_item:
        product_id = int(checkout_item.product_id or product_id or 0)
        qty = int(checkout_item.quantity or qty or 0)
        sale_price = float(checkout_item.price or sale_price or 0)
        checkout_item_id = checkout_item.id

    if product_id <= 0 or qty <= 0:
        return None, 0, checkout_item_id

    product = db.execute(select(Product).where(Product.id == product_id).with_for_update()).scalar_one_or_none()
    if not product:
        return product_id, 0, checkout_item_id

    returned_qty = return_fifo_stock(db, product=product, qty=qty, sale_price=sale_price)
    product.in_stock = int(product.in_stock or 0) + returned_qty
    product.sold = max(0, int(product.sold or 0) - returned_qty)
    return product_id, returned_qty, checkout_item_id


@router.post("")
def create_refunds(
    payload: RefundCreatePayload,
    current_user: User = Depends(get_current_user),
    _: User = Depends(require_permission("refund:create")),
    db: Session = Depends(get_db),
):
    created: list[RefundRecord] = []
    skipped = 0
    for item in payload.records:
        checkout_items = _resolve_checkout_items(db, item)
        if not checkout_items:
            skipped += 1
            continue

        for checkout_item in checkout_items:
            duplicate = db.execute(
                select(RefundRecord.id).where(RefundRecord.checkout_item_id == checkout_item.id).limit(1)
            ).scalar_one_or_none()
            if duplicate:
                skipped += 1
                continue

            line_item = item.model_copy(
                update={
                    "product": checkout_item.product_name,
                    "productId": checkout_item.product_id,
                    "qty": int(checkout_item.quantity or 0),
                    "price": float(checkout_item.price or 0),
                    "amount": float(checkout_item.total or 0),
                }
            )
            product_id, returned_qty, checkout_item_id = _return_refund_stock(
                db, checkout_item=checkout_item, item=line_item
            )
            if returned_qty <= 0 and int(checkout_item.product_id or 0) > 0:
                skipped += 1
                continue

            row = RefundRecord(
                invoice_no=item.invoiceNo,
                sale_date=item.date,
                customer=item.customer,
                product=checkout_item.product_name,
                seller=item.seller,
                source=item.source,
                address=item.address,
                amount=float(checkout_item.total or 0),
                checkout_item_id=checkout_item_id,
                product_id=product_id,
                qty=returned_qty,
                refund_reason=(item.refundReason or "").strip(),
                created_by=current_user.id,
            )
            db.add(row)
            created.append(row)

    if not created:
        if skipped >= len(payload.records):
            return error_response(
                status.HTTP_409_CONFLICT,
                "All selected refund rows already exist or could not be processed",
                "CONFLICT",
            )
        return error_response(
            status.HTTP_400_BAD_REQUEST,
            "No refund rows were created",
            "BAD_REQUEST",
        )

    db.commit()
    for row in created:
        db.refresh(row)
    record_history(db, current_user.id, "Create", f"Created {len(created)} refund record(s)")
    db.commit()
    invalidate_after_checkout()
    return {"data": [serialize_refund(row) for row in created], "skipped": skipped}


@router.delete("/{refund_id}")
def delete_refund(
    refund_id: int,
    current_user: User = Depends(get_current_user),
    _: User = Depends(require_permission("refund:delete")),
    db: Session = Depends(get_db),
):
    row = db.get(RefundRecord, refund_id)
    if not row:
        return error_response(status.HTTP_404_NOT_FOUND, "Refund not found", "NOT_FOUND")

    product_id = int(row.product_id or 0)
    qty = int(row.qty or 0)
    if product_id > 0 and qty > 0:
        product = db.execute(select(Product).where(Product.id == product_id).with_for_update()).scalar_one_or_none()
        if product:
            if int(product.in_stock or 0) < qty:
                return error_response(
                    status.HTTP_409_CONFLICT,
                    f"Cannot delete refund because returned stock for {product.name} has already been sold",
                    "REFUND_STOCK_CONFLICT",
                )
            consumed = allocate_fifo(db, product_id, qty, consume=True)
            if not consumed:
                return error_response(
                    status.HTTP_409_CONFLICT,
                    f"Cannot delete refund because returned FIFO stock for {product.name} is not available",
                    "REFUND_STOCK_CONFLICT",
                )
            product.in_stock = max(0, int(product.in_stock or 0) - qty)
            product.sold = int(product.sold or 0) + qty

    db.delete(row)
    record_history(db, current_user.id, "Delete", f"Deleted refund #{refund_id}")
    db.commit()
    invalidate_after_checkout()
    return {"message": "Refund deleted"}
