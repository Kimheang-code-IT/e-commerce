from sqlalchemy import select, text
from sqlalchemy.orm import Session

from app.models import Invoice, Product

_INVOICE_NO_LOCK_KEY = 424242


def get_products_by_ids(db: Session, ids: list[int]) -> list[Product]:
    if not ids:
        return []
    return db.scalars(select(Product).where(Product.id.in_(ids))).all()


def get_products_by_ids_for_update(db: Session, ids: list[int]) -> list[Product]:
    """Row locks prevent concurrent checkout overselling the same SKU."""
    if not ids:
        return []
    return db.scalars(
        select(Product).where(Product.id.in_(ids)).with_for_update()
    ).all()


def next_invoice_no(db: Session) -> str:
    """Allocate next DNS invoice number inside a transaction-scoped advisory lock."""
    db.execute(text("SELECT pg_advisory_xact_lock(:k)"), {"k": _INVOICE_NO_LOCK_KEY})
    latest = db.scalars(
        select(Invoice.invoice_no)
        .where(Invoice.invoice_no.like("DNS-%"))
        .order_by(Invoice.invoice_no.desc())
        .limit(1)
    ).first()
    next_num = 1
    if latest:
        try:
            next_num = int(str(latest).split("-", 1)[1]) + 1
        except (ValueError, IndexError):
            next_num = 1
    return f"DNS-{next_num:010d}"
