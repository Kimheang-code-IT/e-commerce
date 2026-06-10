from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.utils.timezone import cambodia_now

if TYPE_CHECKING:
    from app.models.product import Product


class Reward(Base):
    __tablename__ = "rewards"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(180), index=True)
    status: Mapped[str] = mapped_column(String(20), default="active", index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=cambodia_now)

    products: Mapped[list["RewardProduct"]] = relationship(
        back_populates="reward",
        cascade="all, delete-orphan",
    )


class RewardProduct(Base):
    __tablename__ = "reward_products"
    __table_args__ = (UniqueConstraint("reward_id", "product_id", name="uq_reward_product"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    reward_id: Mapped[int] = mapped_column(ForeignKey("rewards.id", ondelete="CASCADE"), index=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id", ondelete="CASCADE"), index=True)
    qty: Mapped[int] = mapped_column(Integer, default=1)

    reward: Mapped["Reward"] = relationship(back_populates="products")
    product: Mapped["Product"] = relationship()
