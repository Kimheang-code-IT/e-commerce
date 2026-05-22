"""Redis lock so only one container runs a scheduled job (multi backend replicas)."""

from __future__ import annotations

import logging

logger = logging.getLogger(__name__)


def try_acquire_scheduler_lock(name: str, *, ttl_seconds: int = 3600) -> bool:
    try:
        import redis

        from app.core.config import settings

        client = redis.from_url(settings.redis_url, decode_responses=True)
        acquired = client.set(f"ecom:schedlock:{name}", "1", nx=True, ex=ttl_seconds)
        return bool(acquired)
    except Exception as exc:
        logger.warning("Scheduler lock unavailable for %s: %s", name, exc)
        return True
