from __future__ import annotations

import secrets
from datetime import datetime, timedelta, timezone
from typing import Any

from jose import JWTError, jwt

from app.core.config import settings

ALGORITHM = "HS256"
TOKEN_TYPE_ACCESS = "access"
TOKEN_TYPE_REFRESH = "refresh"


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def build_token(
    *,
    subject: str,
    token_type: str,
    expires_delta: timedelta,
    extra_claims: dict[str, Any] | None = None,
    jti: str | None = None,
) -> tuple[str, str]:
    issued_at = _utc_now()
    token_jti = jti or secrets.token_hex(16)
    payload: dict[str, Any] = {
        "sub": subject,
        "type": token_type,
        "jti": token_jti,
        "iat": issued_at,
        "exp": issued_at + expires_delta,
    }
    if settings.jwt_issuer:
        payload["iss"] = settings.jwt_issuer
    if settings.jwt_audience:
        payload["aud"] = settings.jwt_audience
    if extra_claims:
        payload.update(extra_claims)
    return jwt.encode(payload, settings.secret_key, algorithm=ALGORITHM), token_jti


def create_access_token(subject: str, extra_claims: dict[str, Any] | None = None) -> str:
    token, _ = build_token(
        subject=subject,
        token_type=TOKEN_TYPE_ACCESS,
        expires_delta=timedelta(minutes=settings.access_token_expire_minutes),
        extra_claims=extra_claims,
    )
    return token


def create_refresh_token(subject: str, jti: str | None = None) -> tuple[str, str]:
    return build_token(
        subject=subject,
        token_type=TOKEN_TYPE_REFRESH,
        expires_delta=timedelta(days=settings.refresh_token_expire_days),
        jti=jti,
    )


def decode_token(token: str) -> dict[str, Any]:
    options = {"verify_aud": bool(settings.jwt_audience)}
    kwargs: dict[str, Any] = {"algorithms": [ALGORITHM], "options": options}
    if settings.jwt_audience:
        kwargs["audience"] = settings.jwt_audience
    if settings.jwt_issuer:
        kwargs["issuer"] = settings.jwt_issuer
    return jwt.decode(token, settings.secret_key, **kwargs)


def parse_bearer_token(token: str) -> dict[str, Any]:
    try:
        return decode_token(token)
    except JWTError as exc:
        raise ValueError("Invalid token") from exc
