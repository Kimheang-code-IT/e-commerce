"""Shared Redis connection for cache and Celery idempotency keys."""

from __future__ import annotations

import logging
from functools import lru_cache
from typing import TYPE_CHECKING

import redis

from app.core.config import settings

if TYPE_CHECKING:
    from redis import Redis

logger = logging.getLogger(__name__)


@lru_cache
def get_redis() -> Redis:
    client = redis.from_url(
        settings.redis_url,
        decode_responses=True,
        socket_connect_timeout=5,
        socket_timeout=5,
    )
    try:
        client.ping()
    except redis.RedisError as exc:
        logger.warning("Redis ping failed: %s", exc)
    return client


def redis_available() -> bool:
    if not settings.cache_enabled:
        return False
    try:
        return bool(get_redis().ping())
    except Exception:
        return False
