# E-Commerce Backend (FastAPI)

PostgreSQL, Redis/Celery, Telegram, Google Sheets backup.

## Docker (from repo root)

```bash
docker compose up -d --build
curl http://127.0.0.1:8000/health
```

Services: `backend`, `db`, `redis`, `celery-worker`, `celery-beat`, `telegram-bot`.

Production overlay: `docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d`

## First admin

Use the frontend `/setup` page when the database has no users.

## Environment

- Template: `.env.example` (every `Settings` field + `POSTGRES_*` for the `db` service)
- Live secrets: `.env` (gitignored)
- Catalog: `app/core/env_catalog.py` (keys used by the checker)

```bash
python Backend/app/scripts/check_env_docker.py   # Docker hosts + Settings() load
```

## Utilities (`app/scripts/`)

**Delete all data** (drops every table, recreates empty schema):

```bash
# From repo root (Docker)
./reset-database.sh

# Or directly
docker compose exec backend python app/scripts/reset_db.py --yes
```

Interactive (asks you to type `YES`):

```bash
docker compose exec backend python app/scripts/reset_db.py
```
