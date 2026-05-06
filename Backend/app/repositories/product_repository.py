from sqlalchemy import delete, or_, select, update
from sqlalchemy.orm import Session, joinedload

from app.models import Category, CheckoutItem, Finance, Product, ProductDamage, ProductStockAddition


def resolve_category_by_public_id(db: Session, raw_value: str | None) -> Category | None:
    if not raw_value:
        return None
    normalized = raw_value.strip()
    if not normalized:
        return None
    db_id = Category.from_public_id(normalized)
    if db_id is None:
        return None
    return db.get(Category, db_id)


def find_duplicate_product(db: Session, *, name: str, category_id: int, exclude_id: int | None = None) -> Product | None:
    stmt = select(Product).where(Product.name.ilike(name), Product.category_id == category_id)
    if exclude_id is not None:
        stmt = stmt.where(Product.id != exclude_id)
    return db.execute(stmt).scalar_one_or_none()


def list_products_query(db: Session, *, search: str | None, category: str | None):
    query = select(Product).options(joinedload(Product.category_rel)).join(Category, Product.category_id == Category.id, isouter=True)
    if search:
        keyword = search.strip()
        query = query.where(or_(Product.name.ilike(f"%{keyword}%"), Category.name.ilike(f"%{keyword}%")))
    if category:
        category_ids: list[int] = []
        for value in [item.strip() for item in category.split(",") if item.strip()]:
            db_id = Category.from_public_id(value)
            if db_id is not None:
                category_ids.append(db_id)
        query = query.where(Product.category_id.in_(category_ids)) if category_ids else query.where(Product.id == -1)
    return query


def adjust_category_product_count(db: Session, category_id: int | None, delta: int) -> None:
    if not category_id:
        return
    row = db.get(Category, category_id)
    if not row:
        return
    row.product_count = max(0, int(row.product_count or 0) + delta)


def create_product_record(db: Session, **kwargs) -> Product:
    row = Product(**kwargs)
    db.add(row)
    db.flush()
    return row


def ensure_finance_for_product(db: Session, product_id: int) -> None:
    if not db.execute(select(Finance).where(Finance.product_id == product_id)).scalar_one_or_none():
        db.add(Finance(product_id=product_id))


def delete_product_related_records(db: Session, product_id: int) -> None:
    db.execute(update(CheckoutItem).where(CheckoutItem.product_id == product_id).values(product_id=None))
    db.execute(delete(Finance).where(Finance.product_id == product_id))
    db.execute(delete(ProductStockAddition).where(ProductStockAddition.product_id == product_id))
    db.execute(delete(ProductDamage).where(ProductDamage.product_id == product_id))
