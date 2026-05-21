import json
import logging
import time
import uuid
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from app.middleware.rate_limit import RateLimitMiddleware
from app.middleware.security_headers import SecurityHeadersMiddleware
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.api.v1.routes import router as api_router
from app.core.config import settings
from app.core.database import Base, SessionLocal, engine
from app.core.logging_config import setup_logging
from app.core.security import get_password_hash
from app.core.scheduler import start_scheduler, shutdown_scheduler
from app.models import Role, User

setup_logging()
logger = logging.getLogger(__name__)
app = FastAPI(
    title=settings.app_name,
    docs_url="/docs" if settings.api_docs_enabled and settings.APP_ENV.lower() != "production" else None,
    redoc_url="/redoc" if settings.api_docs_enabled and settings.APP_ENV.lower() != "production" else None,
    openapi_url="/openapi.json" if settings.api_docs_enabled and settings.APP_ENV.lower() != "production" else None,
)

cors_origins = [origin.strip() for origin in settings.cors_origins.split(",") if origin.strip()]
if settings.APP_ENV.lower() == "production" and "*" in cors_origins:
    raise ValueError("Wildcard CORS is not allowed in production")

# Private LAN / localhost with any port (phones on Wi-Fi, dynamic DHCP IP per machine).
_LAN_ORIGIN_REGEX = (
    r"https?://(localhost|127\.0\.0\.1)(:\d+)?"
    r"|https?://(192\.168\.\d{1,3}\.\d{1,3}|10\.\d{1,3}\.\d{1,3}\.\d{1,3}"
    r"|172\.(?:1[6-9]|2\d|3[0-1])\.\d{1,3}\.\d{1,3})(:\d+)?"
)

_cors_kwargs: dict = {
    "allow_credentials": True,
    "allow_methods": ["*"],
    "allow_headers": ["*"],
}
if settings.CORS_ALLOW_LAN:
    _cors_kwargs["allow_origins"] = cors_origins
    _cors_kwargs["allow_origin_regex"] = _LAN_ORIGIN_REGEX
else:
    _cors_kwargs["allow_origins"] = cors_origins

app.add_middleware(CORSMiddleware, **_cors_kwargs)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(RateLimitMiddleware)


def init_db() -> None:
    """Create tables from SQLAlchemy models (aligned with `e-commerce.sql`)."""
    Base.metadata.create_all(bind=engine)


def _legacy_admin_email_tuple(raw: str | None) -> tuple[str, ...]:
    if not (raw and raw.strip()):
        return ()
    return tuple(part.strip() for part in raw.split(",") if part.strip())


