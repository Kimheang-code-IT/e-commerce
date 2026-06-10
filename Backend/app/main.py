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
from sqlalchemy import text

from app.api.v1.routes import router as api_router
from app.core.config import settings
from app.core.database import Base, engine
from app.core.logging_config import setup_logging
from app.core.health import is_live, run_health_checks
from app.core.scheduler import start_scheduler, shutdown_scheduler

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

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(RateLimitMiddleware)


def init_db() -> None:
    """Create tables from SQLAlchemy models (aligned with `e-commerce.sql`)."""
    from app.core.stock_lot_migration import ensure_stock_lot_schema
    from app.core.product_catalog_migration import ensure_product_catalog_schema
    from app.core.search_index_migration import ensure_search_indexes

    # Serialize schema init across uvicorn workers without holding a DB transaction
    # open during slow migrations (that would block the second worker until timeout).
    conn = engine.connect()
    try:
        conn.execute(text("SELECT pg_advisory_lock(572901, 1)"))
        try:
            Base.metadata.create_all(bind=engine)
            ensure_stock_lot_schema()
            ensure_product_catalog_schema()
            ensure_search_indexes()
        finally:
            conn.execute(text("SELECT pg_advisory_unlock(572901, 1)"))
    finally:
        conn.close()


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

def _health_response():
    payload = run_health_checks()
    if not is_live(payload):
        return JSONResponse(status_code=503, content=payload)
    return payload


@app.get("/health")
def health():
    return _health_response()


@app.get(f"{settings.api_prefix}/health")
def api_health():
    return _health_response()


@app.on_event("startup")
def on_startup():
    try:
        init_db()
    except Exception:
        logger.exception("Database initialization failed")
        raise
    start_scheduler()
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
