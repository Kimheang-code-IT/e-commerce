from celery import Celery

from app.core.config import settings


def _get_broker_url() -> str:
    return settings.celery_broker_url or settings.redis_url


def _get_result_backend() -> str:
    return settings.celery_result_backend or settings.redis_url


celery_app = Celery(
    "e_comerce_backend",
    broker=_get_broker_url(),
    backend=_get_result_backend(),
    include=[
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
    beat_schedule={
        "daily-product-report": {
            "task": "app.tasks.send_daily_product_report",
            "schedule": 60.0 * 60.0 * 24.0,
        }
    },
)
