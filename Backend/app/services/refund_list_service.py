"""Refund list grouped by invoice (one table row per invoice, like reports-view)."""

from __future__ import annotations

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.models import Invoice, RefundRecord
from app.services.data_service import apply_created_at_range, parse_csv, to_iso


def _dedupe_joined(values: list[str], *, max_len: int = 177) -> str:
    seen: set[str] = set()
    parts: list[str] = []
    for raw in values:
        name = (raw or "").strip()
        if not name or name in seen:
            continue
        seen.add(name)
        parts.append(name)
    text = ", ".join(parts)
    if len(text) > max_len:
        return text[: max_len - 3] + "..."
    return text


def _dedupe_reasons(values: list[str]) -> str:
    seen: set[str] = set()
    parts: list[str] = []
    for raw in values:
        text = (raw or "").strip()
        if not text or text in seen:
            continue
        seen.add(text)
        parts.append(text)
    return "; ".join(parts)


def build_refunds_query(
    db: Session,
    *,
    search: str | None = None,
    products: list[str] | None = None,
    provinces: list[str] | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    invoice_nos: list[str] | None = None,
):
    q = select(RefundRecord).where(
        RefundRecord.invoice_no.isnot(None),
        RefundRecord.invoice_no != "",
    )
    if search:
        keyword = search.strip()
        q = q.where(
            RefundRecord.invoice_no.ilike(f"%{keyword}%")
            | RefundRecord.customer.ilike(f"%{keyword}%")
            | RefundRecord.product.ilike(f"%{keyword}%")
            | RefundRecord.seller.ilike(f"%{keyword}%")
        )
    if products:
        q = q.where(or_(*[RefundRecord.product.ilike(f"%{name}%") for name in products]))
    if provinces:
        q = q.where(RefundRecord.address.in_(provinces))
    if invoice_nos:
        q = q.where(RefundRecord.invoice_no.in_(invoice_nos))
    q = apply_created_at_range(q, date_from, date_to, RefundRecord.refunded_at)
    return q


def group_refund_rows(rows: list[RefundRecord], db: Session) -> list[dict]:
    if not rows:
        return []

    invoice_nos = {r.invoice_no for r in rows if r.invoice_no}
    inv_map: dict[str, int] = {}
    if invoice_nos:
        inv_rows = db.execute(
            select(Invoice.invoice_no, Invoice.id).where(Invoice.invoice_no.in_(invoice_nos))
        ).all()
        inv_map = {str(no): int(iid) for no, iid in inv_rows}

    groups: dict[str, dict] = {}
    for row in rows:
        key = row.invoice_no or ""
        if not key:
            continue
        if key not in groups:
            groups[key] = {
                "invoice_no": key,
                "invoice_id": inv_map.get(key),
                "products": [],
                "product_set": set(),
                "reasons": [],
                "reason_set": set(),
                "amount": 0.0,
                "refund_ids": [],
                "refunded_at": row.refunded_at,
                "customer": row.customer or "",
                "seller": row.seller or "",
                "address": row.address or "",
                "sale_date": row.sale_date or "",
            }
        g = groups[key]
        g["amount"] += float(row.amount or 0)
        g["refund_ids"].append(int(row.id))
        name = (row.product or "").strip()
        if name and name not in g["product_set"]:
            g["product_set"].add(name)
            g["products"].append(name)
        reason = (row.refund_reason or "").strip()
        if reason and reason not in g["reason_set"]:
            g["reason_set"].add(reason)
            g["reasons"].append(reason)
        if row.refunded_at and (not g["refunded_at"] or row.refunded_at > g["refunded_at"]):
            g["refunded_at"] = row.refunded_at
            g["customer"] = row.customer or g["customer"]
            g["seller"] = row.seller or g["seller"]
            g["address"] = row.address or g["address"]
            g["sale_date"] = row.sale_date or g["sale_date"]

    out: list[dict] = []
    for g in groups.values():
        invoice_id = int(g["invoice_id"] or 0)
        out.append(
            {
                "id": invoice_id if invoice_id > 0 else int(g["refund_ids"][0]),
                "invoiceId": invoice_id if invoice_id > 0 else None,
                "invoiceNo": g["invoice_no"],
                "date": g["sale_date"],
                "product": _dedupe_joined(g["products"]),
                "productId": 0,
                "qty": 0,
                "price": 0,
                "customer": g["customer"],
                "phoneCustomer": "",
                "phoneSaler": "",
                "seller": g["seller"],
                "address": g["address"],
                "amount": float(g["amount"]),
                "refundedAt": to_iso(g["refunded_at"]),
                "refundReason": _dedupe_reasons(g["reasons"]),
                "refundIds": sorted(g["refund_ids"]),
            }
        )
    return out


def _grouped_invoice_page_query(
    db: Session,
    *,
    search: str | None = None,
    products: list[str] | None = None,
    provinces: list[str] | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    sort_by: str | None = None,
    sort_order: str | None = None,
):
    filtered = build_refunds_query(
        db,
        search=search,
        products=products,
        provinces=provinces,
        date_from=date_from,
        date_to=date_to,
    ).order_by(None)
    rr = filtered.subquery()

    sort_key = sort_by or "refundedAt"
    reverse = (sort_order or "desc").lower() != "asc"
    sort_map = {
        "refundedAt": func.max(rr.c.refunded_at),
        "invoiceNo": rr.c.invoice_no,
        "amount": func.sum(rr.c.amount),
        "product": func.min(rr.c.product),
        "seller": func.min(rr.c.seller),
        "source": func.min(rr.c.source),
        "customer": func.min(rr.c.customer),
    }
    order_expr = sort_map.get(sort_key, func.max(rr.c.refunded_at))

    grouped = (
        select(
            rr.c.invoice_no,
            func.max(rr.c.refunded_at).label("latest_refund"),
            func.sum(rr.c.amount).label("total_amount"),
        )
        .group_by(rr.c.invoice_no)
    )
    grouped = grouped.order_by(order_expr.desc() if reverse else order_expr.asc(), rr.c.invoice_no.asc())
    return grouped


def list_grouped_refunds(
    db: Session,
    *,
    page: int,
    limit: int,
    search: str | None = None,
    product: str | None = None,
    province: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    sort_by: str | None = None,
    sort_order: str | None = None,
):
    products = parse_csv(product)
    provinces = parse_csv(province)

    grouped = _grouped_invoice_page_query(
        db,
        search=search,
        products=products,
        provinces=provinces,
        date_from=date_from,
        date_to=date_to,
        sort_by=sort_by,
        sort_order=sort_order,
    )
    total = db.scalar(select(func.count()).select_from(grouped.order_by(None).subquery())) or 0

    page_rows = db.execute(grouped.offset(max(0, (page - 1) * limit)).limit(limit)).all()
    invoice_nos = [str(row.invoice_no) for row in page_rows if row.invoice_no]
    if not invoice_nos:
        return [], total

    detail_q = build_refunds_query(
        db,
        search=search,
        products=products,
        provinces=provinces,
        date_from=date_from,
        date_to=date_to,
        invoice_nos=invoice_nos,
    ).order_by(RefundRecord.refunded_at.desc(), RefundRecord.id.desc())
    rows = db.scalars(detail_q).all()
    grouped_data = group_refund_rows(list(rows), db)

    order_index = {invoice_no: index for index, invoice_no in enumerate(invoice_nos)}
    grouped_data.sort(key=lambda item: order_index.get(str(item.get("invoiceNo") or ""), 10_000))
    return grouped_data, total
