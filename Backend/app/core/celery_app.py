from celery import Celery
from celery.schedules import crontab

from app.core.config import settings


def _get_broker_url() -> str:
    return settings.celery_broker_url or settings.redis_url


def _get_result_backend() -> str:
    return settings.celery_result_backend or settings.redis_url


def _parse_time_hhmm(value: str, *, default_hour: int, default_minute: int) -> tuple[int, int]:
    try:
        hour, minute = map(int, (value or "").split(":"))
        if not (0 <= hour <= 23 and 0 <= minute <= 59):
            raise ValueError("Hour/minute out of cron range")
        return hour, minute
    except (TypeError, ValueError):
        return default_hour, default_minute


def _parse_backup_cron() -> tuple[int, int]:
    return _parse_time_hhmm(settings.google_backup_time or "19:00", default_hour=19, default_minute=0)


def _build_beat_schedule() -> dict:
    backup_hour, backup_minute = _parse_backup_cron()
    sales_hour, sales_minute = _parse_time_hhmm(
        settings.DAILY_SALES_SUMMARY_TIME,
        default_hour=19,
        default_minute=5,
    )
    schedule: dict = {
        "daily-sales-summary-telegram": {
            "task": "app.tasks.send_daily_sales_summary_task",
            "schedule": crontab(hour=sales_hour, minute=sales_minute),
        },
        "daily-product-report": {
            "task": "app.tasks.send_daily_product_report",
            "schedule": crontab(hour=8, minute=0),
        },
    }
    if settings.LOW_STOCK_ALERT_ENABLED:
        schedule["low-stock-alert"] = {
            "task": "app.tasks.check_low_stock_alert_task",
            "schedule": crontab(minute=0, hour="*/2"),
        }
    if settings.google_backup_enabled:
        schedule["daily-google-backup"] = {
            "task": "app.tasks.scheduled_google_backup_task",
            "schedule": crontab(hour=backup_hour, minute=backup_minute),
        }
    return schedule


celery_app = Celery(
    "e_comerce_backend",
    broker=_get_broker_url(),
    backend=_get_result_backend(),
    include=[
        "app.tasks",
        "app.tasks.checkout_tasks",
    ],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone=settings.scheduler_timezone,
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    task_soft_time_limit=settings.CELERY_TASK_SOFT_TIME_LIMIT,
    task_time_limit=settings.CELERY_TASK_TIME_LIMIT,
    beat_schedule=_build_beat_schedule(),
)
