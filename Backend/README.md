# E-Commerce Backend (FastAPI)

Production-ready FastAPI backend using PostgreSQL, Redis/Celery, Telegram, and Google Sheets backup.

## Local Run

1. `pip install -r requirements.txt`
2. Copy `.env.example` to `.env`
3. `alembic upgrade head` (if using migrations)
4. `uvicorn app.main:app --reload`

## Docker Compose (from repo root)

```bash
docker compose up -d --build
```

Services:

- `backend` — API on **host** `127.0.0.1:8000` (proxy from host nginx)
- `db` — PostgreSQL (`127.0.0.1:5432` on host for admin tools)
- `redis` — internal only
- `celery-worker`, `celery-beat`, `telegram-bot`

There is **no nginx container**. The SPA and TLS are served by **host nginx** — see [`host-nginx-examples/`](../host-nginx-examples/).

## Production

- Host nginx proxies `/api/`, `/uploads/products/`, `/health` → `http://127.0.0.1:8000`
- `SCHEDULER_ENABLED=false` on API when `celery-beat` runs
- See [docs/PRODUCTION.md](../docs/PRODUCTION.md)

## DBeaver via SSH Tunnel

- Host: `localhost`, Port: `5432` (Docker maps to loopback)
