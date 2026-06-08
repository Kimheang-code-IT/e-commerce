from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.dependencies.common import list_query_dependency
from app.models import Supplier, SupplierProduct, User
from app.schemas.common import (
    ListQuery,
    SupplierCreatePayload,
    SupplierProductUpdatePayload,
    SupplierUpdatePayload,
)
from app.services.auth_service import get_current_user, require_permission
from app.services.data_service import apply_created_at_range, apply_sort, list_response, paginate_query, record_history
from app.shared.api_response import error_response

router = APIRouter(prefix="/suppliers", tags=["suppliers"], dependencies=[Depends(get_current_user)])


def _serialize_supplier(row: Supplier, product_count: int, total_amount: float, total_qty: int):
    return {
        "id": row.id,
        "name": row.name,
        "gender": row.gender,
        "address": row.address,
        "phoneNumber": row.phone_number,
        "totalProduct": int(total_qty or 0),
        "productCount": int(product_count or 0),
        "totalAmount": float(total_amount or 0),
        "createdAt": row.created_at.isoformat(),
    }


@router.get("")
def list_suppliers(
    query: ListQuery = Depends(list_query_dependency),
    _: User = Depends(require_permission("supplier:view")),
    db: Session = Depends(get_db),
):
    totals_subq = (
        select(
            SupplierProduct.supplier_id.label("supplier_id"),
            func.count(SupplierProduct.id).label("product_count"),
            func.coalesce(func.sum(SupplierProduct.qty), 0).label("total_qty"),
            func.coalesce(func.sum(SupplierProduct.amount), 0).label("total_amount"),
        )
        .group_by(SupplierProduct.supplier_id)
        .subquery()
    )
    q = (
        select(
            Supplier,
            func.coalesce(totals_subq.c.product_count, 0),
            func.coalesce(totals_subq.c.total_amount, 0),
            func.coalesce(totals_subq.c.total_qty, 0),
        )
        .outerjoin(totals_subq, totals_subq.c.supplier_id == Supplier.id)
    )
    if query.search:
        keyword = query.search.strip()
        q = q.where(
            Supplier.name.ilike(f"%{keyword}%")
            | Supplier.address.ilike(f"%{keyword}%")
            | Supplier.phone_number.ilike(f"%{keyword}%")
        )
    q = apply_created_at_range(q, query.dateFrom, query.dateTo, Supplier.created_at)
    q = apply_sort(
        q,
        query.sortBy,
        query.sortOrder,
        {
            "id": Supplier.id,
            "name": Supplier.name,
            "gender": Supplier.gender,
            "address": Supplier.address,
            "phoneNumber": Supplier.phone_number,
            "createdAt": Supplier.created_at,
        },
    )
    rows, total = paginate_query(q, db, query.page, query.limit)
    return list_response(
        [_serialize_supplier(row[0], int(row[1] or 0), float(row[2] or 0), int(row[3] or 0)) for row in rows],
        total,
    )


