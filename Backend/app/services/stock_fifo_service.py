"""FIFO stock lots: oldest batch sells first (queue by created_at)."""

from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import Product, ProductStockAddition


@dataclass(frozen=True)
class FifoSlice:
    qty: int
    in_price: float
    out_price: float
    lot_id: int | None = None


def create_stock_lot(
    db: Session,
    *,
    product: Product,
    qty: int,
    in_price: float,
    out_price: float,
    note: str,
) -> ProductStockAddition:
    qty_i = int(qty)
    lot = ProductStockAddition(
        product_id=product.id,
        product_name=product.name,
        qty=qty_i,
        qty_remaining=qty_i,
        in_price=float(in_price or 0),
        out_price=float(out_price or 0),
        note=note or "adjust",
    )
    db.add(lot)
    db.flush()
    return lot


def _open_lots_query(product_id: int, *, for_update: bool):
    q = (
        select(ProductStockAddition)
        .where(
            ProductStockAddition.product_id == product_id,
            ProductStockAddition.qty_remaining > 0,
        )
        .order_by(ProductStockAddition.created_at.asc(), ProductStockAddition.id.asc())
    )
    if for_update:
        q = q.with_for_update()
    return q


def _ensure_fifo_lot_coverage(db: Session, product_id: int) -> None:
    """
    Self-heal legacy/inconsistent data:
    if product.in_stock is greater than open FIFO qty_remaining, create a recovery lot.
    """
    product = db.get(Product, product_id)
    if not product:
        return
    in_stock = max(0, int(product.in_stock or 0))
    if in_stock <= 0:
        return

    open_qty = (
        db.execute(
            select(func.coalesce(func.sum(ProductStockAddition.qty_remaining), 0)).where(
                ProductStockAddition.product_id == product_id,
                ProductStockAddition.qty_remaining > 0,
            )
        ).scalar_one()
        or 0
    )
    open_qty_i = max(0, int(open_qty))
    if open_qty_i >= in_stock:
        return

    recover_qty = in_stock - open_qty_i
    create_stock_lot(
        db,
        product=product,
        qty=recover_qty,
        in_price=float(product.in_price or 0),
        out_price=float(product.out_price or 0),
        note="fifo-recovery",
    )


def allocate_fifo(
    db: Session,
    product_id: int,
    qty_needed: int,
    *,
    consume: bool,
) -> list[FifoSlice]:
    """Allocate qty from oldest lots first. Set consume=True to decrement qty_remaining."""
    need = int(qty_needed)
    if need <= 0:
        return []

    # Ensure old/migrated data can still sell according to product.in_stock.
    _ensure_fifo_lot_coverage(db, product_id)

    lots = db.execute(_open_lots_query(product_id, for_update=consume)).scalars().all()
    slices: list[FifoSlice] = []
    left = need

    consumed: list[tuple[ProductStockAddition, int]] = []
    for lot in lots:
        if left <= 0:
            break
        available = int(lot.qty_remaining or 0)
        if available <= 0:
            continue
        take = min(available, left)
        slices.append(
            FifoSlice(
                qty=take,
                in_price=float(lot.in_price or 0),
                out_price=float(lot.out_price or 0),
                lot_id=lot.id,
            )
        )
        if consume:
            lot.qty_remaining = available - take
            consumed.append((lot, take))
        left -= take

    if left > 0:
        for lot, qty in consumed:
            lot.qty_remaining = int(lot.qty_remaining or 0) + qty
        return []  # not enough lot stock
    return slices


def allocate_from_lot(
    db: Session,
    lot_id: int,
    product_id: int,
    qty_needed: int,
    *,
    consume: bool,
) -> list[FifoSlice]:
    """Take qty from one stock batch (used for damaged stock with user-selected lot)."""
    need = int(qty_needed)
    if need <= 0:
        return []

    q = select(ProductStockAddition).where(
        ProductStockAddition.id == lot_id,
        ProductStockAddition.product_id == product_id,
    )
    if consume:
        q = q.with_for_update()
    lot = db.execute(q).scalar_one_or_none()
    if not lot:
        return []

    available = int(lot.qty_remaining or 0)
    if available < need:
        return []

    if consume:
        lot.qty_remaining = available - need

    return [
        FifoSlice(
            qty=need,
            in_price=float(lot.in_price or 0),
            out_price=float(lot.out_price or 0),
            lot_id=lot.id,
        )
    ]


