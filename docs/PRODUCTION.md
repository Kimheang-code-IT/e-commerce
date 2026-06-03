# Production deploy (Docker stack + host nginx)

Docker runs the **API and workers only**. You install and configure **nginx + Certbot** on the host (WSL/Linux) on ports **80/443**.

## Architecture

```
Clients → host nginx (80/443) → 127.0.0.1:8000 (Docker backend)
                ↓
         SPA static files (Frontend/.output/public)
                ↓
         PostgreSQL, Redis, Celery, telegram-bot (Docker internal)
```

| Layer | Role |
|-------|------|
| **Host nginx** | TLS, reverse proxy, SPA `root` — you maintain config |
| **Docker** | `backend`, `db`, `redis`, `celery-worker`, `celery-beat`, `telegram-bot` |
| **Not in Docker** | nginx, Certbot |

Sample config: [`host-nginx-examples/domank-dontrey.in.conf.sample`](../host-nginx-examples/domank-dontrey.in.conf.sample)

## Docker

```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build
# Optional scale:
docker compose up -d --scale backend=2
```

API is published at **`127.0.0.1:8000`** only (not exposed to LAN directly).

**Singleton services (never scale):**

| Service | Why |
|---------|-----|
| `telegram-bot` | Long polling — duplicate token → HTTP 409 |
| `celery-beat` | One cron scheduler |

## Frontend (SPA)

Build once on the host (values baked at generate time):

```bash
cd Frontend
pnpm install
export NUXT_PUBLIC_SITE_URL=https://domank-dontrey.in
export NUXT_PUBLIC_API_BASE=/api/v1
pnpm exec nuxi generate
```

Point host nginx `root` at `Frontend/.output/public`.

## Host nginx + HTTPS

1. DNS: `domank-dontrey.in` → your public IP; router forwards **80** and **443**.
2. Copy and edit `host-nginx-examples/domank-dontrey.in.conf.sample` → `/etc/nginx/sites-available/`.
3. `sudo nginx -t && sudo systemctl reload nginx`
4. `sudo certbot --nginx -d domank-dontrey.in`

## Schedulers

| Component | Production |
|-----------|------------|
| `celery-beat` | **On** |
| API `SCHEDULER_ENABLED` | **false** |

```env
APP_ENV=production
SCHEDULER_ENABLED=false
CACHE_ENABLED=true
```

## Security

| Item | Setting |
|------|---------|
| `APP_DEBUG` | `false` |
| `API_DOCS_ENABLED` | `false` |
| `CORS_ALLOW_LAN` | `false` in production |
| `CORS_ORIGINS` | `https://domank-dontrey.in,http://<LAN-IP>` |
| Redis | No host port in compose |
| Postgres | `127.0.0.1:5432` only |
| API | `127.0.0.1:8000` only |

## Health checks

```bash
curl -fsS http://127.0.0.1:8000/health
curl -fsS http://127.0.0.1/health          # via host nginx
curl -fsS https://domank-dontrey.in/health
```

Returns **503** if PostgreSQL or Redis is down.

## PostgreSQL backup

```bash
docker exec ecom-postgres pg_dump -U ecom-admin ecommerce | gzip > ecom-$(date +%F).sql.gz
```

## Updates

```bash
docker compose build backend celery-worker celery-beat telegram-bot
docker compose up -d
# Rebuild frontend if NUXT_PUBLIC_* changed, then reload nginx
```
