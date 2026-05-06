from typing import Any

from app.security import create_access_token as security_create_access_token
from app.security import get_password_hash, verify_password


def create_access_token(subject: str, extra_claims: dict[str, Any] | None = None) -> str:
    return security_create_access_token(subject, extra_claims)
