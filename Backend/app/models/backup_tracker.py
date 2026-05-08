from datetime import datetime
from sqlalchemy import DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base
from app.utils.timezone import cambodia_now

class BackupTracker(Base):
    __tablename__ = "backup_tracker"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    backup_name: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    last_backup_id: Mapped[int] = mapped_column(Integer, default=0)
    last_run_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    status: Mapped[str | None] = mapped_column(String(50), nullable=True)
    error_message: Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=cambodia_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=cambodia_now, onupdate=cambodia_now)
