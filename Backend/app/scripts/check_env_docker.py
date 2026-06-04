"""Validate Backend/.env for Docker and that it matches .env.example + Settings."""

from __future__ import annotations

import sys
from pathlib import Path
from urllib.parse import urlparse

_BACKEND_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(_BACKEND_ROOT))


def _parse_env_file(path: Path) -> dict[str, str]:
    vals: dict[str, str] = {}
    if not path.exists():
        return vals
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" in line:
            k, v = line.split("=", 1)
            vals[k.strip()] = v.strip()
    return vals


def _placeholder_secret(key: str, value: str) -> bool:
    from app.core.env_catalog import PLACEHOLDER_MARKERS

    low = value.lower()
    if key == "JWT_SECRET_KEY":
        return any(m in low for m in PLACEHOLDER_MARKERS) or len(value) < 32
    if key == "POSTGRES_PASSWORD":
        return value == "CHANGE_ME"
    return False


def main() -> int:
    from app.core.env_catalog import (
        DOCKER_DB_ENV_KEYS,
        DOCUMENTED_EXAMPLE_KEYS,
        REQUIRED_SETTINGS_KEYS,
    )

    env_path = _BACKEND_ROOT / ".env"
    example_path = _BACKEND_ROOT / ".env.example"

    if not example_path.exists():
        print("FAIL: Backend/.env.example missing")
        return 1
    if not env_path.exists():
        print("FAIL: Backend/.env missing (copy from .env.example)")
        return 1

    vals = _parse_env_file(env_path)
    example_vals = _parse_env_file(example_path)
    issues: list[str] = []

    for k in REQUIRED_SETTINGS_KEYS:
        if k not in vals or not vals[k]:
            issues.append(f"missing or empty: {k}")
    for k in DOCKER_DB_ENV_KEYS:
        if k not in vals or not vals[k]:
            issues.append(f"missing or empty: {k}")

    for k in ("REDIS_URL", "CELERY_BROKER_URL", "CELERY_RESULT_BACKEND"):
        if k not in vals or not vals[k]:
            issues.append(f"missing or empty: {k}")

    optional_missing = sorted(
        k
        for k in DOCUMENTED_EXAMPLE_KEYS
        if k not in vals
        and k in example_vals
        and k not in REQUIRED_SETTINGS_KEYS
        and k not in DOCKER_DB_ENV_KEYS
    )

    stale_in_example = sorted(set(example_vals) - set(DOCUMENTED_EXAMPLE_KEYS))
    if stale_in_example:
        issues.append(
            ".env.example has unknown keys (update env_catalog/config): "
            + ", ".join(stale_in_example)
        )

    for secret_key in ("JWT_SECRET_KEY", "POSTGRES_PASSWORD"):
        v = vals.get(secret_key, "")
        if v and _placeholder_secret(secret_key, v):
            issues.append(f"{secret_key} still uses a placeholder — change before deploy")

    dbu = vals.get("DATABASE_URL", "")
    if dbu:
        normalized = dbu.replace("postgresql+psycopg2", "postgresql", 1)
        u = urlparse(normalized)
        host = (u.hostname or "").lower()
        if host != "db":
            issues.append(f'DATABASE_URL host should be "db" inside Docker (got {host!r})')
        if u.username and vals.get("POSTGRES_USER") and u.username != vals["POSTGRES_USER"]:
            issues.append("DATABASE_URL username != POSTGRES_USER")
        db_name = (u.path or "").lstrip("/").split("?")[0]
        pdb = vals.get("POSTGRES_DB", "")
        if db_name and pdb and db_name != pdb:
            issues.append("DATABASE_URL database != POSTGRES_DB")

    for redis_key in ("REDIS_URL", "CELERY_BROKER_URL", "CELERY_RESULT_BACKEND"):
        ru = vals.get(redis_key, "")
        if not ru:
            continue
        h = (urlparse(ru).hostname or "").lower()
        if h != "redis":
            issues.append(f'{redis_key} host should be "redis" in Compose (got {h!r})')

    if issues:
        print("Backend .env:")
        for i in issues:
            print("  -", i)
        print("Fix the above, then re-run.")
        return 1

    try:
        from app.core.config import Settings

        Settings()
    except Exception as exc:
        print(f"FAIL: Settings() could not load from .env: {exc}")
        return 1

    print("Backend .env: Docker alignment OK, Settings() loads OK")
    if optional_missing:
        print(
            "Optional (add from .env.example if you use these features): "
            + ", ".join(optional_missing)
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
