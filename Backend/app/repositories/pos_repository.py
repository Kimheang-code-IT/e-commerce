from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Invoice, Product


def get_products_by_ids(db: Session, ids: list[int]) -> list[Product]:
    if not ids:
        return []
    return db.scalars(select(Product).where(Product.id.in_(ids))).all()


def next_invoice_no(db: Session) -> str:
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
