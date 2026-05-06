from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.models import TokenSession, User


def get_user_by_email(db: Session, email: str) -> User | None:
    stmt = select(User).options(joinedload(User.role_rel)).where(User.email.ilike(email))
    return db.execute(stmt).scalar_one_or_none()


def get_user_by_id(db: Session, user_id: int) -> User | None:
    stmt = select(User).options(joinedload(User.role_rel)).where(User.id == user_id)
    return db.execute(stmt).scalar_one_or_none()


def create_refresh_session(db: Session, *, user_id: int, refresh_jti: str, expires_at: datetime) -> TokenSession:
    TokenSession.__table__.create(bind=db.get_bind(), checkfirst=True)
    session = TokenSession(user_id=user_id, refresh_jti=refresh_jti, expires_at=expires_at)
    db.add(session)
    db.flush()
    return session


def get_refresh_session(db: Session, refresh_jti: str) -> TokenSession | None:
    stmt = select(TokenSession).where(TokenSession.refresh_jti == refresh_jti)
    return db.execute(stmt).scalar_one_or_none()


def revoke_refresh_session(db: Session, refresh_jti: str) -> None:
    session = get_refresh_session(db, refresh_jti)
    if session:
        session.revoked = True


def revoke_all_user_sessions(db: Session, user_id: int) -> int:
    stmt = select(TokenSession).where(TokenSession.user_id == user_id, TokenSession.revoked.is_(False))
    sessions = db.execute(stmt).scalars().all()
    for session in sessions:
        session.revoked = True
    return len(sessions)


def is_refresh_session_active(session: TokenSession | None) -> bool:
    if not session or session.revoked:
        return False
    now = datetime.now(timezone.utc)
    expires_at = session.expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    return expires_at > now
