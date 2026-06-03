"""Non-secret checks before Docker Compose. Run: python scripts/check_env_docker.py"""
from __future__ import annotations

import sys
from pathlib import Path
from urllib.parse import urlparse

_BACK = Path(__file__).resolve().parent.parent


def main() -> int:
    path = _BACK / ".env"
    if not path.exists():
        print("FAIL: Backend/.env missing (copy from .env.example)")
        return 1

    vals: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" in line:
            k, v = line.split("=", 1)
            vals[k.strip()] = v.strip()

    issues: list[str] = []
    required = [
        "DATABASE_URL",
        "JWT_SECRET_KEY",
        "POSTGRES_USER",
        "POSTGRES_PASSWORD",
        "POSTGRES_DB",
        "REDIS_URL",
        "CELERY_BROKER_URL",
    ]
    for k in required:
        if k not in vals or not vals[k]:
            issues.append(f"missing or empty: {k}")

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

    if "CACHE_ENABLED" not in vals:
        issues.append("missing CACHE_ENABLED (copy from .env.example)")
    if "INVOICE_PDF_DIR" not in vals:
        issues.append("missing INVOICE_PDF_DIR (e.g. uploads/invoices)")

    allow_lan = str(vals.get("CORS_ALLOW_LAN", "")).lower() in ("1", "true", "yes")
    cors = vals.get("CORS_ORIGINS", "")
    if not allow_lan and cors and "192.168" not in cors and "10." not in cors:
        if "localhost" in cors.lower() or "127.0.0.1" in cors:
            issues.append(
                "Set CORS_ALLOW_LAN=true for Wi-Fi on changing IPs, or add http://<LAN-ip>:<port> to CORS_ORIGINS"
            )

    if issues:
        print("Backend .env:")
        for i in issues:
            print("  -", i)
        print("Fix the above before docker compose up.")
        return 1

    print("Backend .env Docker alignment: OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
