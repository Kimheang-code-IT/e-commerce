from __future__ import annotations

from sqlalchemy import String, cast, func, or_, select
from sqlalchemy.orm import Session, selectinload

from app.models import Product, Reward, RewardProduct
from app.schemas.common import RewardCreatePayload, RewardUpdatePayload
from app.services.data_service import apply_created_at_range, apply_sort, to_iso


def serialize_reward_product(row: RewardProduct) -> dict:
    product = row.product
    return {
        "productId": int(row.product_id),
        "qty": int(row.qty or 1),
        "name": product.name if product else "",
        "image": product.image if product else "",
        "inStock": int(product.in_stock or 0) if product else 0,
        "outPrice": float(product.out_price or 0) if product else 0,
        "salePrice": float(product.out_price or 0) if product else 0,
        "categoryId": product.category_rel.public_id if product and product.category_rel else "",
        "category": product.category_rel.name if product and product.category_rel else "",
        "status": product.status if product else "active",
    }


def serialize_reward(row: Reward) -> dict:
    products = [serialize_reward_product(link) for link in (row.products or [])]
    names = [p["name"] for p in products if p.get("name")]
    return {
        "id": int(row.id),
        "name": row.name,
        "status": row.status or "active",
        "productIds": [p["productId"] for p in products],
        "productNames": ", ".join(names),
        "products": products,
        "createdAt": to_iso(row.created_at),
    }


def list_rewards_query(
    *,
    search: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    sort_by: str | None = None,
    sort_order: str | None = None,
    active_only: bool = False,
):
    q = select(Reward)
    if active_only:
        q = q.where(Reward.status == "active")
    if search:
        keyword = search.strip()
        q = q.where(
            or_(
                Reward.name.ilike(f"%{keyword}%"),
                cast(Reward.id, String).ilike(f"%{keyword}%"),
            )
        )
    q = apply_created_at_range(q, date_from, date_to, Reward.created_at)
    q = apply_sort(
        q,
        sort_by,
        sort_order,
        {
            "id": Reward.id,
            "name": Reward.name,
            "createdAt": Reward.created_at,
        },
    )
    return q.options(
        selectinload(Reward.products)
        .selectinload(RewardProduct.product)
        .selectinload(Product.category_rel)
    )


def paginate_rewards(db: Session, q, page: int, limit: int) -> tuple[list[Reward], int]:
    count_source = q.order_by(None).enable_eagerloads(False)
    try:
        total = db.scalar(select(func.count()).select_from(count_source.subquery())) or 0
    except Exception:
        total = db.scalar(select(func.count(Reward.id)).select_from(Reward)) or 0
    rows = db.scalars(q.offset((page - 1) * limit).limit(limit)).all()
    return rows, total


def _sync_reward_products(db: Session, reward: Reward, items: list) -> None:
    reward.products.clear()
    db.flush()
    for item in items:
        db.add(
            RewardProduct(
                reward_id=reward.id,
                product_id=int(item.productId),
                qty=int(item.qty or 1),
            )
        )


def load_reward(db: Session, reward_id: int) -> Reward | None:
    return db.scalars(
        select(Reward)
        .options(
            selectinload(Reward.products)
            .selectinload(RewardProduct.product)
            .selectinload(Product.category_rel)
        )
        .where(Reward.id == reward_id)
    ).first()


def create_reward(db: Session, body: RewardCreatePayload) -> Reward:
    row = Reward(name=body.name, status="active")
    db.add(row)
    db.flush()
    _sync_reward_products(db, row, body.products)
    db.flush()
    loaded = load_reward(db, row.id)
    if not loaded:
        raise RuntimeError("Failed to load created reward")
    return loaded


def update_reward(db: Session, reward_id: int, body: RewardUpdatePayload) -> Reward | None:
    row = db.get(Reward, reward_id)
    if not row:
        return None
    if body.name is not None:
        row.name = body.name
    if body.products is not None:
        _sync_reward_products(db, row, body.products)
    db.flush()
    return load_reward(db, reward_id)


def delete_reward(db: Session, reward_id: int) -> bool:
    row = db.get(Reward, reward_id)
    if not row:
        return False
    db.delete(row)
    return True
