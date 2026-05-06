import base64
import json

from fastapi import status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import CheckoutItem, Invoice, User
from app.repositories.pos_repository import get_products_by_ids, next_invoice_no
from app.schemas.common import PosCheckoutPayload, PosPreviewSessionCreatePayload
from app.shared.api_response import error_response
from app.utils.timezone import cambodia_now


def encode_preview(payload: PosPreviewSessionCreatePayload) -> dict:
    raw = json.dumps(payload.invoices, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    preview_key = base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=")
    return {"previewKey": preview_key}


def decode_preview(preview_key: str):
    pad = "=" * (-len(preview_key) % 4)
    raw = base64.urlsafe_b64decode(preview_key + pad)
    parsed = json.loads(raw.decode("utf-8"))
    return parsed if isinstance(parsed, list) else []


def calculate_totals_service(*, db: Session, payload: PosCheckoutPayload):
    product_ids = [line.productId for line in payload.lines]
    product_map = {row.id: row for row in get_products_by_ids(db, product_ids)}
    subtotal = 0.0
    for line in payload.lines:
        product = product_map.get(line.productId)
        if product:
            if int(product.in_stock or 0) < line.qty:
                return error_response(
                    status.HTTP_400_BAD_REQUEST,
                    f"Not enough stock for {product.name} (Available: {product.in_stock})",
                    "NOT_ENOUGH_STOCK",
                )
            subtotal += float(product.out_price) * line.qty
    discount_amount = subtotal * (float(payload.discountPercent) / 100)
    return {"subtotal": subtotal, "discountAmount": discount_amount, "total": subtotal - discount_amount}


def complete_checkout_service(*, db: Session, payload: PosCheckoutPayload, current_user):
    invoice_no = next_invoice_no(db)
    if not str(invoice_no).startswith("DNS-"):
        raise RuntimeError("Invoice numbering must use DNS-* format")
    product_ids = [line.productId for line in payload.lines]
    product_map = {row.id: row for row in get_products_by_ids(db, product_ids)}
    subtotal = 0.0
    line_totals: list[tuple[object, int, float]] = []

    for line in payload.lines:
        product = product_map.get(line.productId)
        if not product:
            continue
        if int(product.in_stock or 0) < line.qty:
            return error_response(
                status.HTTP_400_BAD_REQUEST,
                f"Not enough stock for {product.name} (Available: {product.in_stock})",
                "NOT_ENOUGH_STOCK",
            )
        line_total = float(product.out_price) * line.qty
        subtotal += line_total
        line_totals.append((product, line.qty, line_total))

    discount_amount = subtotal * (float(payload.discountPercent) / 100)
    total = max(0.0, subtotal - discount_amount)
    summary_names = ", ".join([item[0].name for item in line_totals])
    if len(summary_names) > 177:
        summary_names = summary_names[:177] + "..."

    invoice = Invoice(
        invoice_no=invoice_no,
        user_id=payload.sellerId if payload.sellerId is not None else current_user.id,
        customer_name=payload.customerName,
        customer_phone=payload.customerPhone,
        customer_address=payload.customerAddress,
        product_name=summary_names,
        delivery_type=payload.deliveryType,
        delivery_price=float(payload.deliveryPrice or 0),
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

    db.commit()
    return {
        "data": {
            "invoiceNo": invoice_no,
            "subtotal": subtotal,
            "discountAmount": discount_amount,
            "total": total,
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


def invoice_preview_by_no(*, db: Session, invoice_no: str):
    invoice = db.execute(select(Invoice).where(Invoice.invoice_no == invoice_no)).scalar_one_or_none()
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
