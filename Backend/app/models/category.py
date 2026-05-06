from datetime import datetime
from typing import TYPE_CHECKING
from sqlalchemy import DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base
from app.utils.timezone import cambodia_now

if TYPE_CHECKING:
    from app.models.product import Product


class Category(Base):
    __tablename__ = "categories"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(120), index=True)
    description: Mapped[str] = mapped_column(Text, default="")
    product_count: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=cambodia_now)
    products: Mapped[list["Product"]] = relationship(back_populates="category_rel")

    @property
    def public_id(self) -> str:
        return self.to_public_id(self.id)

    @staticmethod
    def to_public_id(raw_id: int) -> str:
        return f"Cat_{raw_id:05d}"

    @staticmethod
    def from_public_id(value: str) -> int | None:
        if not value:
            return None
        normalized = value.strip()
        if not normalized:
            return None
        if normalized.isdigit():
            return int(normalized)
        parts = normalized.split("_", 1)
        if len(parts) == 2 and parts[0].lower() == "cat" and parts[1].isdigit():
            return int(parts[1])
        return None
