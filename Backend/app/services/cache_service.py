"""Redis response cache with prefix-based invalidation."""

from __future__ import annotations

import hashlib
import json
import logging
from collections.abc import Callable
from typing import Any

from app.core.config import settings
from app.core.redis_client import get_redis, redis_available

logger = logging.getLogger(__name__)

PREFIX_PRODUCTS = "cache:products:"
PREFIX_CATEGORIES = "cache:categories:"
PREFIX_DASHBOARD = "cache:dashboard:"
PREFIX_STOCK = "cache:stock:"

ALL_CHECKOUT_PREFIXES = (
    PREFIX_PRODUCTS,
    PREFIX_CATEGORIES,
    PREFIX_DASHBOARD,
    PREFIX_STOCK,
)


def _stable_key(prefix: str, parts: dict[str, Any] | None = None) -> str:
    if not parts:
        return prefix.rstrip(":") + ":all"
    raw = json.dumps(parts, sort_keys=True, default=str)
    digest = hashlib.sha256(raw.encode()).hexdigest()[:16]
    return f"{prefix}{digest}"


def get_cached(prefix: str, parts: dict[str, Any] | None = None) -> Any | None:
    if not redis_available():
        return None
    key = _stable_key(prefix, parts)
    try:
        raw = get_redis().get(key)
        if raw is None:
            return None
        return json.loads(raw)
    except Exception as exc:
        logger.warning("Cache get failed for %s: %s", key, exc)
        return None


def set_cached(prefix: str, value: Any, parts: dict[str, Any] | None = None) -> None:
    if not redis_available():
        return
    key = _stable_key(prefix, parts)
    try:
        get_redis().setex(key, settings.cache_ttl_seconds, json.dumps(value, default=str))
    except Exception as exc:
        logger.warning("Cache set failed for %s: %s", key, exc)


def cached_response(
    prefix: str,
    parts: dict[str, Any] | None,
    builder: Callable[[], Any],
) -> Any:
    hit = get_cached(prefix, parts)
    if hit is not None:
        return hit
    data = builder()
    set_cached(prefix, data, parts)
    return data


def _redis_up() -> bool:
    try:
        get_redis().ping()
        return True
    except Exception:
        return False


def invalidate_prefixes(*prefixes: str) -> int:
    if not _redis_up():
        return 0
    client = get_redis()
    deleted = 0
    for prefix in prefixes:
        cursor = 0
        while True:
            cursor, keys = client.scan(cursor=cursor, match=f"{prefix}*", count=200)
            if keys:
                deleted += int(client.delete(*keys))
            if cursor == 0:
                break
    if deleted:
        logger.info("Invalidated %s Redis cache key(s) for prefixes %s", deleted, prefixes)
    return deleted


def invalidate_after_checkout() -> int:
    return invalidate_prefixes(*ALL_CHECKOUT_PREFIXES)


def invalidate_products_and_dashboard() -> None:
    invalidate_prefixes(PREFIX_PRODUCTS, PREFIX_DASHBOARD, PREFIX_STOCK)


def invalidate_categories_and_dashboard() -> None:
    invalidate_prefixes(PREFIX_CATEGORIES, PREFIX_DASHBOARD)
