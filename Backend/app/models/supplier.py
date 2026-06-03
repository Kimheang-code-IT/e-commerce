from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.utils.timezone import cambodia_now

if TYPE_CHECKING:
    from app.models.user import User


class Supplier(Base):
    __tablename__ = "suppliers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(160), index=True)
    gender: Mapped[str] = mapped_column(String(20), default="Other")
    address: Mapped[str] = mapped_column(Text, default="")
    phone_number: Mapped[str] = mapped_column(String(40), default="", index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=cambodia_now)

    products: Mapped[list["SupplierProduct"]] = relationship(
        "SupplierProduct",
        back_populates="supplier_rel",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


class SupplierProduct(Base):
    __tablename__ = "supplier_products"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    supplier_id: Mapped[int] = mapped_column(
        ForeignKey("suppliers.id", ondelete="CASCADE"),
        index=True,
    )
    product_name: Mapped[str] = mapped_column(String(180), index=True)
    qty: Mapped[int] = mapped_column(Integer, default=0)
    unit_price: Mapped[float] = mapped_column(Float, default=0)
    amount: Mapped[float] = mapped_column(Float, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=cambodia_now)
    updated_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)

    supplier_rel: Mapped[Supplier] = relationship("Supplier", back_populates="products")
    updated_by_user: Mapped[User | None] = relationship("User")
