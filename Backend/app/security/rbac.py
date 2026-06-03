from __future__ import annotations
import json
from app.models import Role, User

ALIASES: dict[str, tuple[str, ...]] = {
    # Category permissions
    "category:view": ("settings:category-management:view",),
    "category:create": ("settings:category-management:create",),
    "category:update": ("settings:category-management:update",),
    "category:delete": ("settings:category-management:delete",),
    # Supplier permissions
    "supplier:view": ("settings:supplier-management:view",),
    "supplier:create": ("settings:supplier-management:create",),
    "supplier:update": ("settings:supplier-management:update",),
    "supplier:delete": ("settings:supplier-management:delete",),
    # Product permissions
    "product:view": ("settings:product-management:view",),
    "product:create": ("settings:product-management:create",),
    "product:update": ("settings:product-management:update",),
    "product:delete": ("settings:product-management:delete",),
    "product:export": ("settings:product-management:export",),
    "product:adjust-stock": ("settings:product-management:adjust-stock",),
    "product:view-adjust-stock": ("settings:product-management:view-adjust-stock",),
    "product:add-damage": ("settings:product-management:add-damage",),
    "product:view-add-damage": ("settings:product-management:view-add-damage",),
    # POS permissions
    "pos:view": ("settings:pos-management:view",),
    "pos:checkout": ("settings:pos-management:checkout",),
    "pos:create": ("settings:pos-management:checkout",),
    "backup:manage": ("admin:*",),
    # Finance permissions
    "finance:view": ("settings:finance-management:view",),
    "finance:update": ("settings:finance-management:update",),
    # Report permissions
    "report:view": ("settings:report-management:view",),
    "report:export": ("settings:report-management:export",),
    # Delivery permissions
    "delivery:view": ("settings:delivery-management:view",),
    "delivery:update": ("settings:delivery-management:update",),
    "delivery:export": ("settings:delivery-management:export",),
    # History permissions
    "history:view": ("settings:history-management:view",),
    "history:export": ("settings:history-management:export",),
    # Commission permissions
    "commission:view": ("settings:commission-management:view",),
    "commission:export": ("settings:commission-management:export",),
    # Refund permissions
    "refund:view": ("settings:refund-management:view",),
    "refund:create": ("settings:refund-management:create",),
    "refund:delete": ("settings:refund-management:delete",),
    # dashboard permissions
    "dashboard:view": ("settings:dashboard-management:view",),
    "role:view": ("settings:role-management:view",),
    "role:create": ("settings:role-management:update",),
    "role:update": ("settings:role-management:update",),
    "role:delete": ("settings:role-management:update",),
    # User permissions
    "user:view": ("settings:user-management:view",),
    "user:create": ("settings:user-management:create",),
    "user:update": ("settings:user-management:update",),
    "user:delete": ("settings:user-management:delete",),
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
