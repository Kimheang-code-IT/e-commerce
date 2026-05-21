# E-Commerce Backend (FastAPI)

Production-ready FastAPI backend using PostgreSQL as primary database, Redis/Celery for background processing, Telegram integration, and Google Sheets backup.

## Local Run

1. Install dependencies:
   - `pip install -r requirements.txt`
2. Configure env:
   - copy `.env.example` to `.env`
   - set `DATABASE_URL`, JWT secret, Telegram/Google settings
3. Run migrations:
   - `alembic revision --autogenerate -m "init database"`
   - `alembic upgrade head`
4. Start API:
   - `uvicorn app.main:app --reload`

## Docker Compose (recommended)

From repo root:

- `docker compose up --build -d`

Services started:

- `nginx` (public reverse proxy)
- `frontend` (Nuxt internal service)
- `backend` (FastAPI internal service)
- `db` (PostgreSQL)
- `redis`
- `celery-worker`
- `celery-beat`

## Production Docker Security

- Only `nginx` is public on the host: default **`8080:80`** (not host port 80). HTTPS host **`8443:443`**.
- Static frontend is baked into the `nginx` image (no separate frontend container).
- `backend` is internal only (Docker `expose: 8000`).
- `db` is not publicly exposed; it is bound to VPS localhost only: `127.0.0.1:5432:5432`.
- Frontend API base in production is relative: `/api/v1` (no hardcoded backend IP).
- Nginx proxies:
  - `/` -> static SPA in nginx
  - `/api/` -> `backend:8000/api/`

## DBeaver via SSH Tunnel

### Database tab

- Host: `localhost`
- Port: `5432`
- Database: value from `POSTGRES_DB`
- Username: value from `POSTGRES_USER`
- Password: value from `POSTGRES_PASSWORD`

### SSH Tunnel tab

- SSH Host: `<VPS_IP>`
- SSH Port: `22`
- SSH User: `<VPS_USERNAME>`
- Authentication: password or private key

## Validation Commands

Run on VPS:

- `docker compose ps`
- `curl http://YOUR_DOMAIN/api/v1/health`
- `curl http://YOUR_VPS_IP:8000` (expected: connection refused/timeout)
- `curl http://YOUR_VPS_IP:5432` (expected: connection refused/timeout)
- `sudo ufw status` (expected open ports: `22`, `80`, `443`)

## Background Jobs

- Checkout follow-up task (`app.tasks.process_checkout_background`):
  - Telegram checkout notification
  - Google Sheets backup
- Scheduled report task (`app.tasks.send_daily_product_report`) via Celery Beat

## Testing

- `pytest -q`
