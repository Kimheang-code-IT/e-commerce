from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models import History, User
from app.services.auth_service import get_current_user, require_permission
from app.services.data_service import apply_created_at_range, apply_sort, list_response, paginate_query, parse_csv, to_iso

router = APIRouter(prefix="/histories", tags=["histories"], dependencies=[Depends(get_current_user)])


@router.get("")
def list_histories(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=200),
    search: str | None = None,
    action: str | None = None,
    dateFrom: str | None = None,
    dateTo: str | None = None,
    sortBy: str | None = None,
    sortOrder: str | None = Query(None, pattern="^(asc|desc)$"),
    _=Depends(require_permission("history:view")),
    db: Session = Depends(get_db),
):
    q = select(History, User).join(User, History.user_id == User.id)
    if search:
        keyword = search.strip()
        q = q.where(
            User.name.ilike(f"%{keyword}%")
            | History.description.ilike(f"%{keyword}%")
            | History.type_action.ilike(f"%{keyword}%")
        )
    actions = parse_csv(action)
    if actions:
        q = q.where(History.type_action.in_(actions))
    q = apply_created_at_range(q, dateFrom, dateTo, History.created_at)
    q = apply_sort(
        q,
        sortBy,
        sortOrder,
        {
            "id": History.id,
            "typeAction": History.type_action,
            "username": User.name,
            "date": History.created_at,
        },
    )
    rows, total = paginate_query(q, db, page, limit)
    data = [
        {
            "id": h.id,
            "typeAction": h.type_action,
            "username": u.name,
            "date": to_iso(h.created_at),
            "description": h.description,
            "metadata": {},
        }
        for h, u in rows
    ]
    return list_response(data, total)
