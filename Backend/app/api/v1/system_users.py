from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.core.database import get_db
from app.core.security import get_password_hash
from app.models import Role, User
from app.schemas.common import SystemUserCreatePayload, SystemUserUpdatePayload
from app.services.auth_service import get_current_user, require_permission
from app.services.data_service import apply_sort, list_response, paginate_query, serialize_user, record_history
from app.shared.api_response import error_response

router = APIRouter(prefix="/users", tags=["users"], dependencies=[Depends(get_current_user)])


def _resolve_role(db: Session, role_name: str) -> Role | None:
    return db.execute(select(Role).where(Role.name.ilike(role_name.strip()))).scalar_one_or_none()


@router.get("")
def list_users(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=200),
    search: str | None = None,
    dateFrom: str | None = None,
    dateTo: str | None = None,
    sortBy: str | None = None,
    sortOrder: str | None = Query(None, pattern="^(asc|desc)$"),
    _: User = Depends(require_permission("user:view")),
    db: Session = Depends(get_db),
):
    q = select(User).options(joinedload(User.role_rel))
    if search:
        keyword = search.strip()
        q = q.where(User.name.ilike(f"%{keyword}%") | User.email.ilike(f"%{keyword}%"))
    q = apply_sort(q, sortBy, sortOrder, {"id": User.id, "name": User.name, "email": User.email})
    rows, total = paginate_query(q, db, page, limit)
    return list_response([serialize_user(row[0]) for row in rows], total)


@router.post("")
def create_user(
    payload: SystemUserCreatePayload,
    current_user: User = Depends(get_current_user),
    _: User = Depends(require_permission("user:create")),
    db: Session = Depends(get_db),
):
    existing = db.execute(select(User).where(User.email.ilike(payload.email))).scalar_one_or_none()
    if existing:
        return error_response(status.HTTP_409_CONFLICT, "Email already exists", "CONFLICT")
    role = _resolve_role(db, payload.role)
    if not role:
        return error_response(status.HTTP_400_BAD_REQUEST, "Unknown role", "BAD_REQUEST")
    row = User(
        name=payload.name,
        email=payload.email,
        password_hash=get_password_hash(payload.password),
        role_id=role.id,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    record_history(db, current_user.id, "Create", f"Created user '{row.name}'")
    db.commit()
    row_out = db.execute(select(User).options(joinedload(User.role_rel)).where(User.id == row.id)).scalar_one()
    return {"data": serialize_user(row_out)}


@router.put("/{user_id}")
def update_user(
    user_id: int,
    payload: SystemUserUpdatePayload,
    current_user: User = Depends(get_current_user),
    _: User = Depends(require_permission("user:update")),
    db: Session = Depends(get_db),
):
    row = db.get(User, user_id)
    if not row:
        return error_response(status.HTTP_404_NOT_FOUND, "Not found", "NOT_FOUND")
    if payload.email is not None and payload.email != row.email:
        duplicate = db.execute(select(User).where(User.email.ilike(payload.email), User.id != row.id)).scalar_one_or_none()
        if duplicate:
            return error_response(status.HTTP_409_CONFLICT, "Email already exists", "CONFLICT")
    if payload.name is not None:
        row.name = payload.name
    if payload.email is not None:
        row.email = payload.email
    if payload.role is not None:
        role = _resolve_role(db, payload.role)
        if not role:
            return error_response(status.HTTP_400_BAD_REQUEST, "Unknown role", "BAD_REQUEST")
        row.role_id = role.id
    if payload.password:
        row.password_hash = get_password_hash(payload.password)
    db.commit()
    db.refresh(row)
    record_history(db, current_user.id, "Update", f"Updated user '{row.name}'")
    db.commit()
    row_out = db.execute(select(User).options(joinedload(User.role_rel)).where(User.id == row.id)).scalar_one()
    return {"data": serialize_user(row_out)}


@router.delete("/{user_id}")
def delete_user(
    user_id: int,
    current_user: User = Depends(get_current_user),
    _: User = Depends(require_permission("user:delete")),
    db: Session = Depends(get_db),
):
    row = db.get(User, user_id)
    if not row:
        return error_response(status.HTTP_404_NOT_FOUND, "Not found", "NOT_FOUND")
    if row.id == current_user.id:
        return error_response(status.HTTP_409_CONFLICT, "Cannot delete current user", "CONFLICT")
    
    user_name = row.name
    db.delete(row)
    db.commit()
    record_history(db, current_user.id, "Delete", f"Deleted user '{user_name}'")
    db.commit()
    return {"message": "User deleted"}
