import json

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models import Role, User
from app.schemas.common import SystemRoleCreatePayload, SystemRoleUpdatePayload
from app.services.auth_service import get_current_user, require_permission
from app.services.data_service import apply_sort, list_response, paginate_query, serialize_role, record_history
from app.shared.api_response import error_response

router = APIRouter(prefix="/roles", tags=["roles"], dependencies=[Depends(get_current_user)])


def _page_access_json(items: list[str]) -> str:
    cleaned = [item.strip() for item in items if item.strip()]
    return json.dumps(cleaned)


@router.get("")
def list_roles(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=200),
    search: str | None = None,
    sortBy: str | None = None,
    sortOrder: str | None = Query(None, pattern="^(asc|desc)$"),
    _: User = Depends(require_permission("role:view")),
    db: Session = Depends(get_db),
):
    q = select(Role)
    if search:
        q = q.where(Role.name.ilike(f"%{search.strip()}%"))
    q = apply_sort(q, sortBy, sortOrder, {"id": Role.id, "name": Role.name})
    rows, total = paginate_query(q, db, page, limit)
    return list_response([serialize_role(row[0]) for row in rows], total)


@router.post("")
def create_role(
    payload: SystemRoleCreatePayload,
    current_user: User = Depends(get_current_user),
    _: User = Depends(require_permission("role:create")),
    db: Session = Depends(get_db),
):
    existing = db.execute(select(Role).where(Role.name.ilike(payload.name))).scalar_one_or_none()
    if existing:
        return error_response(status.HTTP_409_CONFLICT, "Role name already exists", "CONFLICT")
    row = Role(name=payload.name, page_access=_page_access_json(payload.pageAccess))
    db.add(row)
    db.commit()
    db.refresh(row)
    record_history(db, current_user.id, "Create", f"Created role '{row.name}'")
    db.commit()
    return {"data": serialize_role(row)}


@router.put("/{role_id}")
def update_role(
    role_id: int,
    payload: SystemRoleUpdatePayload,
    current_user: User = Depends(get_current_user),
    _: User = Depends(require_permission("role:update")),
    db: Session = Depends(get_db),
):
    row = db.get(Role, role_id)
    if not row:
        return error_response(status.HTTP_404_NOT_FOUND, "Not found", "NOT_FOUND")
    if payload.name is not None and payload.name != row.name:
        duplicate = db.execute(select(Role).where(Role.name.ilike(payload.name), Role.id != row.id)).scalar_one_or_none()
        if duplicate:
            return error_response(status.HTTP_409_CONFLICT, "Role name already exists", "CONFLICT")
        row.name = payload.name
    if payload.pageAccess is not None:
        row.page_access = _page_access_json(payload.pageAccess)
    db.commit()
    db.refresh(row)
    record_history(db, current_user.id, "Update", f"Updated role '{row.name}'")
    db.commit()
    return {"data": serialize_role(row)}


@router.delete("/{role_id}")
def delete_role(
    role_id: int,
    current_user: User = Depends(get_current_user),
    _: User = Depends(require_permission("role:delete")),
    db: Session = Depends(get_db),
):
    row = db.get(Role, role_id)
    if not row:
        return error_response(status.HTTP_404_NOT_FOUND, "Not found", "NOT_FOUND")
    role_in_use = db.scalar(select(User.id).where(User.role_id == row.id).limit(1))
    if role_in_use is not None:
        return error_response(status.HTTP_409_CONFLICT, "Role is assigned to users", "CONFLICT")
    
    role_name = row.name
    db.delete(row)
    db.commit()
    record_history(db, current_user.id, "Delete", f"Deleted role '{role_name}'")
    db.commit()
    return {"message": "Role deleted"}
