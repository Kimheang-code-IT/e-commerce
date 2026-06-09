"""Add catalog display columns to products."""

from __future__ import annotations

import logging

from sqlalchemy import inspect, text

from app.core.database import engine

logger = logging.getLogger(__name__)

_PRODUCT_CATALOG_COLUMNS: list[tuple[str, str]] = [
    ("model", "VARCHAR(120) NOT NULL DEFAULT ''"),
    ("discount_price", "DOUBLE PRECISION NOT NULL DEFAULT 0"),
    ("total_price", "DOUBLE PRECISION NOT NULL DEFAULT 0"),
    ("size", "VARCHAR(120) NOT NULL DEFAULT ''"),
    ("top", "VARCHAR(120) NOT NULL DEFAULT ''"),
    ("back_side", "VARCHAR(120) NOT NULL DEFAULT ''"),
    ("fretboard", "VARCHAR(180) NOT NULL DEFAULT ''"),
    ("string_brand", "VARCHAR(120) NOT NULL DEFAULT ''"),
    ("finishing", "VARCHAR(120) NOT NULL DEFAULT ''"),
    ("color", "VARCHAR(120) NOT NULL DEFAULT ''"),
    ("show_on_website", "BOOLEAN NOT NULL DEFAULT FALSE"),
]


def ensure_product_catalog_schema() -> None:
    insp = inspect(engine)
    if "products" not in set(insp.get_table_names()):
        return

    existing = {c["name"] for c in insp.get_columns("products")}
    alters = [
        f"ADD COLUMN {name} {definition}"
        for name, definition in _PRODUCT_CATALOG_COLUMNS
        if name not in existing
    ]
    if not alters:
        return

    adding_show_on_website = "show_on_website" not in existing

    with engine.begin() as conn:
        for clause in alters:
            conn.execute(text(f"ALTER TABLE products {clause}"))
        if adding_show_on_website:
            conn.execute(
                text(
                    "UPDATE products SET show_on_website = TRUE "
                    "WHERE status = 'active'"
                )
            )
        conn.execute(
            text(
                "UPDATE products SET total_price = out_price "
                "WHERE total_price = 0 AND out_price > 0"
            )
        )

    logger.info("Catalog columns ready on products")
