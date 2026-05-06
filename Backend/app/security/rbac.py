from __future__ import annotations

import json

from app.models import Role, User

ALIASES: dict[str, tuple[str, ...]] = {
    "role:view": ("settings:role-management:view",),
    "role:create": ("settings:role-management:update", "settings:role-management:edit"),
    "role:update": ("settings:role-management:update",),
    "role:delete": ("settings:role-management:update",),
    "user:view": ("settings:user-management:view",),
    "user:create": ("settings:user-management:update", "settings:user-management:edit"),
    "user:update": ("settings:user-management:update",),
    "user:delete": ("settings:user-management:update",),
}


def role_permission_tokens(role: Role | None) -> set[str]:
    if not role:
        return set()
    if role.name.lower() == "admin":
        return {"admin:*"}
    try:
        parsed = json.loads(role.page_access or "[]")
    except json.JSONDecodeError:
        return set()
    if not isinstance(parsed, list):
        return set()
    return {str(value) for value in parsed}


def user_has_permission(user: User, permission: str) -> bool:
    tokens = role_permission_tokens(getattr(user, "role_rel", None))
    if "admin:*" in tokens or permission in tokens:
        return True
    return any(alias in tokens for alias in ALIASES.get(permission, ()))


def user_has_role(user: User, role_name: str) -> bool:
    role = getattr(user, "role_rel", None)
    if not role:
        return False
    return role.name.lower() == role_name.lower()
