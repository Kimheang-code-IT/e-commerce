from fastapi import APIRouter, Depends, Header, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models import User
from app.schemas.common import AuthLoginPayload, AuthLoginResponse
from app.services.auth_service import (
    login_user,
    logout_user_sessions,
    rotate_refresh_token,
    user_payload,
)
from app.dependencies.auth import get_current_user
from app.shared.api_response import error_response
from app.services.data_service import record_history

router = APIRouter(prefix="/auth", tags=["auth"])


from app.utils.timezone import cambodia_now


@router.post("/login", response_model=AuthLoginResponse)
def login(payload: AuthLoginPayload, db: Session = Depends(get_db)):
    try:
        auth_data = login_user(db, email=payload.email, password=payload.password)
        # Record login history and update last_login
        user = db.query(User).filter(User.email == payload.email).first()
        if user:
            user.last_login = cambodia_now()
            record_history(db, user.id, "Login", f"User logged in ({user.email})")
            db.commit()
    except Exception:
        return error_response(status.HTTP_401_UNAUTHORIZED, "Invalid credentials", "UNAUTHORIZED")
    return {"success": True, "message": "Login successful", "data": auth_data}


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
    record_history(db, user.id, "Logout", f"User logged out ({user.email})")
    db.commit()
    return {"data": {"ok": True, "revokedSessions": revoked}}
