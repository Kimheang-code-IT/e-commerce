from __future__ import annotations
from datetime import datetime, timedelta, timezone
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from app.core.config import settings
from app.repositories.auth_repository import (
	create_refresh_session,
	get_refresh_session,
	get_user_by_email,
	get_user_by_id,
	is_refresh_session_active,
	revoke_all_user_sessions,
	revoke_refresh_session,
)
from app.security import (
	TOKEN_TYPE_REFRESH,
	create_access_token,
	create_refresh_token,
	parse_bearer_token,
	role_permission_tokens,
	verify_password,
)
from app.dependencies.auth import get_current_user, require_permission, require_role


def _refresh_expiry_utc() -> datetime:
	return datetime.now(timezone.utc) + timedelta(days=settings.refresh_token_expire_days)


def authenticate_user(db: Session, *, email: str, password: str):
	user = get_user_by_email(db, email)
	if not user or not verify_password(password, user.password_hash):
		raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
	return user


def issue_token_pair(db: Session, user_id: int, role_name: str) -> dict[str, str]:
	access_token = create_access_token(str(user_id), {"role": role_name})
	refresh_token, refresh_jti = create_refresh_token(str(user_id))
	create_refresh_session(db, user_id=user_id, refresh_jti=refresh_jti, expires_at=_refresh_expiry_utc())
	db.commit()
	return {"accessToken": access_token, "refreshToken": refresh_token}


def login_user(db: Session, *, email: str, password: str) -> dict:
	user = authenticate_user(db, email=email, password=password)
	role_name = user.role_rel.name if user.role_rel else ""
	tokens = issue_token_pair(db, user.id, role_name)
	return {
		"token": tokens["accessToken"],
		"refreshToken": tokens["refreshToken"],
		"user": user_payload(user),
	}


def rotate_refresh_token(db: Session, refresh_token: str) -> tuple[dict[str, str], int]:
	payload = parse_bearer_token(refresh_token)
	if payload.get("type") != TOKEN_TYPE_REFRESH:
		raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token type")
	jti = payload.get("jti")
	sub = payload.get("sub")
	if not jti or not sub:
		raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token payload")

	session = get_refresh_session(db, str(jti))
	if not is_refresh_session_active(session):
		raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token expired or revoked")
	revoke_refresh_session(db, str(jti))

	user_id = int(sub)
	user = get_user_by_id(db, user_id)
	if not user:
		raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
	role_name = user.role_rel.name if user.role_rel else ""

	access_token = create_access_token(str(user_id), {"role": role_name})
	next_refresh, next_jti = create_refresh_token(str(user_id))
	create_refresh_session(db, user_id=user_id, refresh_jti=next_jti, expires_at=_refresh_expiry_utc())
	db.commit()
	return {"accessToken": access_token, "refreshToken": next_refresh}, user_id


def logout_user_sessions(db: Session, user_id: int) -> int:
	revoked_count = revoke_all_user_sessions(db, user_id)
	db.commit()
	return revoked_count


def user_payload(user) -> dict:
	role_name = user.role_rel.name if user.role_rel else ""
	return {
		"id": user.id,
		"name": user.name,
		"email": user.email,
		"avatar": "",
		"role": role_name,
		"pageAccess": sorted(role_permission_tokens(user.role_rel)),
	}
