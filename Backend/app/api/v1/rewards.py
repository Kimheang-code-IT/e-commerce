from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models import Product, Reward, User
from app.schemas.common import RewardCreatePayload, RewardUpdatePayload
from app.services.auth_service import get_current_user, require_any_permission, require_permission
from app.services.data_service import list_response, record_history
from app.services.reward_service import (
    create_reward,
    delete_reward,
    list_rewards_query,
    load_reward,
    paginate_rewards,
    serialize_reward,
    update_reward,
)
from app.shared.api_response import error_response
from app.shared.pagination_constants import MAX_LIST_PAGE_SIZE

router = APIRouter()


@router.get("/rewards")
def list_rewards(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=MAX_LIST_PAGE_SIZE),
    search: str | None = None,
    dateFrom: str | None = None,
    dateTo: str | None = None,
    sortBy: str | None = None,
    sortOrder: str | None = Query(None, pattern="^(asc|desc)$"),
    _: User = Depends(require_any_permission("product:view", "pos:view")),
    db: Session = Depends(get_db),
):
    q = list_rewards_query(
        search=search,
        date_from=dateFrom,
        date_to=dateTo,
        sort_by=sortBy,
        sort_order=sortOrder,
    )
    rows, total = paginate_rewards(db, q, page, limit)
    return list_response([serialize_reward(row) for row in rows], total)


@router.get("/rewards/pos")
def list_pos_rewards(
    _: User = Depends(require_permission("pos:view")),
    db: Session = Depends(get_db),
):
    q = list_rewards_query(active_only=True, sort_by="name", sort_order="asc")
    rows, _ = paginate_rewards(db, q, 1, MAX_LIST_PAGE_SIZE)
    return {"data": [serialize_reward(row) for row in rows]}


@router.post("/rewards")
def create_reward_route(
    body: RewardCreatePayload,
    current_user: User = Depends(get_current_user),
    _: User = Depends(require_permission("product:create")),
    db: Session = Depends(get_db),
):
    product_ids = [item.productId for item in body.products]
    found = db.execute(select(Product.id).where(Product.id.in_(product_ids))).scalars().all()
    missing = [pid for pid in product_ids if pid not in set(found)]
    if missing:
        return error_response(
            status.HTTP_400_BAD_REQUEST,
            f"Unknown product id(s): {', '.join(str(i) for i in missing)}",
            "BAD_REQUEST",
        )
    row = create_reward(db, body)
    record_history(db, current_user.id, "Create", f"Created reward '{row.name}'")
    db.commit()
    db.refresh(row)
    return {"data": serialize_reward(row)}


@router.put("/rewards/{item_id}")
def update_reward_route(
    item_id: int,
    body: RewardUpdatePayload,
    current_user: User = Depends(get_current_user),
    _: User = Depends(require_permission("product:update")),
    db: Session = Depends(get_db),
):
    if body.products is not None:
        product_ids = [item.productId for item in body.products]
        if not product_ids:
            return error_response(status.HTTP_400_BAD_REQUEST, "Select at least one product", "BAD_REQUEST")
        found = db.execute(select(Product.id).where(Product.id.in_(product_ids))).scalars().all()
        missing = [pid for pid in product_ids if pid not in set(found)]
        if missing:
            return error_response(
                status.HTTP_400_BAD_REQUEST,
                f"Unknown product id(s): {', '.join(str(i) for i in missing)}",
                "BAD_REQUEST",
            )
    row = update_reward(db, item_id, body)
    if not row:
        return error_response(status.HTTP_404_NOT_FOUND, "Not found", "NOT_FOUND")
    record_history(db, current_user.id, "Update", f"Updated reward '{row.name}'")
    db.commit()
    refreshed = load_reward(db, row.id) or row
    return {"data": serialize_reward(refreshed)}


@router.delete("/rewards/{item_id}")
def delete_reward_route(
    item_id: int,
    current_user: User = Depends(get_current_user),
    _: User = Depends(require_permission("product:delete")),
    db: Session = Depends(get_db),
):
    row = db.get(Reward, item_id)
    if not row:
        return error_response(status.HTTP_404_NOT_FOUND, "Not found", "NOT_FOUND")
    name = row.name
    delete_reward(db, item_id)
    record_history(db, current_user.id, "Delete", f"Deleted reward '{name}'")
    db.commit()
    return {"message": "Reward deleted"}
