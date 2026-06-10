import logging
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from app.core.config import settings
from app.core.database import SessionLocal
from app.core.scheduler_lock import try_acquire_scheduler_lock
from app.services.alert_service import run_google_backup_with_notify, run_low_stock_alert

logger = logging.getLogger(__name__)

scheduler = BackgroundScheduler(timezone=settings.scheduler_timezone)


def scheduled_google_sheet_backup():
    if not try_acquire_scheduler_lock("google_sheet_backup", ttl_seconds=7200):
        logger.info("Google backup skipped — another replica holds the lock.")
        return
    logger.info("Starting scheduled full Google Sheets backup...")
    db = SessionLocal()
    try:
        outcome = run_google_backup_with_notify(db)
        logger.info("Scheduled backup finished: %s", outcome.get("status"))
    finally:
        db.close()


def scheduled_low_stock_check():
    if not try_acquire_scheduler_lock("low_stock_alert", ttl_seconds=1800):
        return
    db = SessionLocal()
    try:
        outcome = run_low_stock_alert(db)
        logger.info("Low stock check: %s", outcome)
    finally:
        db.close()

def start_scheduler():
    if not settings.scheduler_enabled:
        logger.info("Scheduler is disabled by configuration.")
        return

    try:
        if settings.google_backup_enabled:
            hour, minute = map(int, settings.google_backup_time.split(":"))
            scheduler.add_job(
                scheduled_google_sheet_backup,
                CronTrigger(hour=hour, minute=minute),
                id="google_sheet_backup",
                replace_existing=True,
            )
        if settings.LOW_STOCK_ALERT_ENABLED:
            scheduler.add_job(
                scheduled_low_stock_check,
                CronTrigger(minute=0, hour="*/2"),
                id="low_stock_alert",
                replace_existing=True,
            )
        if not scheduler.get_jobs():
            logger.info("No scheduler jobs enabled.")
            return
        scheduler.start()
        logger.info(
            "Scheduler started (%s). Backup=%s at %s; low-stock=%s",
            settings.scheduler_timezone,
            settings.google_backup_enabled,
            settings.google_backup_time,
            settings.LOW_STOCK_ALERT_ENABLED,
        )
    except Exception as e:
        logger.error(f"Failed to start scheduler: {e}")

def shutdown_scheduler():
    if scheduler.running:
        scheduler.shutdown()
        logger.info("Scheduler shut down.")