@router.post("")
def create_supplier(
    payload: SupplierCreatePayload,
    current_user: User = Depends(get_current_user),
    _: User = Depends(require_permission("supplier:create")),
    db: Session = Depends(get_db),
):
    row = Supplier(
        name=payload.name,
        gender=payload.gender,
        address=payload.address,
        phone_number=payload.phoneNumber,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    record_history(db, current_user.id, "Create", f"Created supplier '{row.name}'")
    db.commit()
    return {"data": _serialize_supplier(row, 0, 0, 0)}


@router.put("/{supplier_id}")
def update_supplier(
    supplier_id: int,
    payload: SupplierUpdatePayload,
    current_user: User = Depends(get_current_user),
    _: User = Depends(require_permission("supplier:update")),
    db: Session = Depends(get_db),
):
    row = db.get(Supplier, supplier_id)
    if not row:
        return error_response(status.HTTP_404_NOT_FOUND, "Supplier not found", "NOT_FOUND")

    if payload.name is not None:
        row.name = payload.name
    if payload.gender is not None:
        row.gender = payload.gender
    if payload.address is not None:
        row.address = payload.address
    if payload.phoneNumber is not None:
        row.phone_number = payload.phoneNumber

    db.commit()
    db.refresh(row)
    record_history(db, current_user.id, "Update", f"Updated supplier '{row.name}'")
    db.commit()

    p_count = db.scalar(select(func.count(SupplierProduct.id)).where(SupplierProduct.supplier_id == supplier_id)) or 0
    t_qty = db.scalar(select(func.coalesce(func.sum(SupplierProduct.qty), 0)).where(SupplierProduct.supplier_id == supplier_id)) or 0
    t_amount = db.scalar(select(func.coalesce(func.sum(SupplierProduct.amount), 0)).where(SupplierProduct.supplier_id == supplier_id)) or 0
    return {"data": _serialize_supplier(row, int(p_count), float(t_amount), int(t_qty))}


@router.delete("/{supplier_id}")
def delete_supplier(
    supplier_id: int,
    current_user: User = Depends(get_current_user),
    _: User = Depends(require_permission("supplier:delete")),
    db: Session = Depends(get_db),
):
    row = db.get(Supplier, supplier_id)
    if not row:
        return error_response(status.HTTP_404_NOT_FOUND, "Supplier not found", "NOT_FOUND")
    # Prevent deleting suppliers that still have linked products.
    in_use = db.scalar(select(func.count(SupplierProduct.id)).where(SupplierProduct.supplier_id == supplier_id)) or 0
    if in_use > 0:
        return error_response(
            status.HTTP_400_BAD_REQUEST,
            "Supplier is in use and cannot be deleted.",
            "SUPPLIER_IN_USE",
        )
    name = row.name
    db.delete(row)
    record_history(db, current_user.id, "Delete", f"Deleted supplier '{name}'")
    db.commit()
    return {"message": "Supplier deleted"}


@router.get("/{supplier_id}/products")
def list_supplier_products(
    supplier_id: int,
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=200),
    dateFrom: str | None = None,
    dateTo: str | None = None,
    _: User = Depends(require_permission("supplier:view")),
    db: Session = Depends(get_db),
):
    supplier = db.get(Supplier, supplier_id)
    if not supplier:
        return error_response(status.HTTP_404_NOT_FOUND, "Supplier not found", "NOT_FOUND")
    q = select(SupplierProduct).where(SupplierProduct.supplier_id == supplier_id)
    q = apply_created_at_range(q, dateFrom, dateTo, SupplierProduct.created_at)
    q = q.order_by(SupplierProduct.created_at.desc())
    rows, total = paginate_query(q, db, page, limit)
    return list_response(
        [
            {
                "id": r[0].id,
                "productName": r[0].product_name,
                "qty": r[0].qty,
                "unitPrice": r[0].unit_price,
                "amount": r[0].amount,
                "createdAt": r[0].created_at.isoformat(),
            }
            for r in rows
        ],
        total,
    )


@router.patch("/{supplier_id}/products/{product_id}")
def update_supplier_product(
    supplier_id: int,
    product_id: int,
    payload: SupplierProductUpdatePayload,
    current_user: User = Depends(get_current_user),
    _: User = Depends(require_permission("supplier:update")),
    db: Session = Depends(get_db),
):
    row = db.execute(
        select(SupplierProduct).where(
            SupplierProduct.id == product_id,
            SupplierProduct.supplier_id == supplier_id,
        )
    ).scalar_one_or_none()
    if not row:
        return error_response(status.HTTP_404_NOT_FOUND, "Supplier product not found", "NOT_FOUND")
    if payload.productName is not None:
        row.product_name = payload.productName
    if payload.qty is not None:
        row.qty = int(payload.qty)
    if payload.unitPrice is not None:
        row.unit_price = float(payload.unitPrice)
    row.amount = float(row.qty or 0) * float(row.unit_price or 0)
    row.updated_by = current_user.id
    db.commit()
    record_history(db, current_user.id, "Update", f"Updated supplier product #{row.id}")
    db.commit()
    return {
        "data": {
            "id": row.id,
            "productName": row.product_name,
            "qty": row.qty,
            "unitPrice": row.unit_price,
            "amount": row.amount,
            "createdAt": row.created_at.isoformat(),
        }
    }
