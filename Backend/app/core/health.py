"""Dependency checks for load balancer / container health endpoints."""

from __future__ import annotations

from sqlalchemy import text

from app.core.config import settings
from app.core.database import engine
from app.core.redis_client import redis_available


def check_postgres() -> tuple[bool, str]:
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True, "ok"
    except Exception as exc:
        return False, str(exc)[:200]


def check_redis() -> tuple[bool, str]:
    if not settings.cache_enabled:
        return True, "skipped"
    if redis_available():
        return True, "ok"
    return False, "unavailable"


def run_health_checks() -> dict:
    db_ok, db_detail = check_postgres()
    redis_ok, redis_detail = check_redis()
    checks = {
        "database": {"status": "ok" if db_ok else "error", "detail": db_detail},
        "redis": {"status": "ok" if redis_ok else "error", "detail": redis_detail},
    }
    healthy = db_ok and redis_ok
    return {
        "status": "ok" if healthy else "degraded",
        "checks": checks,
    }
