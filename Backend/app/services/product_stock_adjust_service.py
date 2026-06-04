from fastapi import status
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.models import Product, ProductDamage
from app.schemas.common import ProductStockAdjustPayload
from app.services.cache_service import invalidate_products_and_dashboard
from app.services.data_service import batch_stock_totals, record_history, serialize_product
from app.services.stock_fifo_service import (
    allocate_fifo,
    allocate_from_lot,
    batch_fifo_head_out_prices,
    create_stock_lot,
)
from app.shared.api_response import error_response


def adjust_product_stock_service(
    *,
    db: Session,
    item_id: int,
    body: ProductStockAdjustPayload,
    user_id: int,
):
    row = db.get(Product, item_id)
    if not row:
        return error_response(status.HTTP_404_NOT_FOUND, "Not found", "NOT_FOUND")

    qty = int(body.qty)
    note = (body.note or "").strip() or "adjust"

    if body.mode == "added":
        create_stock_lot(
            db,
            product=row,
            qty=qty,
            in_price=body.inPrice,
            out_price=body.outPrice,
            note=note,
        )
        row.in_stock = int(row.in_stock or 0) + qty
        row.total_stock = int(row.total_stock or 0) + qty
        row.in_price = float(body.inPrice)
        row.out_price = float(body.outPrice)
        action = f"Added {qty} stock (cost ${body.inPrice:.2f}, sale ${body.outPrice:.2f})"
    else:
        if int(row.in_stock or 0) < qty:
            return error_response(
                status.HTTP_400_BAD_REQUEST,
                f"Not enough stock (available: {row.in_stock})",
                "NOT_ENOUGH_STOCK",
            )
        if body.stockAdditionId:
            slices = allocate_from_lot(
                db,
                int(body.stockAdditionId),
                row.id,
                qty,
                consume=True,
            )
            if not slices:
                return error_response(
                    status.HTTP_400_BAD_REQUEST,
                    "Selected stock batch has insufficient quantity",
                    "NOT_ENOUGH_STOCK",
                )
        else:
            slices = allocate_fifo(db, row.id, qty, consume=True)
            if not slices:
                return error_response(
                    status.HTTP_400_BAD_REQUEST,
                    "Not enough stock in FIFO lots",
                    "NOT_ENOUGH_STOCK",
                )
        db.add(
            ProductDamage(
                product_id=row.id,
                product_name=row.name,
                qty=qty,
                note=note,
            )
        )
        row.in_stock = max(0, int(row.in_stock or 0) - qty)
        lot_label = f"lot #{body.stockAdditionId}" if body.stockAdditionId else "FIFO"
        action = f"Recorded {qty} damaged ({lot_label})"

    db.commit()
    db.refresh(row)

    record_history(db, user_id, "Update", f"{action} for '{row.name}'")
    db.commit()
    invalidate_products_and_dashboard()

    row_out = (
        db.execute(select(Product).options(joinedload(Product.category_rel)).where(Product.id == item_id))
        .unique()
        .scalar_one()
    )
    amap, dmap = batch_stock_totals(db, [row_out.id])
    sale_map = batch_fifo_head_out_prices(db, [row_out.id])
    return {
        "data": serialize_product(
            row_out,
            added=amap.get(row_out.id, 0),
            damaged=dmap.get(row_out.id, 0),
            sale_price=sale_map.get(row_out.id),
        )
    }
