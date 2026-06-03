import json

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.security import get_password_hash
from app.models import Role, User

ADMIN_ROLE_NAME = "admin"
ADMIN_PAGE_ACCESS = ["admin:*"]


def user_count(db: Session) -> int:
    return int(db.scalar(select(func.count()).select_from(User)) or 0)


def needs_initial_setup(db: Session) -> bool:
    return user_count(db) == 0


def ensure_admin_role(db: Session) -> Role | None:
    role = db.execute(select(Role).where(Role.name.ilike(ADMIN_ROLE_NAME))).scalar_one_or_none()
    if role is not None:
        return role
    role = Role(name=ADMIN_ROLE_NAME, page_access=json.dumps(ADMIN_PAGE_ACCESS))
    db.add(role)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        role = db.execute(select(Role).where(Role.name.ilike(ADMIN_ROLE_NAME))).scalar_one_or_none()
    else:
        db.refresh(role)
    return role


def bootstrap_admin_user(db: Session, *, name: str, email: str, password: str) -> User:
    if not needs_initial_setup(db):
        raise ValueError("SETUP_ALREADY_COMPLETE")

    role = ensure_admin_role(db)
    if role is None:
        raise ValueError("ADMIN_ROLE_UNAVAILABLE")

    existing = db.execute(select(User).where(User.email.ilike(email))).scalar_one_or_none()
    if existing:
        raise ValueError("EMAIL_EXISTS")

    user = User(
        name=name,
        email=email,
        password_hash=get_password_hash(password),
        role_id=role.id,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user
