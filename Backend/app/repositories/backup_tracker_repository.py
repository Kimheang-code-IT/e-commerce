from datetime import datetime
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.models.backup_tracker import BackupTracker
from app.utils.timezone import cambodia_now

class BackupTrackerRepository:
    def get_by_name(self, db: Session, backup_name: str) -> BackupTracker | None:
        return db.scalar(select(BackupTracker).where(BackupTracker.backup_name == backup_name))

    def update_status(self, db: Session, backup_name: str, last_backup_id: int, status: str, error_message: str | None = None):
        tracker = self.get_by_name(db, backup_name)
        if not tracker:
            tracker = BackupTracker(backup_name=backup_name)
            db.add(tracker)
        
        tracker.last_backup_id = last_backup_id
        tracker.status = status
        tracker.error_message = error_message
        tracker.last_run_at = cambodia_now()
        
        db.commit()
        db.refresh(tracker)
        return tracker

backup_tracker_repo = BackupTrackerRepository()
