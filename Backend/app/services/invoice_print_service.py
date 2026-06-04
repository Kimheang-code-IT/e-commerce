"""Optional server-side print via HTTP webhook (receipt printer bridge URL)."""

from __future__ import annotations

import logging

import httpx
from sqlalchemy.orm import Session

from app.core.config import settings
from app.services.invoice_pdf_service import generate_invoice_pdf, invoice_pdf_path

logger = logging.getLogger(__name__)


def print_invoice(db: Session, invoice_id: int, *, pdf_url: str | None = None) -> dict:
    if not settings.invoice_print_enabled:
        return {"status": "skipped", "reason": "print_disabled", "invoice_id": invoice_id}

    url = settings.invoice_print_webhook_url
    if not url:
        return {"status": "skipped", "reason": "no_webhook_url", "invoice_id": invoice_id}

    from app.models import Invoice

    invoice = db.get(Invoice, invoice_id)
    if not invoice:
        return {"status": "not_found", "invoice_id": invoice_id}

    if not pdf_url:
        path = invoice_pdf_path(invoice.invoice_no)
        if not path.is_file():
            pdf_meta = generate_invoice_pdf(db, invoice_id)
            pdf_url = pdf_meta.get("pdf_url")
        else:
            pdf_url = f"/{settings.invoice_pdf_dir.strip('/')}/{path.name}".replace("//", "/")

    base = (settings.file_base_url or "").rstrip("/")
    full_pdf_url = f"{base}{pdf_url}" if base else pdf_url

    payload = {
        "invoiceId": invoice.id,
        "invoiceNo": invoice.invoice_no,
        "pdfUrl": full_pdf_url,
        "total": float(invoice.total or 0),
    }
    try:
        with httpx.Client(timeout=15.0) as client:
            response = client.post(url, json=payload)
            response.raise_for_status()
        logger.info("Print webhook OK invoice_id=%s", invoice_id)
        return {"status": "ok", "invoice_id": invoice_id, "pdf_url": full_pdf_url}
    except Exception as exc:
        logger.exception("Print webhook failed invoice_id=%s: %s", invoice_id, exc)
        raise
