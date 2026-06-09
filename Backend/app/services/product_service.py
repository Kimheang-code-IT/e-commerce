from fastapi import status
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload
from app.models import Product, ProductDamage, ProductStockAddition, Supplier, SupplierProduct
from app.repositories.product_repository import (
    adjust_category_product_count,
    create_product_record,
    delete_product_related_records,
    ensure_finance_for_product,
    find_duplicate_product,
    list_products_query,
    resolve_category_by_public_id,
)
from app.schemas.common import ListQuery, ProductCreatePayload, ProductUpdatePayload
from app.services.data_service import (
    apply_created_at_range,
    apply_sort,
    batch_stock_totals,
    list_response,
    paginate_query,
    serialize_product,
    record_history,
)
from app.services.product_image_service import delete_stored_file_if_local, normalize_stored_image
from app.services.stock_fifo_service import allocate_fifo, batch_fifo_head_out_prices, create_stock_lot
from app.services.cache_service import cached_response, invalidate_products_and_dashboard, PREFIX_PRODUCTS
from app.shared.api_response import error_response


def _sync_stock_history(
    db: Session,
    row: Product,
    *,
    prev_added: int,
    prev_damaged: int,
    new_added: int | None,
    new_damaged: int | None,
    note: str | None = None,
) -> None:
    if new_added is not None:
        diff = int(new_added) - prev_added
        if diff > 0:
            create_stock_lot(
                db,
                product=row,
                qty=diff,
                in_price=float(row.in_price or 0),
                out_price=float(row.out_price or 0),
                note=note or "adjust",
            )
    if new_damaged is not None:
        diff = int(new_damaged) - prev_damaged
        if diff > 0:
            if not allocate_fifo(db, row.id, diff, consume=True):
                raise ValueError("Not enough FIFO stock for damage adjustment")
            db.add(ProductDamage(product_id=row.id, product_name=row.name, qty=diff, note=note or "adjust"))


def _sync_manual_in_stock_fifo(
    db: Session,
    row: Product,
    *,
    target_in_stock: int,
    note: str | None = None,
) -> bool:
    """Keep FIFO lots aligned when in_stock is edited directly."""
    current = int(row.in_stock or 0)
    target = max(0, int(target_in_stock or 0))
    if target == current:
        row.in_stock = target
        return True

    diff = target - current
    if diff > 0:
        create_stock_lot(
            db,
            product=row,
            qty=diff,
            in_price=float(row.in_price or 0),
            out_price=float(row.out_price or 0),
            note=note or "manual-in-stock",
        )
    else:
        if not allocate_fifo(db, row.id, abs(diff), consume=True):
            return False

    row.in_stock = target
    return True


def _upsert_supplier_product(
    db: Session,
    *,
    supplier_id: int,
    product_name: str,
    qty: int,
    unit_price: float,
    user_id: int,
) -> None:
    row = db.execute(
        select(SupplierProduct).where(
            SupplierProduct.supplier_id == supplier_id,
            SupplierProduct.product_name == product_name,
        )
    ).scalar_one_or_none()
    if row is None:
        row = SupplierProduct(
            supplier_id=supplier_id,
            product_name=product_name,
            qty=max(0, int(qty or 0)),
            unit_price=max(0.0, float(unit_price or 0)),
            amount=max(0, int(qty or 0)) * max(0.0, float(unit_price or 0)),
            updated_by=user_id,
        )
        db.add(row)
        return
    row.qty = max(0, int(qty or 0))
    row.unit_price = max(0.0, float(unit_price or 0))
    row.amount = row.qty * row.unit_price
    row.updated_by = user_id


def list_products_service(*, db: Session, query: ListQuery, category: str | None):
    cache_parts = {
        "page": query.page,
        "limit": query.limit,
        "search": query.search,
        "category": category,
        "dateFrom": query.dateFrom,
        "dateTo": query.dateTo,
        "sortBy": query.sortBy,
        "sortOrder": query.sortOrder,
    }

    def _build():
        return _list_products_uncached(db=db, query=query, category=category)

    return cached_response(PREFIX_PRODUCTS, cache_parts, _build)


