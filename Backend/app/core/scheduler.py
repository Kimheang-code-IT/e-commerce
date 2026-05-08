import logging
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from app.core.config import settings
from app.core.database import SessionLocal
from app.services.backup_service import backup_service

logger = logging.getLogger(__name__)

scheduler = BackgroundScheduler()

def scheduled_google_sheet_backup():
    logger.info("Starting scheduled full Google Sheets backup...")
    db = SessionLocal()
    try:
        results = backup_service.backup_all(db)
        logger.info(f"Scheduled full backup finished. Results: {results}")
    except Exception as e:
        logger.error(f"Scheduled full backup failed: {e}")
    finally:
        db.close()

def start_scheduler():
    if not settings.google_backup_enabled:
        logger.info("Google Sheets backup scheduler is disabled.")
        return

    try:
        hour, minute = map(int, settings.google_backup_time.split(':'))
        
        scheduler.add_job(
            scheduled_google_sheet_backup,
            CronTrigger(hour=hour, minute=minute),
            id="google_sheet_backup",
            replace_existing=True
        )
        scheduler.start()
        logger.info(f"Scheduler started. Google Sheets backup scheduled daily at {settings.google_backup_time}")
    except Exception as e:
        logger.error(f"Failed to start scheduler: {e}")

def shutdown_scheduler():
    if scheduler.running:
        scheduler.shutdown()
        logger.info("Scheduler shut down.")
