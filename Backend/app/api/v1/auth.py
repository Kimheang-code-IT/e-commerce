from fastapi import APIRouter, Depends, Header, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models import User
from app.schemas.common import AuthLoginPayload
from app.services.auth_app_service import (
    authenticate_user,
    issue_token_pair,
    logout_user_sessions,
    rotate_refresh_token,
    user_payload,
)
from app.services.auth_service import get_current_user
from app.shared.api_response import error_response

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login")
def login(payload: AuthLoginPayload, db: Session = Depends(get_db)):
    try:
        user = authenticate_user(db, email=payload.email, password=payload.password)
    except Exception:
        return error_response(status.HTTP_401_UNAUTHORIZED, "Invalid credentials", "UNAUTHORIZED")
    role_name = user.role_rel.name if user.role_rel else ""
    tokens = issue_token_pair(db, user.id, role_name)
    payload_user = user_payload(user)
    # Keep legacy keys while introducing refresh token support.
    return {
        "token": tokens["accessToken"],
        "refreshToken": tokens["refreshToken"],
        "user": payload_user,
        "data": {"token": tokens["accessToken"], "refreshToken": tokens["refreshToken"], "user": payload_user},
    }


@router.post("/refresh")
def refresh(refreshToken: str | None = Header(default=None), db: Session = Depends(get_db)):
    if not refreshToken:
        return error_response(status.HTTP_400_BAD_REQUEST, "Missing refresh token", "BAD_REQUEST")
    try:
        tokens, _ = rotate_refresh_token(db, refreshToken)
    except Exception:
        return error_response(status.HTTP_401_UNAUTHORIZED, "Invalid refresh token", "UNAUTHORIZED")
    return {"data": {"token": tokens["accessToken"], "refreshToken": tokens["refreshToken"]}}


@router.get("/me")
def me(user: User = Depends(get_current_user)):
    return {"user": user_payload(user)}


@router.post("/logout")
def logout(user=Depends(get_current_user), db: Session = Depends(get_db)):
    revoked = logout_user_sessions(db, user.id)
    return {"data": {"ok": True, "revokedSessions": revoked}}
