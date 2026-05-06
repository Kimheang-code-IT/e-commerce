from fastapi import status
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.models import Product, ProductDamage, ProductStockAddition
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
)
from app.services.product_image_service import delete_stored_file_if_local, normalize_stored_image
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
            db.add(ProductStockAddition(product_id=row.id, product_name=row.name, qty=diff, note=note or "adjust"))
    if new_damaged is not None:
        diff = int(new_damaged) - prev_damaged
        if diff > 0:
            db.add(ProductDamage(product_id=row.id, product_name=row.name, qty=diff, note=note or "adjust"))


def list_products_service(*, db: Session, query: ListQuery, category: str | None):
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
    return list_response([serialize_product(row, added=amap.get(row.id, 0), damaged=dmap.get(row.id, 0)) for row in products], total)


def create_product_service(*, db: Session, body: ProductCreatePayload):
    category_row = resolve_category_by_public_id(db, body.categoryId)
    if not category_row:
        return error_response(status.HTTP_400_BAD_REQUEST, "Invalid category", "BAD_REQUEST")
    if find_duplicate_product(db, name=body.name, category_id=category_row.id):
        return error_response(status.HTTP_409_CONFLICT, "Product already exists in this category", "CONFLICT")

    row = create_product_record(
        db,
        name=body.name,
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
    if body.added and int(body.added) > 0:
        db.add(ProductStockAddition(product_id=row.id, product_name=row.name, qty=int(body.added), note=body.stockNote or "initial"))
    if body.damaged and int(body.damaged) > 0:
        db.add(ProductDamage(product_id=row.id, product_name=row.name, qty=int(body.damaged), note=body.stockNote or "initial"))
    adjust_category_product_count(db, category_row.id, 1)
    ensure_finance_for_product(db, row.id)
    db.commit()
    db.refresh(row)
    row_out = db.execute(select(Product).options(joinedload(Product.category_rel)).where(Product.id == row.id)).unique().scalar_one()
    amap, dmap = batch_stock_totals(db, [row_out.id])
    return {"data": serialize_product(row_out, added=amap.get(row_out.id, 0), damaged=dmap.get(row_out.id, 0))}


def update_product_service(*, db: Session, item_id: int, body: ProductUpdatePayload):
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

    row.name = next_name
    row.category_id = next_category_id
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
        row.in_stock = body.inStock
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
    ensure_finance_for_product(db, row.id)
    db.commit()
    row_out = db.execute(select(Product).options(joinedload(Product.category_rel)).where(Product.id == item_id)).unique().scalar_one()
    amap, dmap = batch_stock_totals(db, [row_out.id])
    return {"data": serialize_product(row_out, added=amap.get(row_out.id, 0), damaged=dmap.get(row_out.id, 0))}


def delete_product_service(*, db: Session, item_id: int):
    row = db.get(Product, item_id)
    if not row:
        return error_response(status.HTTP_404_NOT_FOUND, "Not found", "NOT_FOUND")
    delete_product_related_records(db, row.id)
    delete_stored_file_if_local(getattr(row, "image", None) or "")
    adjust_category_product_count(db, row.category_id, -1)
    db.delete(row)
    db.commit()
    return {"message": "Product deleted"}
