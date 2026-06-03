"""Update individual stock addition (FIFO lot) or damage history rows."""

from fastapi import status
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.models import Product, ProductDamage, ProductStockAddition
from app.schemas.common import StockAdditionUpdatePayload, StockDamageUpdatePayload
from app.services.cache_service import invalidate_products_and_dashboard
from app.services.data_service import batch_stock_totals, record_history, serialize_product
from app.services.stock_fifo_service import allocate_fifo, batch_fifo_head_out_prices, restore_fifo_stock
from app.shared.api_response import error_response


def update_stock_addition_service(
    *,
    db: Session,
    product_id: int,
    record_id: int,
    body: StockAdditionUpdatePayload,
    user_id: int,
):
    product = db.get(Product, product_id)
    if not product:
        return error_response(status.HTTP_404_NOT_FOUND, "Product not found", "NOT_FOUND")

    lot = db.execute(
        select(ProductStockAddition).where(
            ProductStockAddition.id == record_id,
            ProductStockAddition.product_id == product_id,
        )
    ).scalar_one_or_none()
    if not lot:
        return error_response(status.HTTP_404_NOT_FOUND, "Stock batch not found", "NOT_FOUND")

    if body.qty is None and body.inPrice is None and body.outPrice is None and body.note is None:
        return error_response(status.HTTP_400_BAD_REQUEST, "No fields to update", "BAD_REQUEST")

    old_qty = int(lot.qty or 0)
    old_remaining = int(lot.qty_remaining if lot.qty_remaining is not None else lot.qty or 0)
    consumed = max(0, old_qty - old_remaining)

    if body.qty is not None:
        new_qty = int(body.qty)
        if new_qty < consumed:
            return error_response(
                status.HTTP_400_BAD_REQUEST,
                f"Cannot set qty below {consumed} (already sold/damaged from this batch)",
                "INVALID_QTY",
            )
        delta = new_qty - old_qty
        lot.qty = new_qty
        lot.qty_remaining = new_qty - consumed
        product.in_stock = int(product.in_stock or 0) + delta
        product.total_stock = int(product.total_stock or 0) + delta

    if body.inPrice is not None:
        lot.in_price = float(body.inPrice)
    if body.outPrice is not None:
        lot.out_price = float(body.outPrice)
    if body.note is not None:
        lot.note = body.note.strip()

    db.commit()
    db.refresh(product)

    record_history(
        db,
        user_id,
        "Update",
        f"Updated stock batch #{record_id} for '{product.name}'",
    )
    db.commit()
    invalidate_products_and_dashboard()

    row_out = (
        db.execute(select(Product).options(joinedload(Product.category_rel)).where(Product.id == product_id))
        .unique()
        .scalar_one()
    )
    amap, dmap = batch_stock_totals(db, [row_out.id])
    sale_map = batch_fifo_head_out_prices(db, [row_out.id])
    return {
        "data": {
            "product": serialize_product(
                row_out,
                added=amap.get(row_out.id, 0),
                damaged=dmap.get(row_out.id, 0),
                sale_price=sale_map.get(row_out.id),
            ),
            "record": {
                "id": lot.id,
                "qty": lot.qty,
                "qtyRemaining": lot.qty_remaining,
                "inPrice": lot.in_price,
                "outPrice": lot.out_price,
                "note": lot.note,
                "createdAt": lot.created_at.isoformat(),
            },
        }
    }


def update_stock_damage_service(
    *,
    db: Session,
    product_id: int,
    record_id: int,
    body: StockDamageUpdatePayload,
    user_id: int,
):
    product = db.get(Product, product_id)
    if not product:
        return error_response(status.HTTP_404_NOT_FOUND, "Product not found", "NOT_FOUND")

    damage = db.execute(
        select(ProductDamage).where(
            ProductDamage.id == record_id,
            ProductDamage.product_id == product_id,
        )
    ).scalar_one_or_none()
    if not damage:
        return error_response(status.HTTP_404_NOT_FOUND, "Damage record not found", "NOT_FOUND")

    if body.qty is None and body.note is None:
        return error_response(status.HTTP_400_BAD_REQUEST, "No fields to update", "BAD_REQUEST")

    if body.qty is not None:
        old_qty = int(damage.qty or 0)
        new_qty = int(body.qty)
        delta = new_qty - old_qty

        if delta > 0:
            if int(product.in_stock or 0) < delta:
                return error_response(
                    status.HTTP_400_BAD_REQUEST,
                    f"Not enough stock to increase damage by {delta}",
                    "NOT_ENOUGH_STOCK",
                )
            if not allocate_fifo(db, product_id, delta, consume=True):
                return error_response(
                    status.HTTP_400_BAD_REQUEST,
                    "Not enough FIFO stock for damage adjustment",
                    "NOT_ENOUGH_STOCK",
                )
            product.in_stock = int(product.in_stock or 0) - delta
        elif delta < 0:
            restore = -delta
            if not restore_fifo_stock(db, product_id, restore):
                return error_response(
                    status.HTTP_400_BAD_REQUEST,
                    "Could not restore stock to FIFO batches (no consumed lots to refill)",
                    "RESTORE_FAILED",
                )
            product.in_stock = int(product.in_stock or 0) + restore

        damage.qty = new_qty

    if body.note is not None:
        damage.note = body.note.strip()

    db.commit()
    db.refresh(product)

    record_history(
        db,
        user_id,
        "Update",
        f"Updated damage record #{record_id} for '{product.name}'",
    )
    db.commit()
    invalidate_products_and_dashboard()

    row_out = (
        db.execute(select(Product).options(joinedload(Product.category_rel)).where(Product.id == product_id))
        .unique()
        .scalar_one()
    )
    amap, dmap = batch_stock_totals(db, [row_out.id])
    sale_map = batch_fifo_head_out_prices(db, [row_out.id])
    return {
        "data": {
            "product": serialize_product(
                row_out,
                added=amap.get(row_out.id, 0),
                damaged=dmap.get(row_out.id, 0),
                sale_price=sale_map.get(row_out.id),
            ),
            "record": {
                "id": damage.id,
                "qty": damage.qty,
                "note": damage.note,
                "createdAt": damage.created_at.isoformat(),
            },
        }
    }