def _list_products_uncached(*, db: Session, query: ListQuery, category: str | None):
    q = list_products_query(db, search=query.search, category=category)
    q = apply_created_at_range(q, query.dateFrom, query.dateTo, Product.created_at)
    q = apply_sort(
        q,
        query.sortBy,
        query.sortOrder,
        {
            "id": Product.id,
            "name": Product.name,
            "inPrice": Product.in_price,
            "outPrice": Product.out_price,
            "commission": Product.commission,
            "totalStock": Product.total_stock,
            "inStock": Product.in_stock,
            "sold": Product.sold,
            "status": Product.status,
            "createdAt": Product.created_at,
        },
    )
    rows, total = paginate_query(q, db, query.page, query.limit)
    products = [row[0] for row in rows]
    ids = [row.id for row in products]
    amap, dmap = batch_stock_totals(db, ids)
    sale_map = batch_fifo_head_out_prices(db, ids)
    return list_response(
        [
            serialize_product(
                row,
                added=amap.get(row.id, 0),
                damaged=dmap.get(row.id, 0),
                sale_price=sale_map.get(row.id),
            )
            for row in products
        ],
        total,
    )


def create_product_service(*, db: Session, body: ProductCreatePayload, user_id: int):
    category_row = resolve_category_by_public_id(db, body.categoryId)
    if not category_row:
        return error_response(status.HTTP_400_BAD_REQUEST, "Invalid category", "BAD_REQUEST")
    if find_duplicate_product(db, name=body.name, category_id=category_row.id):
        return error_response(status.HTTP_409_CONFLICT, "Product already exists in this category", "CONFLICT")
    if body.supplierId is not None:
        supplier_row = db.get(Supplier, int(body.supplierId))
        if not supplier_row:
            return error_response(status.HTTP_400_BAD_REQUEST, "Invalid supplier", "BAD_REQUEST")

    row = create_product_record(
        db,
        name=body.name,
        model=body.model,
        discount_price=(
            body.discountPrice
            if body.discountPrice > 0 and body.discountPrice < body.outPrice
            else 0
        ),
        total_price=body.outPrice,
        size=body.size,
        top=body.top,
        back_side=body.backSide,
        fretboard=body.fretboard,
        string_brand=body.string,
        finishing=body.finishing,
        color=body.color,
        category_id=category_row.id,
        in_price=body.inPrice,
        out_price=body.outPrice,
        commission=body.commission,
        total_stock=body.totalStock,
        in_stock=body.inStock,
        sold=body.sold,
        status=body.status,
        image="",
    )
    if body.image is not None and body.image.strip():
        try:
            row.image = normalize_stored_image(body.image, row.id, None)
        except ValueError:
            db.rollback()
            return error_response(status.HTTP_400_BAD_REQUEST, "Invalid image", "BAD_REQUEST")
    added_qty = int(body.added or 0)
    if added_qty > 0:
        create_stock_lot(
            db,
            product=row,
            qty=added_qty,
            in_price=body.inPrice,
            out_price=body.outPrice,
            note=body.stockNote or "initial",
        )
    elif int(row.in_stock or 0) > 0:
        # Keep FIFO ready even when product starts with inStock but no explicit "added" value.
        create_stock_lot(
            db,
            product=row,
            qty=int(row.in_stock or 0),
            in_price=body.inPrice,
            out_price=body.outPrice,
            note=body.stockNote or "initial-sync",
        )
    if body.damaged and int(body.damaged) > 0:
        db.add(ProductDamage(product_id=row.id, product_name=row.name, qty=int(body.damaged), note=body.stockNote or "initial"))
    adjust_category_product_count(db, category_row.id, 1)
    if body.supplierId is not None:
        _upsert_supplier_product(
            db,
            supplier_id=int(body.supplierId),
            product_name=row.name,
            qty=int(row.in_stock or 0),
            unit_price=float(row.in_price or 0),
            user_id=user_id,
        )
    ensure_finance_for_product(db, row.id)
    db.commit()
    db.refresh(row)

    record_history(db, user_id, "Create", f"Created product '{row.name}'")
    db.commit()
    invalidate_products_and_dashboard()

    row_out = db.execute(select(Product).options(joinedload(Product.category_rel)).where(Product.id == row.id)).unique().scalar_one()
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


