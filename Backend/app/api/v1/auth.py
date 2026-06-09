from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models import User
from app.schemas.common import AuthLoginPayload, AuthLoginResponse, SetupBootstrapPayload
from app.services.auth_service import (
    login_user,
    logout_user_sessions,
    rotate_refresh_token,
    user_payload,
)
from app.dependencies.auth import get_current_user
from app.shared.api_response import error_response
from app.services.data_service import record_history
from app.services.setup_service import (
    ADMIN_ROLE_NAME,
    bootstrap_admin_user,
    needs_initial_setup,
    user_count,
)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.get("/setup/status")
def setup_status(db: Session = Depends(get_db)):
    count = user_count(db)
    return {
        "data": {
            "needsSetup": count == 0,
            "userCount": count,
        }
    }


@router.post("/setup")
def setup_initial_admin(payload: SetupBootstrapPayload, db: Session = Depends(get_db)):
    if not needs_initial_setup(db):
        return error_response(
            status.HTTP_409_CONFLICT,
            "Initial setup already completed",
            "SETUP_COMPLETE",
        )
    try:
        user = bootstrap_admin_user(
            db,
            name=payload.name,
            email=payload.email,
            password=payload.password,
        )
    except ValueError as exc:
        code = str(exc)
        if code == "EMAIL_EXISTS":
            return error_response(status.HTTP_409_CONFLICT, "Email already exists", "CONFLICT")
        if code == "ADMIN_ROLE_UNAVAILABLE":
            return error_response(
                status.HTTP_500_INTERNAL_SERVER_ERROR,
                "Could not create admin role",
                "INTERNAL_ERROR",
            )
        return error_response(status.HTTP_409_CONFLICT, "Initial setup already completed", "SETUP_COMPLETE")
    return {
        "success": True,
        "message": "Admin account created. You can log in now.",
        "data": {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "role": ADMIN_ROLE_NAME,
        },
    }


@router.post("/login", response_model=AuthLoginResponse)
def login(payload: AuthLoginPayload, db: Session = Depends(get_db)):
    try:
        auth_data = login_user(db, email=payload.email, password=payload.password)
    except HTTPException as exc:
        if exc.status_code == status.HTTP_401_UNAUTHORIZED:
            return error_response(status.HTTP_401_UNAUTHORIZED, "Invalid credentials", "UNAUTHORIZED")
        raise
    except Exception:
        return error_response(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            "Login failed",
            "INTERNAL_ERROR",
        )
    return {"success": True, "message": "Login successful", "data": auth_data}


@router.post("/refresh")
def refresh(refreshToken: str | None = Header(default=None), db: Session = Depends(get_db)):
    if not refreshToken:
        return error_response(status.HTTP_400_BAD_REQUEST, "Missing refresh token", "BAD_REQUEST")
    try:
        tokens, _ = rotate_refresh_token(db, refreshToken)
    except HTTPException as exc:
        if exc.status_code == status.HTTP_401_UNAUTHORIZED:
            return error_response(status.HTTP_401_UNAUTHORIZED, "Invalid refresh token", "UNAUTHORIZED")
        raise
    except Exception:
        return error_response(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            "Token refresh failed",
            "INTERNAL_ERROR",
        )
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
