"""Single source of truth for Backend environment variable names (Settings + Docker DB)."""

from __future__ import annotations

from app.core.config import Settings

# Loaded by the `db` service from the same Backend/.env (not read by FastAPI Settings).
DOCKER_DB_ENV_KEYS = ("POSTGRES_DB", "POSTGRES_USER", "POSTGRES_PASSWORD")

# Must be set in Backend/.env (no default in Settings).
REQUIRED_SETTINGS_KEYS = tuple(
    name
    for name, field in Settings.model_fields.items()
    if field.is_required()
)

# Keys every new deploy should copy from .env.example (includes required + common optional).
DOCUMENTED_EXAMPLE_KEYS = tuple(
    sorted(
        set(Settings.model_fields.keys())
        | set(DOCKER_DB_ENV_KEYS)
    )
)

PLACEHOLDER_MARKERS = (
    "CHANGE_ME",
    "change-me-to-a-long-random-string",
)
