"""Redis lock so only one container runs a scheduled job (multi backend replicas)."""

from __future__ import annotations

import logging

from app.core.config import settings
from app.core.redis_client import get_redis

logger = logging.getLogger(__name__)


def _lock_required() -> bool:
    """Strict locking when multiple API replicas or production without Redis is unsafe."""
    if settings.backend_replicas > 1:
        return True
    return settings.is_production


def try_acquire_scheduler_lock(name: str, *, ttl_seconds: int = 3600) -> bool:
    if not settings.cache_enabled:
        if _lock_required():
            logger.warning(
                "Scheduler lock skipped for %s: CACHE_ENABLED=false but strict lock is required",
                name,
            )
            return False
        return True
    try:
        client = get_redis()
        acquired = client.set(f"ecom:schedlock:{name}", "1", nx=True, ex=ttl_seconds)
        return bool(acquired)
    except Exception as exc:
        logger.warning("Scheduler lock unavailable for %s: %s", name, exc)
        if _lock_required():
            return False
        return True
