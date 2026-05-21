import base64
import json
import logging

from fastapi import status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models import CheckoutItem, Invoice, User
from app.repositories.pos_repository import get_products_by_ids, get_products_by_ids_for_update, next_invoice_no
from app.schemas.common import PosCheckoutPayload, PosPreviewSessionCreatePayload
from app.security.rbac import user_has_permission
from app.services.checkout_enqueue import enqueue_checkout_followups
from app.services.data_service import record_history
from app.services.invoice_pdf_service import ensure_invoice_pdf, invoice_pdf_api_path
from app.shared.api_response import error_response
from app.utils.timezone import cambodia_now

logger = logging.getLogger(__name__)


def encode_preview(payload: PosPreviewSessionCreatePayload) -> dict:
    raw = json.dumps(payload.invoices, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    preview_key = base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=")
    return {"previewKey": preview_key}


def _clamp_discount_usd(subtotal: float, discount_amount: float) -> float:
    da = max(0.0, float(discount_amount or 0))
    return min(da, float(subtotal))


def _checkout_grand_total(subtotal: float, discount_amount: float, delivery_price: float) -> float:
    return max(
        0.0,
        float(subtotal) - float(discount_amount or 0) + float(delivery_price or 0),
    )


def decode_preview(preview_key: str):
    pad = "=" * (-len(preview_key) % 4)
    raw = base64.urlsafe_b64decode(preview_key + pad)
    parsed = json.loads(raw.decode("utf-8"))
    return parsed if isinstance(parsed, list) else []


def _resolve_seller_id(db: Session, payload: PosCheckoutPayload, current_user: User) -> int | dict:
    """Only admins may attribute checkout to another user."""
    if payload.sellerId is None or payload.sellerId == current_user.id:
        return current_user.id
    if not user_has_permission(current_user, "user:view"):
        return current_user.id
    seller = db.get(User, payload.sellerId)
    if not seller:
        return error_response(status.HTTP_400_BAD_REQUEST, "Invalid seller", "BAD_REQUEST")
    return seller.id


def _build_checkout_lines(db: Session, payload: PosCheckoutPayload):
    product_ids = [line.productId for line in payload.lines]
    if not product_ids:
        return error_response(status.HTTP_400_BAD_REQUEST, "Cart is empty", "BAD_REQUEST")

    product_map = {row.id: row for row in get_products_by_ids_for_update(db, product_ids)}
    missing = [pid for pid in product_ids if pid not in product_map]
    if missing:
        return error_response(
            status.HTTP_400_BAD_REQUEST,
            f"Unknown product id(s): {', '.join(str(i) for i in missing)}",
            "BAD_REQUEST",
        )

    subtotal = 0.0
    line_totals: list[tuple[object, int, float]] = []
    for line in payload.lines:
        product = product_map[line.productId]
        if int(product.in_stock or 0) < line.qty:
            return error_response(
                status.HTTP_400_BAD_REQUEST,
                f"Not enough stock for {product.name} (Available: {product.in_stock})",
                "NOT_ENOUGH_STOCK",
            )
        line_total = float(product.out_price) * line.qty
        subtotal += line_total
        line_totals.append((product, line.qty, line_total))

    discount_amount = _clamp_discount_usd(subtotal, float(payload.discountAmount))
    delivery_price = float(payload.deliveryPrice or 0)
    total = _checkout_grand_total(subtotal, discount_amount, delivery_price)
    return {
        "subtotal": subtotal,
        "discount_amount": discount_amount,
        "delivery_price": delivery_price,
        "total": total,
        "line_totals": line_totals,
    }


def calculate_totals_service(*, db: Session, payload: PosCheckoutPayload):
    product_ids = [line.productId for line in payload.lines]
    product_map = {row.id: row for row in get_products_by_ids(db, product_ids)}
    subtotal = 0.0
    for line in payload.lines:
        product = product_map.get(line.productId)
        if not product:
            return error_response(
                status.HTTP_400_BAD_REQUEST,
                f"Unknown product id: {line.productId}",
                "BAD_REQUEST",
            )
        if int(product.in_stock or 0) < line.qty:
            return error_response(
                status.HTTP_400_BAD_REQUEST,
                f"Not enough stock for {product.name} (Available: {product.in_stock})",
                "NOT_ENOUGH_STOCK",
            )
        subtotal += float(product.out_price) * line.qty
    discount_amount = _clamp_discount_usd(subtotal, float(payload.discountAmount))
    delivery_price = float(payload.deliveryPrice or 0)
    total = _checkout_grand_total(subtotal, discount_amount, delivery_price)
    return {"subtotal": subtotal, "discountAmount": discount_amount, "total": total}


def complete_checkout_service(*, db: Session, payload: PosCheckoutPayload, current_user):
    """
    Synchronous checkout: invoice, line items, stock, and history in one DB transaction.
    Post-commit: Celery (PDF optional sync, notify, print, cache invalidation).
    """
    seller = _resolve_seller_id(db, payload, current_user)
    if not isinstance(seller, int):
        return seller

    built = _build_checkout_lines(db, payload)
    if not isinstance(built, dict) or "line_totals" not in built:
        return built

    subtotal = built["subtotal"]
    discount_amount = built["discount_amount"]
    delivery_price = built["delivery_price"]
    total = built["total"]
    line_totals = built["line_totals"]
    summary_names = ", ".join([item[0].name for item in line_totals])
    if len(summary_names) > 177:
        summary_names = summary_names[:177] + "..."

    invoice_no = next_invoice_no(db)
    if not str(invoice_no).startswith("DNS-"):
        raise RuntimeError("Invoice numbering must use DNS-* format")

    try:
        invoice = Invoice(
            invoice_no=invoice_no,
            user_id=seller,
            customer_name=payload.customerName,
            customer_phone=payload.customerPhone,
            customer_address=payload.customerAddress,
            product_name=summary_names,
            delivery_type=payload.deliveryType,
            delivery_price=delivery_price,
            delivery_date=payload.deliveryDate,
            delivery_status=payload.deliveryStatus or "pending",
            subtotal=subtotal,
            discount=discount_amount,
            total=total,
            source=payload.source or "other",
            payment_method=payload.paymentMethod or "cash",
            status="paid",
        )
        db.add(invoice)
        db.flush()

        for product, qty, line_total in line_totals:
            db.add(
                CheckoutItem(
                    invoice_id=invoice.id,
                    product_id=product.id,
                    product_name=product.name,
                    quantity=qty,
                    price=product.out_price,
                    total=line_total,
                )
            )
            product.sold = int(product.sold or 0) + qty
            product.in_stock = max(0, int(product.in_stock or 0) - qty)

        record_history(
            db,
            current_user.id,
            "Create",
            f"Checkout completed (Invoice: {invoice.invoice_no})",
        )
        db.commit()
        db.refresh(invoice)
    except IntegrityError:
        db.rollback()
        logger.warning("Checkout integrity error for invoice %s", invoice_no)
        return error_response(
            status.HTTP_409_CONFLICT,
            "Checkout conflict — please retry",
            "CHECKOUT_CONFLICT",
        )
    except Exception:
        db.rollback()
        logger.exception("Checkout transaction failed")
        raise

    pdf_url = invoice_pdf_api_path(invoice_no)
    if settings.invoice_pdf_sync:
        try:
            ensure_invoice_pdf(db, invoice.id)
        except Exception as exc:
            logger.warning("Sync PDF generation failed for %s: %s", invoice_no, exc)

    celery_tasks = enqueue_checkout_followups(invoice.id)

    return {
        "data": {
            "orderId": invoice.id,
            "invoiceId": invoice.id,
            "invoiceNo": invoice_no,
            "invoiceNumber": invoice_no,
            "subtotal": subtotal,
            "discountAmount": discount_amount,
            "total": total,
            "pdfUrl": pdf_url,
            "pdfTaskId": celery_tasks.get("pdfTaskId"),
            "printTaskId": celery_tasks.get("printTaskId"),
            "notificationTaskId": celery_tasks.get("notificationTaskId"),
            "cacheTaskId": celery_tasks.get("cacheTaskId"),
            "invoice": {
                "invoiceNo": invoice_no,
                "customerName": invoice.customer_name,
                "customerPhone": invoice.customer_phone,
                "customerAddress": invoice.customer_address,
                "source": invoice.source,
                "deliveryType": invoice.delivery_type,
                "deliveryPrice": invoice.delivery_price,
                "deliveryDate": invoice.delivery_date,
            },
        }
    }


from app.services.data_service import serialize_report_row


def invoice_preview_by_no(*, db: Session, invoice_no: str):
    nos = [n.strip() for n in invoice_no.split(",") if n.strip()]
    if not nos:
        return error_response(status.HTTP_400_BAD_REQUEST, "Missing invoice number", "BAD_REQUEST")

    if len(nos) > 1:
        query = (
            select(CheckoutItem, Invoice, User)
            .join(Invoice, CheckoutItem.invoice_id == Invoice.id)
            .outerjoin(User, Invoice.user_id == User.id)
            .where(Invoice.invoice_no.in_(nos))
        )
        rows = db.execute(query).all()
        return {"invoices": [serialize_report_row(ci, inv, seller) for ci, inv, seller in rows]}

    invoice = db.execute(select(Invoice).where(Invoice.invoice_no == nos[0])).scalar_one_or_none()
    if not invoice:
        return error_response(status.HTTP_404_NOT_FOUND, "Invoice not found", "NOT_FOUND")
    items = db.execute(select(CheckoutItem).where(CheckoutItem.invoice_id == invoice.id)).scalars().all()
    user = db.get(User, invoice.user_id) if invoice.user_id else None
    return {
        "invoice": {
            "invoiceNo": invoice.invoice_no,
            "date": (invoice.created_at or cambodia_now()).isoformat(),
            "customer": invoice.customer_name or "",
            "phoneCustomer": invoice.customer_phone or "",
            "seller": user.name if user else "",
            "source": invoice.source or "",
            "address": invoice.customer_address or "",
            "subtotal": float(invoice.subtotal or 0),
            "discount": float(invoice.discount or 0),
            "deliveryPrice": float(invoice.delivery_price or 0),
            "amount": float(invoice.total or 0),
        },
        "lines": [
            {
                "productId": row.product_id,
                "product": row.product_name,
                "qty": int(row.quantity or 0),
                "price": float(row.price or 0),
                "total": float(row.total or 0),
            }
            for row in items
        ],
    }