def fifo_head_out_price(db: Session, product_id: int, fallback: float = 0.0) -> float:
    """Next unit sale price (oldest open lot)."""
    lot = db.execute(
        select(ProductStockAddition.out_price)
        .where(
            ProductStockAddition.product_id == product_id,
            ProductStockAddition.qty_remaining > 0,
        )
        .order_by(ProductStockAddition.created_at.asc(), ProductStockAddition.id.asc())
        .limit(1)
    ).scalar_one_or_none()
    if lot is None:
        return float(fallback or 0)
    return float(lot)


def restore_fifo_stock(db: Session, product_id: int, qty: int) -> bool:
    """Return consumed units to lots (newest lots first) when reducing a damage record."""
    need = int(qty)
    if need <= 0:
        return True

    lots = db.execute(
        select(ProductStockAddition)
        .where(ProductStockAddition.product_id == product_id)
        .order_by(ProductStockAddition.created_at.desc(), ProductStockAddition.id.desc())
    ).scalars().all()

    restored: list[tuple[ProductStockAddition, int]] = []
    left = need
    for lot in lots:
        if left <= 0:
            break
        consumed_from_lot = int(lot.qty or 0) - int(lot.qty_remaining if lot.qty_remaining is not None else lot.qty or 0)
        if consumed_from_lot <= 0:
            continue
        put = min(consumed_from_lot, left)
        lot.qty_remaining = int(lot.qty_remaining if lot.qty_remaining is not None else lot.qty or 0) + put
        restored.append((lot, put))
        left -= put

    if left:
        for lot, qty_restored in restored:
            lot.qty_remaining = int(lot.qty_remaining or 0) - qty_restored
    return left == 0


def return_fifo_stock(
    db: Session,
    *,
    product: Product,
    qty: int,
    sale_price: float | None = None,
) -> int:
    """
    Put refunded units back into sellable FIFO stock.
    Prefer consumed lots with the same sale price; create a return lot for legacy rows.
    """
    left = int(qty)
    if left <= 0:
        return 0

    predicates = [ProductStockAddition.product_id == product.id]
    if sale_price is not None:
        predicates.append(ProductStockAddition.out_price == float(sale_price))

    lots = db.execute(
        select(ProductStockAddition)
        .where(*predicates)
        .order_by(ProductStockAddition.created_at.asc(), ProductStockAddition.id.asc())
        .with_for_update()
    ).scalars().all()

    returned = 0
    for lot in lots:
        if left <= 0:
            break
        remaining = int(lot.qty_remaining if lot.qty_remaining is not None else lot.qty or 0)
        consumed_from_lot = int(lot.qty or 0) - remaining
        if consumed_from_lot <= 0:
            continue
        put = min(consumed_from_lot, left)
        lot.qty_remaining = remaining + put
        returned += put
        left -= put

    if left > 0:
        create_stock_lot(
            db,
            product=product,
            qty=left,
            in_price=float(product.in_price or 0),
            out_price=float(sale_price if sale_price is not None else product.out_price or 0),
            note="refund-return",
        )
        returned += left

    return returned


def batch_fifo_head_out_prices(db: Session, product_ids: list[int]) -> dict[int, float]:
    if not product_ids:
        return {}
    rows = db.execute(
        select(ProductStockAddition.product_id, ProductStockAddition.out_price)
        .where(
            ProductStockAddition.product_id.in_(product_ids),
            ProductStockAddition.qty_remaining > 0,
        )
        .order_by(
            ProductStockAddition.product_id.asc(),
            ProductStockAddition.created_at.asc(),
            ProductStockAddition.id.asc(),
        )
    ).all()
    out: dict[int, float] = {}
    for pid, price in rows:
        if int(pid) not in out:
            out[int(pid)] = float(price or 0)
    return out
