import json
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models import Category, CheckoutItem, Finance, Invoice, Product, ProductDamage, ProductStockAddition, Role, User
from app.services.product_image_service import public_image_url
from app.services.product_stock_status import stock_status_tier


def list_response(rows: list[dict[str, Any]], total: int, aggregates: dict[str, Any] | None = None):
    payload: dict[str, Any] = {"data": rows, "total": total}
    if aggregates is not None:
        payload["aggregates"] = aggregates
    return payload


def paginate_query(query, db: Session, page: int, limit: int):
    total = db.scalar(select(func.count()).select_from(query.order_by(None).subquery())) or 0
    rows = db.execute(query.offset((page - 1) * limit).limit(limit)).all()
    return rows, total


def apply_sort(query, sort_by: str | None, sort_order: str | None, sort_map: dict[str, Any]):
    if not sort_by or sort_by not in sort_map:
        return query
    col = sort_map[sort_by]
    if (sort_order or "").lower() == "desc":
        return query.order_by(col.desc())
    return query.order_by(col.asc())


def parse_csv(value: str | None) -> list[str]:
    if not value:
        return []
    return [item.strip() for item in value.split(",") if item.strip()]


def parse_iso_date(value: str | None, end_of_day: bool = False) -> datetime | None:
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        try:
            parsed = datetime.strptime(value, "%Y-%m-%d")
        except ValueError:
            return None
    if end_of_day and len(value) <= 10:
        return parsed + timedelta(days=1)
    return parsed


def apply_created_at_range(query, date_from: str | None, date_to: str | None, column):
    parsed_from = parse_iso_date(date_from)
    parsed_to = parse_iso_date(date_to, end_of_day=True)
    if parsed_from:
        query = query.where(column >= parsed_from)
    if parsed_to:
        query = query.where(column < parsed_to)
    return query


def to_iso(dt_value: datetime | None) -> str:
    if not dt_value:
        return ""
    return dt_value.isoformat()


def serialize_category(row: Category) -> dict[str, Any]:
    return {
        "id": row.public_id,
        "name": row.name,
        "description": row.description,
        "total": row.product_count,
        "createdAt": to_iso(row.created_at),
    }


def batch_stock_totals(db: Session, product_ids: list[int]) -> tuple[dict[int, int], dict[int, int]]:
    if not product_ids:
        return {}, {}
    stmt_a = (
        select(ProductStockAddition.product_id, func.coalesce(func.sum(ProductStockAddition.qty), 0))
        .where(ProductStockAddition.product_id.in_(product_ids))
        .group_by(ProductStockAddition.product_id)
    )
    stmt_d = (
        select(ProductDamage.product_id, func.coalesce(func.sum(ProductDamage.qty), 0))
        .where(ProductDamage.product_id.in_(product_ids))
        .group_by(ProductDamage.product_id)
    )
    added = {int(pid): int(s or 0) for pid, s in db.execute(stmt_a).all()}
    damaged = {int(pid): int(s or 0) for pid, s in db.execute(stmt_d).all()}
    return added, damaged


def serialize_product(
    row: Product,
    *,
    added: int = 0,
    damaged: int = 0,
) -> dict[str, Any]:
    category_name = row.category_rel.name if getattr(row, "category_rel", None) is not None else ""
    category_public = Category.to_public_id(row.category_id) if row.category_id else ""
    return {
        "id": row.id,
        "image": public_image_url(getattr(row, "image", None) or ""),
        "name": row.name,
        "category": category_name,
        "categoryId": category_public,
        "inPrice": row.in_price,
        "outPrice": row.out_price,
        "commission": row.commission,
        "totalStock": row.total_stock,
        "inStock": row.in_stock,
        "sold": row.sold,
        "added": added,
        "damaged": damaged,
        "status": row.status,
        "stockStatus": stock_status_tier(int(row.in_stock or 0)),
        "createdAt": to_iso(row.created_at),
    }


def serialize_report_row(ci: CheckoutItem, inv: Invoice, u: User | None = None) -> dict[str, Any]:
    return {
        "id": ci.id,
        "invoiceNo": inv.invoice_no,
        "date": to_iso(inv.created_at),
        # One row = one checkout line product
        "product": ci.product_name,
        "customer": inv.customer_name,
        "phoneCustomer": inv.customer_phone,
        "seller": u.name if u else "",
        "phoneSaler": "",
        "source": inv.source or "",
        "address": inv.customer_address or "",
        "amount": float(ci.total),
    }


def serialize_finance_view(row_f: Finance, row_p: Product) -> dict[str, Any]:
    sold_qty = float(row_f.total_sold_product or 0)
    in_cost = float(row_p.in_price or 0) * sold_qty
    gross = float(row_p.out_price or 0) * sold_qty
    final_price = gross - float(row_f.total_commission or 0) - float(row_f.facebook or 0) - float(row_f.other or 0) - in_cost
    return {
        "id": row_f.id,
        "productName": row_p.name,
        "printPrice": row_p.in_price,
        "totalCommission": row_f.total_commission,
        "facebook": row_f.facebook,
        "other": row_f.other,
        "inPriceForPos": in_cost,
        "finalPrice": final_price,
        "createdAt": to_iso(row_f.created_at),
    }


def serialize_commission_row(ci: CheckoutItem, inv: Invoice, seller: User | None, product: Product | None) -> dict[str, Any]:
    unit_commission = float(product.commission or 0) if product else 0.0
    commission_amt = unit_commission * int(ci.quantity or 0)
    return {
        "id": ci.id,
        "seller": seller.name if seller else "",
        "invoiceNo": inv.invoice_no,
        "product": ci.product_name,
        "customer": inv.customer_name,
        "source": inv.source or "",
        "date": to_iso(inv.created_at),
        "amount": float(ci.total),
        "commission": commission_amt,
    }


def serialize_delivery_invoice(inv: Invoice) -> dict[str, Any]:
    return {
        "id": inv.id,
        "no": inv.id,
        "invoiceNo": inv.invoice_no,
        "invoiceId": inv.invoice_no,
        "customer": inv.customer_name,
        "address": inv.customer_address or "",
        "deliveryType": inv.delivery_type or "",
        "deliveryStatus": inv.delivery_status or "",
        "deliveryPrice": float(inv.delivery_price or 0),
        "date": to_iso(inv.created_at),
    }


def serialize_role(row: Role) -> dict[str, Any]:
    try:
        pages = json.loads(row.page_access or "[]")
        if not isinstance(pages, list):
            pages = []
    except json.JSONDecodeError:
        pages = []
    return {"id": row.id, "name": row.name, "pageAccess": pages}


def serialize_user(row: User, *, role_name: str | None = None) -> dict[str, Any]:
    resolved_role = role_name or (row.role_rel.name if getattr(row, "role_rel", None) else "")
    return {
        "id": row.id,
        "name": row.name,
        "role": resolved_role,
        "email": row.email,
        "lastLogin": "",
        "commission": 0,
    }


def export_payload(data: list[dict[str, Any]], module_name: str):
    if len(data) <= settings.export_inline_threshold:
        return {"data": data}
    export_dir = Path(settings.export_dir)
    export_dir.mkdir(parents=True, exist_ok=True)
    file_name = f"{module_name}-{uuid.uuid4().hex}.json"
    (export_dir / file_name).write_text(json.dumps(data), encoding="utf-8")
    return {"data": {"url": f"/{settings.export_dir}/{file_name}"}}
