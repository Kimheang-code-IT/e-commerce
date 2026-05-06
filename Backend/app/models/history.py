from datetime import datetime
from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base
from app.utils.timezone import cambodia_now


class History(Base):
    __tablename__ = "histories"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    type_action: Mapped[str] = mapped_column(String(120), index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    description: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=cambodia_now)
