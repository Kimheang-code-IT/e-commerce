"""Generate invoice PDF files on disk (used by Celery after checkout)."""

from __future__ import annotations

import logging
from pathlib import Path

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models import CheckoutItem, Invoice, User

logger = logging.getLogger(__name__)


def _pdf_root() -> Path:
    root = Path(__file__).resolve().parent.parent.parent / settings.invoice_pdf_dir
    root.mkdir(parents=True, exist_ok=True)
    return root


def invoice_pdf_path(invoice_no: str) -> Path:
    safe = "".join(c if c.isalnum() or c in "-_" else "_" for c in invoice_no)
    return _pdf_root() / f"{safe}.pdf"


def invoice_pdf_api_path(invoice_no: str) -> str:
    """Authenticated download route (invoice PDFs are not public under /uploads)."""
    safe = "".join(c if c.isalnum() or c in "-_" else "_" for c in invoice_no)
    prefix = settings.api_prefix.rstrip("/")
    return f"{prefix}/pos/invoice/{safe}/pdf"


def invoice_pdf_public_url(invoice_no: str) -> str:
    """Backward-compatible alias — always use the protected API path."""
    return invoice_pdf_api_path(invoice_no)


def generate_invoice_pdf(db: Session, invoice_id: int) -> dict:
    invoice = db.get(Invoice, invoice_id)
    if not invoice:
        return {"status": "not_found", "invoice_id": invoice_id}

    path = invoice_pdf_path(invoice.invoice_no)
    if path.is_file() and path.stat().st_size > 0:
        return {
            "status": "ok",
            "invoice_id": invoice_id,
            "invoice_no": invoice.invoice_no,
            "pdf_path": str(path),
            "pdf_url": invoice_pdf_public_url(invoice.invoice_no),
            "cached": True,
        }

    items = db.execute(
        select(CheckoutItem).where(CheckoutItem.invoice_id == invoice.id)
    ).scalars().all()
    seller = db.get(User, invoice.user_id) if invoice.user_id else None

    c = canvas.Canvas(str(path), pagesize=A4)
    width, height = A4
    y = height - 20 * mm
    c.setFont("Helvetica-Bold", 14)
    c.drawString(20 * mm, y, f"Invoice {invoice.invoice_no}")
    y -= 8 * mm
    c.setFont("Helvetica", 10)
    c.drawString(20 * mm, y, f"Customer: {invoice.customer_name or 'N/A'}")
    y -= 6 * mm
    c.drawString(20 * mm, y, f"Phone: {invoice.customer_phone or 'N/A'}")
    y -= 6 * mm
    c.drawString(20 * mm, y, f"Seller: {seller.name if seller else 'N/A'}")
    y -= 6 * mm
    c.drawString(20 * mm, y, f"Payment: {invoice.payment_method or 'cash'}")
    y -= 10 * mm

    c.setFont("Helvetica-Bold", 10)
    c.drawString(20 * mm, y, "Product")
    c.drawString(100 * mm, y, "Qty")
    c.drawString(120 * mm, y, "Price")
    c.drawString(150 * mm, y, "Total")
    y -= 6 * mm
    c.setFont("Helvetica", 10)

    name_counts: dict[str, int] = {}
    for row in items:
        key = (row.product_name or "").strip()
        name_counts[key] = name_counts.get(key, 0) + 1
    name_ref: dict[str, int] = {}

    for row in items:
        if y < 30 * mm:
            c.showPage()
            y = height - 20 * mm
            c.setFont("Helvetica", 10)
        base_name = (row.product_name or "").strip()
        name = base_name[:36]
        if name_counts.get(base_name, 0) > 1:
            idx = name_ref.get(base_name, 0) + 1
            name_ref[base_name] = idx
            letter = chr(64 + idx) if idx <= 26 else str(idx)
            name = f"{name[:32]} ({letter})"
        qty = int(row.quantity or 0)
        price = float(row.price or 0)
        line_total = float(row.total or 0)
        c.drawString(20 * mm, y, name)
        c.drawRightString(110 * mm, y, str(qty))
        c.drawRightString(140 * mm, y, f"${price:.2f}")
        c.drawRightString(180 * mm, y, f"${line_total:.2f}")
        y -= 6 * mm

    delivery = float(invoice.delivery_price or 0)
    discount = float(invoice.discount or 0)
    subtotal = float(invoice.subtotal or 0)
    grand = max(0.0, subtotal - discount + delivery)

    y -= 4 * mm
    c.drawRightString(180 * mm, y, f"Subtotal: ${subtotal:.2f}")
    y -= 6 * mm
    c.drawRightString(180 * mm, y, f"Delivery: ${delivery:.2f}")
    y -= 6 * mm
    c.drawRightString(180 * mm, y, f"Discount: ${discount:.2f}")
    y -= 6 * mm
    c.setFont("Helvetica-Bold", 11)
    c.drawRightString(180 * mm, y, f"Total: ${grand:.2f}")
    c.save()

    rel = invoice_pdf_public_url(invoice.invoice_no)
    logger.info("Generated invoice PDF invoice_id=%s path=%s", invoice_id, path)
    return {
        "status": "ok",
        "invoice_id": invoice_id,
        "invoice_no": invoice.invoice_no,
        "pdf_path": str(path),
        "pdf_url": rel,
    }


def ensure_invoice_pdf(db: Session, invoice_id: int) -> dict:
    """Create PDF on disk if missing (safe to call from API after checkout)."""
    return generate_invoice_pdf(db, invoice_id)


def resolve_invoice_pdf_file(db: Session, invoice_no: str) -> tuple[Path, Invoice] | None:
    invoice = db.execute(
        select(Invoice).where(Invoice.invoice_no == invoice_no)
    ).scalar_one_or_none()
    if not invoice:
        return None
    meta = ensure_invoice_pdf(db, invoice.id)
    if meta.get("status") != "ok":
        return None
    path = Path(meta["pdf_path"])
    if not path.is_file():
        return None
    return path, invoice
