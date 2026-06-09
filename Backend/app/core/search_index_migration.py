"""Create trigram indexes for common ILIKE search columns."""

from __future__ import annotations
import logging
from sqlalchemy import inspect, text
from app.core.database import engine
logger = logging.getLogger(__name__)

_INDEX_STATEMENTS = (
    "CREATE EXTENSION IF NOT EXISTS pg_trgm",
    "CREATE INDEX IF NOT EXISTS idx_roles_name_trgm ON roles USING gin (name gin_trgm_ops)",
    "CREATE INDEX IF NOT EXISTS idx_users_name_trgm ON users USING gin (name gin_trgm_ops)",
    "CREATE INDEX IF NOT EXISTS idx_users_email_trgm ON users USING gin (email gin_trgm_ops)",
    "CREATE INDEX IF NOT EXISTS idx_products_name_trgm ON products USING gin (name gin_trgm_ops)",
    "CREATE INDEX IF NOT EXISTS idx_categories_name_trgm ON categories USING gin (name gin_trgm_ops)",
)


def ensure_search_indexes() -> None:
    dialect = engine.dialect.name
    if dialect != "postgresql":
        logger.info("Skipping search index migration for dialect=%s", dialect)
        return

    insp = inspect(engine)
    table_names = set(insp.get_table_names())
    required = {"roles", "users", "products", "categories"}
    if not required.issubset(table_names):
        logger.info("Skipping search index migration until core tables exist")
        return

    try:
        with engine.begin() as conn:
            for statement in _INDEX_STATEMENTS:
                conn.execute(text(statement))
        logger.info("Search trigram indexes ensured")
    except Exception:
        logger.warning("Failed to ensure search indexes", exc_info=True)
