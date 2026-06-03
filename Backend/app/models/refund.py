from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.utils.timezone import cambodia_now

if TYPE_CHECKING:
    from app.models.user import User


class RefundRecord(Base):
    __tablename__ = "refund_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    invoice_no: Mapped[str] = mapped_column(String(120), index=True)
    sale_date: Mapped[str] = mapped_column(String(50), default="")
    customer: Mapped[str] = mapped_column(String(160), default="")
    product: Mapped[str] = mapped_column(String(180), default="")
    seller: Mapped[str] = mapped_column(String(120), default="")
    source: Mapped[str] = mapped_column(String(50), default="")
    address: Mapped[str] = mapped_column(Text, default="")
    amount: Mapped[float] = mapped_column(Float, default=0)
    checkout_item_id: Mapped[int | None] = mapped_column(ForeignKey("checkout_items.id"), nullable=True, index=True)
    product_id: Mapped[int | None] = mapped_column(ForeignKey("products.id"), nullable=True, index=True)
    qty: Mapped[int] = mapped_column(Integer, default=0)
    refund_reason: Mapped[str] = mapped_column(Text, default="")
    refunded_at: Mapped[datetime] = mapped_column(DateTime, default=cambodia_now)
    created_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)

    created_by_user: Mapped[User | None] = relationship("User")
