"""Distinct values for list-view filters (scoped by date range when provided)."""
from __future__ import annotations

from sqlalchemy import distinct, select
from sqlalchemy.orm import Session

from app.models import CheckoutItem, History, Invoice
from app.services.data_service import apply_created_at_range


def _sorted_non_empty(rows: list[tuple]) -> list[str]:
    out: set[str] = set()
    for row in rows:
        if row[0] is None:
            continue
        text = str(row[0]).strip()
        if text:
            out.add(text)
    return sorted(out)


def history_action_options(
    db: Session,
    *,
    date_from: str | None = None,
    date_to: str | None = None,
) -> list[str]:
    q = select(distinct(History.type_action))
    q = apply_created_at_range(q, date_from, date_to, History.created_at)
    rows = db.execute(q.order_by(History.type_action)).all()
    return _sorted_non_empty(rows)


def _invoice_options_query(column, *, paid_only: bool = False):
    q = select(distinct(column))
    if paid_only:
        q = q.where(Invoice.status == "paid")
    return q


def invoice_field_options(
    db: Session,
    column,
    *,
    date_from: str | None = None,
    date_to: str | None = None,
    paid_only: bool = False,
) -> list[str]:
    q = _invoice_options_query(column, paid_only=paid_only)
    q = apply_created_at_range(q, date_from, date_to, Invoice.created_at)
    rows = db.execute(q.order_by(column)).all()
    return _sorted_non_empty(rows)


def report_filter_options(
    db: Session,
    *,
    date_from: str | None = None,
    date_to: str | None = None,
) -> dict[str, list[str]]:
    q = (
        select(distinct(CheckoutItem.product_name))
        .join(Invoice, CheckoutItem.invoice_id == Invoice.id)
        .where(Invoice.status == "paid")
    )
    q = apply_created_at_range(q, date_from, date_to, Invoice.created_at)
    rows = db.execute(q.order_by(CheckoutItem.product_name)).all()
    return {
        "products": _sorted_non_empty(rows),
        "sources": invoice_field_options(
            db, Invoice.source, date_from=date_from, date_to=date_to, paid_only=True
        ),
        "provinces": invoice_field_options(
            db, Invoice.customer_address, date_from=date_from, date_to=date_to, paid_only=True
        ),
    }


def commission_filter_options(
    db: Session,
    *,
    date_from: str | None = None,
    date_to: str | None = None,
) -> dict[str, list[str]]:
    q = (
        select(distinct(CheckoutItem.product_name))
        .join(Invoice, CheckoutItem.invoice_id == Invoice.id)
        .where(Invoice.status == "paid")
    )
    q = apply_created_at_range(q, date_from, date_to, Invoice.created_at)
    product_rows = db.execute(q.order_by(CheckoutItem.product_name)).all()
    return {
        "products": _sorted_non_empty(product_rows),
        "sources": invoice_field_options(
            db, Invoice.source, date_from=date_from, date_to=date_to, paid_only=True
        ),
    }


def pos_form_options(db: Session) -> dict[str, list[str]]:
    """POS checkout dropdowns from values already used in invoices."""
    return {
        "deliveryTypes": invoice_field_options(db, Invoice.delivery_type),
        "sources": invoice_field_options(db, Invoice.source),
        "paymentMethods": invoice_field_options(db, Invoice.payment_method),
        "addresses": invoice_field_options(db, Invoice.customer_address),
    }


def delivery_filter_options(
    db: Session,
    *,
    date_from: str | None = None,
    date_to: str | None = None,
) -> dict[str, list[str]]:
    return {
        "addresses": invoice_field_options(
            db, Invoice.customer_address, date_from=date_from, date_to=date_to
        ),
        "deliveryTypes": invoice_field_options(
            db, Invoice.delivery_type, date_from=date_from, date_to=date_to
        ),
        "statuses": invoice_field_options(
            db, Invoice.delivery_status, date_from=date_from, date_to=date_to
        ),
    }
