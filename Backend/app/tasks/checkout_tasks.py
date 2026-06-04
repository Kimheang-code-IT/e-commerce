"""Post-checkout and scheduled Celery tasks."""

from __future__ import annotations

import asyncio
import logging

from sqlalchemy import select

from app.core.celery_app import celery_app
from app.core.config import settings
from app.core.database import SessionLocal
from app.models import CheckoutItem, Invoice
from app.services.alert_service import run_google_backup_with_notify, run_low_stock_alert
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
    name="app.tasks.send_refund_notification_task",
    base=IdempotentTask,
    bind=True,
)
def send_refund_notification_task(self, payload: dict) -> dict:
    if not settings.telegram_notify_enabled or not settings.telegram_chat_id:
        return {"status": "skipped", "reason": "telegram_disabled"}

    try:
        asyncio.run(
            telegram_service.notify_refund(
                invoice_no=str(payload.get("invoiceNo") or ""),
                customer=str(payload.get("customer") or ""),
                phone=str(payload.get("phone") or ""),
                source=str(payload.get("source") or ""),
                seller=str(payload.get("seller") or ""),
                reason=str(payload.get("reason") or ""),
                refunded_by=str(payload.get("refundedBy") or ""),
                lines=list(payload.get("lines") or []),
            )
        )
        return {"status": "ok", "invoice_no": payload.get("invoiceNo")}
    except Exception as exc:
        logger.exception("Refund Telegram notification failed: %s", exc)
        return {"status": "error", "error": str(exc)}


@celery_app.task(
    name="app.tasks.refresh_checkout_caches_task",
    base=IdempotentTask,
    bind=True,
)
def refresh_checkout_caches_task(self, invoice_id: int) -> dict:
    def _run() -> dict:
        deleted = invalidate_after_checkout()
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


@celery_app.task(name="app.tasks.check_low_stock_alert_task", base=IdempotentTask)
def check_low_stock_alert_task() -> dict:
    from app.core.scheduler_lock import try_acquire_scheduler_lock

    if not try_acquire_scheduler_lock("low_stock_alert", ttl_seconds=900):
        return {"status": "skipped", "reason": "lock_held"}
    db = SessionLocal()
    try:
        return run_low_stock_alert(db)
    except Exception as exc:
        logger.exception("Low stock alert failed: %s", exc)
        return {"status": "error", "error": str(exc)}
    finally:
        db.close()


@celery_app.task(name="app.tasks.scheduled_google_backup_task", base=IdempotentTask)
def scheduled_google_backup_task() -> dict:
    from app.core.scheduler_lock import try_acquire_scheduler_lock

    if not try_acquire_scheduler_lock("google_sheet_backup", ttl_seconds=7200):
        return {"status": "skipped", "reason": "lock_held"}
    db = SessionLocal()
    try:
        return run_google_backup_with_notify(db)
    except Exception as exc:
        logger.exception("Scheduled backup task failed: %s", exc)
        return {"status": "error", "error": str(exc)}
    finally:
        db.close()


@celery_app.task(name="app.tasks.send_daily_sales_summary_task", base=IdempotentTask)
def send_daily_sales_summary_task() -> dict:
    from app.core.scheduler_lock import try_acquire_scheduler_lock
    from app.utils.timezone import cambodia_today_sales_window, format_cambodia_report_date_label

    if not settings.telegram_daily_sales_summary_enabled:
        return {"status": "skipped", "reason": "telegram_daily_sales_disabled"}

    if not try_acquire_scheduler_lock("daily_sales_summary", ttl_seconds=3600):
        return {"status": "skipped", "reason": "lock_held"}

    def _parse_hhmm(value: str, default_h: int, default_m: int) -> tuple[int, int]:
        try:
            h, m = map(int, (value or "").split(":"))
            return h, m
        except (TypeError, ValueError):
            return default_h, default_m

    sh, sm = _parse_hhmm(settings.DAILY_SALES_WINDOW_START, 7, 0)
    eh, em = _parse_hhmm(settings.DAILY_SALES_WINDOW_END, 19, 0)
    start, end, now = cambodia_today_sales_window(
        start_hour=sh, start_minute=sm, end_hour=eh, end_minute=em
    )
    date_label = format_cambodia_report_date_label(now)

    def _ampm(hour: int, minute: int) -> str:
        h12 = hour % 12 or 12
        suffix = "AM" if hour < 12 else "PM"
        return f"{h12}:{minute:02d}{suffix}"

    time_label = f"{_ampm(sh, sm)}-{_ampm(eh, em)}"

    db = SessionLocal()
    try:
        msg = report_service.format_daily_sales_summary(
            db, start, end, date_label=date_label, time_label=time_label
        )
        asyncio.run(telegram_service.send_message(settings.telegram_chat_id, msg))
        return {"status": "ok", "window_start": start.isoformat(), "window_end": end.isoformat()}
    except Exception as exc:
        logger.exception("Daily sales summary task failed: %s", exc)
        return {"status": "error", "error": str(exc)}
    finally:
        db.close()


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
