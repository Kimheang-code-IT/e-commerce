"""Enqueue post-checkout Celery jobs with stable task IDs (idempotent)."""

from __future__ import annotations

import logging

logger = logging.getLogger(__name__)


def _apply_task(task, *, task_id: str, args: tuple):
    """Submit task; reuse existing task_id if already queued (idempotent)."""
    try:
        return task.apply_async(args=args, task_id=task_id)
    except Exception as exc:
        # Celery raises if task_id already exists — treat as success.
        if "already exists" in str(exc).lower() or "Duplicate task" in str(exc):
            logger.info("Task %s already queued", task_id)
            return task_id
        raise


def enqueue_checkout_followups(invoice_id: int) -> dict[str, str | None]:
    from app.tasks import (
        check_low_stock_alert_task,
        generate_invoice_pdf_task,
        print_invoice_task,
        refresh_checkout_caches_task,
        send_checkout_notification_task,
    )

    pdf_task_id = f"checkout-pdf-{invoice_id}"
    print_task_id = f"checkout-print-{invoice_id}"
    notify_task_id = f"checkout-notify-{invoice_id}"
    cache_task_id = f"checkout-cache-{invoice_id}"

    try:
        _apply_task(generate_invoice_pdf_task, task_id=pdf_task_id, args=(invoice_id,))
        _apply_task(send_checkout_notification_task, task_id=notify_task_id, args=(invoice_id,))
        _apply_task(refresh_checkout_caches_task, task_id=cache_task_id, args=(invoice_id,))
        _apply_task(
            check_low_stock_alert_task,
            task_id=f"checkout-low-stock-{invoice_id}",
            args=(),
        )
        # Print runs after PDF when webhook printing is enabled.
        _apply_task(print_invoice_task, task_id=print_task_id, args=(invoice_id,))
        return {
            "pdfTaskId": pdf_task_id,
            "printTaskId": print_task_id,
            "notificationTaskId": notify_task_id,
            "cacheTaskId": cache_task_id,
            "lowStockTaskId": f"checkout-low-stock-{invoice_id}",
        }
    except Exception as exc:
        logger.warning("Celery enqueue failed for invoice %s: %s", invoice_id, exc)
        return {
            "pdfTaskId": None,
            "printTaskId": None,
            "notificationTaskId": None,
            "cacheTaskId": None,
        }
