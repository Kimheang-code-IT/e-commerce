"""Add FIFO columns to product_stock_additions and backfill qty_remaining."""

from __future__ import annotations

import logging

from sqlalchemy import inspect, select, text
from sqlalchemy.orm import Session

from app.core.database import engine, SessionLocal
from app.models import Product, ProductStockAddition

logger = logging.getLogger(__name__)


def ensure_stock_lot_schema() -> None:
    insp = inspect(engine)
    table_names = set(insp.get_table_names())
    if "product_stock_additions" not in table_names:
        _ensure_refund_record_schema(insp, table_names)
        return

    existing = {c["name"] for c in insp.get_columns("product_stock_additions")}
    alters: list[str] = []
    if "in_price" not in existing:
        alters.append("ADD COLUMN in_price DOUBLE PRECISION NOT NULL DEFAULT 0")
    if "out_price" not in existing:
        alters.append("ADD COLUMN out_price DOUBLE PRECISION NOT NULL DEFAULT 0")
    if "qty_remaining" not in existing:
        alters.append("ADD COLUMN qty_remaining INTEGER")

    if not alters:
        _ensure_refund_record_schema(insp, table_names)
        return

    with engine.begin() as conn:
        for clause in alters:
            conn.execute(text(f"ALTER TABLE product_stock_additions {clause}"))
        conn.execute(
            text(
                "UPDATE product_stock_additions SET qty_remaining = qty "
                "WHERE qty_remaining IS NULL"
            )
        )

    db = SessionLocal()
    try:
        _backfill_lot_remaining(db)
        db.commit()
    finally:
        db.close()
    logger.info("Stock FIFO columns ready on product_stock_additions")
    _ensure_refund_record_schema(insp, table_names)


def _ensure_refund_record_schema(insp, table_names: set[str]) -> None:
    if "refund_records" not in table_names:
        return

    existing = {c["name"] for c in insp.get_columns("refund_records")}
    alters: list[str] = []
    if "checkout_item_id" not in existing:
        alters.append("ADD COLUMN checkout_item_id INTEGER")
    if "product_id" not in existing:
        alters.append("ADD COLUMN product_id INTEGER")
    if "qty" not in existing:
        alters.append("ADD COLUMN qty INTEGER NOT NULL DEFAULT 0")

    if not alters:
        return

    with engine.begin() as conn:
        for clause in alters:
            conn.execute(text(f"ALTER TABLE refund_records {clause}"))
    logger.info("Refund return columns ready on refund_records")


def _backfill_lot_remaining(db: Session) -> None:
    """Spread each product's in_stock across lots oldest-first."""
    products = db.execute(select(Product)).scalars().all()
    for product in products:
        lots = (
            db.execute(
                select(ProductStockAddition)
                .where(ProductStockAddition.product_id == product.id)
                .order_by(ProductStockAddition.created_at.asc(), ProductStockAddition.id.asc())
            )
            .scalars()
            .all()
        )
        if not lots:
            continue

        remaining = int(product.in_stock or 0)
        for lot in lots:
            if remaining <= 0:
                lot.qty_remaining = 0
                if not float(lot.in_price or 0) and not float(lot.out_price or 0):
                    lot.in_price = float(product.in_price or 0)
                    lot.out_price = float(product.out_price or 0)
                continue
            cap = int(lot.qty or 0)
            take = min(cap, remaining) if cap > 0 else remaining
            lot.qty_remaining = take
            remaining -= take
            if not float(lot.in_price or 0) and not float(lot.out_price or 0):
                lot.in_price = float(product.in_price or 0)
                lot.out_price = float(product.out_price or 0)

        if remaining > 0:
            db.add(
                ProductStockAddition(
                    product_id=product.id,
                    product_name=product.name,
                    qty=remaining,
                    qty_remaining=remaining,
                    in_price=float(product.in_price or 0),
                    out_price=float(product.out_price or 0),
                    note="fifo-backfill",
                )
            )