def update_product_service(*, db: Session, item_id: int, body: ProductUpdatePayload, user_id: int):
    row = db.get(Product, item_id)
    if not row:
        return error_response(status.HTTP_404_NOT_FOUND, "Not found", "NOT_FOUND")

    amap0, dmap0 = batch_stock_totals(db, [row.id])
    prev_added = amap0.get(row.id, 0)
    prev_damaged = dmap0.get(row.id, 0)
    previous_category_id = row.category_id
    next_category_id = row.category_id
    if body.categoryId is not None:
        category_row = resolve_category_by_public_id(db, body.categoryId)
        if not category_row:
            return error_response(status.HTTP_400_BAD_REQUEST, "Invalid category", "BAD_REQUEST")
        next_category_id = category_row.id
    next_name = body.name if body.name is not None else row.name
    if find_duplicate_product(db, name=next_name, category_id=next_category_id, exclude_id=row.id):
        return error_response(status.HTTP_409_CONFLICT, "Product already exists in this category", "CONFLICT")
    if body.supplierId is not None:
        supplier_row = db.get(Supplier, int(body.supplierId))
        if not supplier_row:
            return error_response(status.HTTP_400_BAD_REQUEST, "Invalid supplier", "BAD_REQUEST")

    row.name = next_name
    row.category_id = next_category_id
    if body.model is not None:
        row.model = body.model
    if body.outPrice is not None:
        row.total_price = body.outPrice
    if body.discountPrice is not None:
        out_p = float(body.outPrice if body.outPrice is not None else row.out_price or 0)
        sale = float(body.discountPrice or 0)
        row.discount_price = sale if sale > 0 and sale < out_p else 0
    if body.size is not None:
        row.size = body.size
    if body.top is not None:
        row.top = body.top
    if body.backSide is not None:
        row.back_side = body.backSide
    if body.fretboard is not None:
        row.fretboard = body.fretboard
    if body.string is not None:
        row.string_brand = body.string
    if body.finishing is not None:
        row.finishing = body.finishing
    if body.color is not None:
        row.color = body.color
    if body.status is not None:
        row.status = body.status
    if body.inPrice is not None:
        row.in_price = body.inPrice
    if body.outPrice is not None:
        row.out_price = body.outPrice
    if body.commission is not None:
        row.commission = body.commission
    if body.totalStock is not None:
        row.total_stock = body.totalStock
    if body.inStock is not None:
        if not _sync_manual_in_stock_fifo(
            db,
            row,
            target_in_stock=int(body.inStock or 0),
            note=body.stockNote or "manual-in-stock",
        ):
            return error_response(status.HTTP_400_BAD_REQUEST, "Not enough FIFO stock for inStock reduction", "NOT_ENOUGH_STOCK")
    if body.sold is not None:
        row.sold = body.sold
    _sync_stock_history(db, row, prev_added=prev_added, prev_damaged=prev_damaged, new_added=body.added, new_damaged=body.damaged, note=body.stockNote)
    if body.image is not None:
        try:
            row.image = normalize_stored_image(body.image, row.id, row.image or None)
        except ValueError:
            return error_response(status.HTTP_400_BAD_REQUEST, "Invalid image", "BAD_REQUEST")
    if next_category_id != previous_category_id:
        adjust_category_product_count(db, previous_category_id, -1)
        adjust_category_product_count(db, next_category_id, 1)
    if body.supplierId is not None:
        _upsert_supplier_product(
            db,
            supplier_id=int(body.supplierId),
            product_name=row.name,
            qty=int(row.in_stock or 0),
            unit_price=float(row.in_price or 0),
            user_id=user_id,
        )
    ensure_finance_for_product(db, row.id)
    db.commit()
    db.refresh(row)

    record_history(db, user_id, "Update", f"Updated product '{row.name}'")
    db.commit()
    invalidate_products_and_dashboard()

    row_out = db.execute(select(Product).options(joinedload(Product.category_rel)).where(Product.id == item_id)).unique().scalar_one()
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


def delete_product_service(*, db: Session, item_id: int, user_id: int):
    row = db.get(Product, item_id)
    if not row:
        return error_response(status.HTTP_404_NOT_FOUND, "Not found", "NOT_FOUND")
    
    product_name = row.name
    delete_product_related_records(db, row.id)
    delete_stored_file_if_local(getattr(row, "image", None) or "")
    adjust_category_product_count(db, row.category_id, -1)
    db.delete(row)
    db.commit()

    record_history(db, user_id, "Delete", f"Deleted product '{product_name}'")
    db.commit()
    invalidate_products_and_dashboard()
    return {"message": "Product deleted"}
