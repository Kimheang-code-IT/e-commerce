"""Shared Celery task utilities: idempotency, retries, logging."""

from __future__ import annotations

import logging
from collections.abc import Callable

from celery import Task

from app.core.config import settings
from app.core.redis_client import get_redis

logger = logging.getLogger(__name__)

IDEMPOTENCY_TTL_SECONDS = 86400
IN_PROGRESS_TTL_SECONDS = 600


class IdempotentTask(Task):
    """Base task with autoretry and Redis execution idempotency."""

    autoretry_for = (Exception,)
    retry_backoff = True
    retry_jitter = True
    max_retries = settings.CELERY_TASK_MAX_RETRIES
    default_retry_delay = settings.CELERY_TASK_DEFAULT_RETRY_DELAY
    soft_time_limit = settings.CELERY_TASK_SOFT_TIME_LIMIT
    time_limit = settings.CELERY_TASK_TIME_LIMIT

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        logger.error(
            "Task %s[%s] failed: %s",
            self.name,
            task_id,
            exc,
            exc_info=einfo,
        )
        super().on_failure(exc, task_id, args, kwargs, einfo)


def idempotency_key(task_name: str, invoice_id: int) -> str:
    return f"celery:done:{task_name}:{invoice_id}"


def idempotency_lock_key(task_name: str, invoice_id: int) -> str:
    return f"celery:lock:{task_name}:{invoice_id}"


def _clear_idempotency_lock(task_name: str, invoice_id: int) -> None:
    try:
        get_redis().delete(idempotency_lock_key(task_name, invoice_id))
    except Exception:
        pass


def run_once_per_invoice(task_name: str, invoice_id: int, runner: Callable[[], dict]) -> dict:
    """
    Run at most one successful execution per invoice+task per TTL.
    Failed runs clear the in-progress lock so Celery autoretry can rerun.
    """
    done_key = idempotency_key(task_name, invoice_id)
    lock_key = idempotency_lock_key(task_name, invoice_id)
    try:
        client = get_redis()
        if client.get(done_key):
            logger.info("Skipping duplicate %s for invoice %s", task_name, invoice_id)
            return {"status": "skipped", "reason": "duplicate", "invoice_id": invoice_id}
        if not client.set(lock_key, "1", nx=True, ex=IN_PROGRESS_TTL_SECONDS):
            logger.info("Task %s already in progress for invoice %s", task_name, invoice_id)
            return {"status": "skipped", "reason": "in_progress", "invoice_id": invoice_id}
    except Exception as exc:
        logger.warning("Idempotency unavailable for %s: %s", task_name, exc)

    try:
        result = runner()
        if result.get("status") not in ("error", "not_found"):
            try:
                get_redis().set(done_key, "1", ex=IDEMPOTENCY_TTL_SECONDS)
            except Exception:
                pass
        return result
    except Exception:
        _clear_idempotency_lock(task_name, invoice_id)
        raise
    finally:
        _clear_idempotency_lock(task_name, invoice_id)
