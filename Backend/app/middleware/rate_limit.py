"""Redis-backed rate limits for sensitive endpoints."""

from __future__ import annotations

import logging

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

from app.core.config import settings
from app.core.redis_client import get_redis

logger = logging.getLogger(__name__)

_LIMITED_SUFFIXES = (
    "/auth/login",
    "/pos/checkout",
    "/invoices/checkout",
)


def _client_ip(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    if request.client:
        return request.client.host
    return "unknown"


class RateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if not settings.rate_limit_enabled or request.method != "POST":
            return await call_next(request)

        path = request.url.path
        if not any(path.endswith(suffix) for suffix in _LIMITED_SUFFIXES):
            return await call_next(request)

        limit = (
            settings.rate_limit_checkout_per_minute
            if "checkout" in path
            else settings.rate_limit_login_per_minute
        )
        window = 60
        ip = _client_ip(request)
        key = f"rl:{ip}:{path}"

        try:
            client = get_redis()
            count = int(client.incr(key))
            if count == 1:
                client.expire(key, window)
            if count > limit:
                return JSONResponse(
                    status_code=429,
                    content={
                        "message": "Too many requests. Please wait and try again.",
                        "code": "RATE_LIMITED",
                    },
                )
        except Exception as exc:
            logger.warning("Rate limit skipped (Redis unavailable): %s", exc)

        return await call_next(request)
