"""Post-checkout and scheduled Celery tasks."""

from __future__ import annotations

import asyncio
import logging

from sqlalchemy import select

from app.core.celery_app import celery_app
from app.core.config import settings
from app.core.database import SessionLocal
from app.models import CheckoutItem, Invoice
from app.services.backup_service import backup_service
from app.services.cache_service import invalidate_after_checkout
from app.services.invoice_pdf_service import generate_invoice_pdf
from app.services.invoice_print_service import print_invoice
from app.services.report_service import report_service
from app.services.telegram_service import telegram_service
from app.tasks.base import IdempotentTask, run_once_per_invoice

logger = logging.getLogger(__name__)


@celery_app.task(
    name="app.tasks.generate_invoice_pdf_task",
    base=IdempotentTask,
    bind=True,
)
def generate_invoice_pdf_task(self, invoice_id: int) -> dict:
    def _run() -> dict:
        db = SessionLocal()
        try:
            return generate_invoice_pdf(db, invoice_id)
        finally:
            db.close()

    return run_once_per_invoice(self.name, invoice_id, _run)


@celery_app.task(
    name="app.tasks.print_invoice_task",
    base=IdempotentTask,
    bind=True,
)
def print_invoice_task(self, invoice_id: int) -> dict:
    def _run() -> dict:
        db = SessionLocal()
        try:
            pdf_result = generate_invoice_pdf(db, invoice_id)
            return print_invoice(db, invoice_id, pdf_url=pdf_result.get("pdf_url"))
        finally:
            db.close()

    return run_once_per_invoice(self.name, invoice_id, _run)


@celery_app.task(
    name="app.tasks.send_checkout_notification_task",
    base=IdempotentTask,
    bind=True,
)
def send_checkout_notification_task(self, invoice_id: int) -> dict:
    def _run() -> dict:
        if not settings.telegram_notify_enabled or not settings.telegram_chat_id:
            return {"status": "skipped", "reason": "telegram_disabled", "invoice_id": invoice_id}

        db = SessionLocal()
        try:
            invoice = db.scalar(select(Invoice).where(Invoice.id == invoice_id))
            if not invoice:
                return {"status": "not_found", "invoice_id": invoice_id}
            items = db.execute(
                select(CheckoutItem).where(CheckoutItem.invoice_id == invoice.id)
            ).scalars().all()
            asyncio.run(telegram_service.notify_checkout(invoice, items))
            return {"status": "ok", "invoice_id": invoice_id}
        finally:
            db.close()

    return run_once_per_invoice(self.name, invoice_id, _run)


@celery_app.task(
    name="app.tasks.refresh_checkout_caches_task",
    base=IdempotentTask,
    bind=True,
)
def refresh_checkout_caches_task(self, invoice_id: int) -> dict:
    def _run() -> dict:
        deleted = invalidate_after_checkout()
        if settings.google_backup_enabled and settings.google_sheet_id:
            db = SessionLocal()
            try:
                backup_service.backup_all(db)
            finally:
                db.close()
        return {"status": "ok", "invoice_id": invoice_id, "cache_keys_deleted": deleted}

    return run_once_per_invoice(self.name, invoice_id, _run)


@celery_app.task(name="app.tasks.process_checkout_background", base=IdempotentTask, bind=True)
def process_checkout_background(self, invoice_id: int) -> dict:
    """Legacy orchestrator — runs notify + cache (+ optional backup). Prefer split tasks."""
    notify = send_checkout_notification_task.apply_async(
        args=(invoice_id,),
        task_id=f"checkout-notify-{invoice_id}",
    )
    cache = refresh_checkout_caches_task.apply_async(
        args=(invoice_id,),
        task_id=f"checkout-cache-{invoice_id}",
    )
    return {
        "status": "ok",
        "invoice_id": invoice_id,
        "notification_task": notify.id,
        "cache_task": cache.id,
    }


@celery_app.task(name="app.tasks.send_daily_product_report", base=IdempotentTask)
def send_daily_product_report() -> dict:
    if not settings.telegram_report_enabled or not settings.telegram_chat_id:
        return {"status": "skipped", "reason": "telegram disabled"}

    db = SessionLocal()
    try:
        messages = report_service.format_product_report_messages(db)
        for msg in messages:
            asyncio.run(telegram_service.send_message(settings.telegram_chat_id, msg))
        return {"status": "ok", "messages": len(messages)}
    except Exception as exc:
        logger.exception("Daily product report task failed: %s", exc)
        return {"status": "error", "error": str(exc)}
    finally:
        db.close()
