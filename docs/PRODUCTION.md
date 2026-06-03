# Single-VPS production (Docker Compose + nginx load balancer)

This stack runs on one server: **nginx** fronts the SPA and load-balances **API replicas** to PostgreSQL, Redis, Celery, and a single Telegram poller.

## Architecture

```
Clients → nginx (port PUBLIC_HTTP_PORT) → backend × N (least_conn)
                ↓
         PostgreSQL, Redis (single instance each)
         celery-worker, celery-beat (×1), telegram-bot (×1)
```

## Load balancer (nginx)

- Upstream: [`nginx/conf.d/00-upstream.conf`](../nginx/conf.d/00-upstream.conf) — `least_conn` to `backend:8000`
- Scale API: set `BACKEND_REPLICAS=2` (or more) in root `.env`, then deploy.

```powershell
# Option A: root .env
BACKEND_REPLICAS=2

# Option B: one-shot
python scripts/deploy_lan.py --backend-replicas 2 --build

# Option C:
.\docker-update.ps1 -BackendReplicas 2
```

**Singleton services (never scale):**

| Service        | Why                                      |
|----------------|------------------------------------------|
| `telegram-bot` | Long polling — duplicate token → HTTP 409 |
| `celery-beat`  | One cron scheduler                       |
| `nginx`        | One entry point                          |
| `db`, `redis`  | Single-node data store                   |

Shared uploads: volume `backend_uploads` — all API replicas on the **same host** read/write the same files.

## Schedulers (avoid duplicate jobs)

| Component        | Production recommendation                          |
|------------------|----------------------------------------------------|
| `celery-beat`    | **On** — owns backup, low-stock, daily report      |
| API `SCHEDULER_ENABLED` | **false** when `celery-beat` runs (see `Backend/.env`) |

Set in [`Backend/.env`](../Backend/.env) for production:

```env
APP_ENV=production
SCHEDULER_ENABLED=false
CACHE_ENABLED=true
BACKEND_REPLICAS=2
```

Match `BACKEND_REPLICAS` to root `.env` so scheduler locks stay strict when scaled.

## Production deploy

```powershell
# 1. Copy and edit secrets (never commit)
copy Backend\.env.example Backend\.env
copy .env.deploy.example .env

# 2. Production overlay (logging limits, memory caps)
docker compose -f docker-compose.yml -f docker-compose.prod.yml build
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --scale backend=2

# Or LAN script with replicas:
python scripts/deploy_lan.py --backend-replicas 2 --build
```

### Security checklist

| Setting | Production |
|---------|------------|
| `APP_DEBUG` | `false` |
| `API_DOCS_ENABLED` | `false` |
| `CORS_ALLOW_LAN` | `false` |
| `CORS_ORIGINS` | Your real site URL(s) |
| `JWT_SECRET_KEY` | Long random string (64+ chars) |
| DB port | Stays `127.0.0.1:5432` in compose (not public) |
| TLS | Replace self-signed cert or put Caddy/Traefik in front |

## Health checks

- `GET /health` and `GET /api/v1/health` verify **PostgreSQL** and **Redis** (when `CACHE_ENABLED=true`).
- Returns **503** if a dependency fails — Docker and nginx stop routing to bad API replicas.

## Phase 1 — Load balancer verification

Run after deploy with `BACKEND_REPLICAS=2`:

```powershell
.\scripts\verify_lb.ps1
```

Or manually:

```powershell
docker compose ps backend
docker compose exec nginx getent hosts backend
curl -s http://127.0.0.1:8081/health
curl -s http://127.0.0.1:8081/api/v1/health
docker compose ps telegram-bot celery-beat
```

**Pass criteria:**

- Two or more `backend` containers, status healthy
- `getent hosts backend` lists multiple IPs
- `/health` returns `200` with `"status":"ok"` and checks for database/redis
- Exactly one `ecom-telegram-bot` and one `ecom-celery-beat`
- Manual: login, checkout, open `/uploads/products/...` image URL

## PostgreSQL backup (cron example)

```bash
# Daily 02:00 — adjust user/db from Backend/.env
0 2 * * * docker exec ecom-postgres pg_dump -U ecom-admin ecommerce | gzip > /var/backups/ecom-$(date +\%F).sql.gz
```

## Updates

```powershell
.\docker-update.ps1 -Build
# or with 2 API replicas:
.\docker-update.ps1 -Build -BackendReplicas 2
curl -s http://127.0.0.1:8081/health
```

## Out of scope (single VPS)

- Multi-server HA, replicated Postgres, floating IP
- Object storage for uploads across separate machines (use S3/NFS if you add nodes later)
- CI/CD — add GitHub Actions when needed