def ensure_default_admin() -> None:
    """Ensure the `admin` role and a full-access superuser exist.

    Credentials must come from settings (environment / ``Backend/.env``); see ``DEFAULT_ADMIN_*`` in config.

    Role name ``admin`` grants every permission (``admin:*`` in RBAC). Legacy addresses in
    ``DEFAULT_ADMIN_LEGACY_EMAILS`` are migrated to ``DEFAULT_ADMIN_EMAIL`` when possible.
    """
    if not settings.DEFAULT_ADMIN_SEED_ENABLED:
        logger.info("DEFAULT_ADMIN_SEED_ENABLED is false; skipping default admin seed")
        return

    admin_email = (settings.DEFAULT_ADMIN_EMAIL or "").strip()
    admin_password = settings.DEFAULT_ADMIN_PASSWORD or ""
    if not admin_email or not admin_password:
        logger.warning(
            "Default admin seed skipped: set DEFAULT_ADMIN_EMAIL and DEFAULT_ADMIN_PASSWORD in the environment"
        )
        return

    admin_role_name = "admin"
    admin_name = (settings.DEFAULT_ADMIN_NAME or "Admin").strip() or "Admin"
    legacy_admin_emails = _legacy_admin_email_tuple(settings.DEFAULT_ADMIN_LEGACY_EMAILS)

    with SessionLocal() as db:
        role = db.execute(select(Role).where(Role.name.ilike(admin_role_name))).scalar_one_or_none()
        if role is None:
            role = Role(name=admin_role_name, page_access=json.dumps(["admin:*"]))
            db.add(role)
            try:
                db.commit()
            except IntegrityError:
                db.rollback()
                role = db.execute(select(Role).where(Role.name.ilike(admin_role_name))).scalar_one_or_none()
            else:
                db.refresh(role)

        if role is None:
            logger.error("Unable to ensure admin role exists")
            return

        user = db.execute(select(User).where(User.email.ilike(admin_email))).scalar_one_or_none()
        if user is not None:
            if user.role_id != role.id:
                user.role_id = role.id
                db.commit()
                logger.info("Attached existing user %s to admin role", admin_email)
            return

        for legacy in legacy_admin_emails:
            legacy_user = db.execute(select(User).where(User.email.ilike(legacy))).scalar_one_or_none()
            if legacy_user is None:
                continue
            legacy_user.email = admin_email
            legacy_user.name = admin_name
            legacy_user.password_hash = get_password_hash(admin_password)
            legacy_user.role_id = role.id
            try:
                db.commit()
            except IntegrityError:
                db.rollback()
                logger.warning(
                    "Could not migrate legacy admin %s (target email may already exist); remove duplicate manually",
                    legacy,
                )
            else:
                logger.info("Migrated legacy admin %s -> %s", legacy, admin_email)
            return

        user = User(
            name=admin_name,
            email=admin_email,
            password_hash=get_password_hash(admin_password),
            role_id=role.id,
        )
        db.add(user)
        try:
            db.commit()
        except IntegrityError:
            db.rollback()
        else:
            logger.info("Seeded default admin user: %s", admin_email)


@app.middleware("http")
async def trace_id_middleware(request: Request, call_next):
    trace_id = str(uuid.uuid4())
    request.state.trace_id = trace_id
    start = time.time()
    response = await call_next(request)
    response.headers["X-Trace-Id"] = trace_id
    response.headers["X-Process-Time"] = str(time.time() - start)
    return response


@app.exception_handler(Exception)
async def global_error_handler(request: Request, exc: Exception):
    logger.exception("Unhandled exception on %s %s", request.method, request.url.path)
    error_payload = None
    if settings.APP_DEBUG and not settings.is_production:
        error_payload = {"exception": [str(exc)]}

    return JSONResponse(
        status_code=500,
        content={
            "message": "Internal server error",
            "code": "INTERNAL_ERROR",
            "traceId": getattr(request.state, "trace_id", None),
            "errors": error_payload,
        },
    )

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get(f"{settings.api_prefix}/health")
def api_health():
    return {"status": "ok"}


@app.on_event("startup")
def on_startup():
    init_db()
    ensure_default_admin()
    start_scheduler()
    lan_ip = (settings.HOST_LAN_IP or "").strip()
    lan_port = (settings.PUBLIC_HTTP_PORT or "8080").strip()
    if lan_ip:
        logger.info("LAN access (Wi-Fi): http://%s:%s/", lan_ip, lan_port)
    elif settings.CORS_ALLOW_LAN:
        logger.info(
            "LAN mode: open http://<this-PC-LAN-IP>:%s/ on Wi-Fi (IP is detected automatically; CORS allows any private LAN origin)",
            lan_port,
        )


@app.on_event("shutdown")
def on_shutdown():
    shutdown_scheduler()


app.include_router(api_router, prefix=settings.api_prefix)

_upload_root = Path(__file__).resolve().parent.parent / "uploads"
_products_dir = _upload_root / "products"
_invoices_dir = _upload_root / "invoices"
_products_dir.mkdir(parents=True, exist_ok=True)
_invoices_dir.mkdir(parents=True, exist_ok=True)
# Product images only — invoice PDFs require auth via /api/v1/pos/invoice/{no}/pdf
app.mount("/uploads/products", StaticFiles(directory=str(_products_dir)), name="upload-products")
