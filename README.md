# E-Commerce (POS + reports + Telegram)

**Docker** runs the API on `http://127.0.0.1:8000` (not exposed to LAN directly).

**Ubuntu nginx** serves the public site: static SPA + proxy `/api` to that backend. No static LAN IP is configured in the app — only your domain in `CORS_ORIGINS` and `FILE_BASE_URL`.

See [docs/NGINX-UBUNTU.md](docs/NGINX-UBUNTU.md).

## Requirements

- [Docker Desktop](https://www.docker.com/products/docker-desktop/)
- Python 3.11+ (env check script)
- Node 20+ and pnpm (frontend build)

## Quick start

```powershell
git clone https://github.com/Kimheang-code-IT/e-commerce.git
cd e-commerce
copy Backend\.env.example Backend\.env
```

Edit `Backend\.env` (database password, `JWT_SECRET_KEY`, Telegram, Google backup).

```powershell
python Backend\app\scripts\check_env_docker.py
.\docker-update.ps1
curl http://127.0.0.1:8000/health
```

Build the static frontend:

```bash
cd Frontend
pnpm install
pnpm exec nuxi generate
```

First run with no users: use `/setup` in the browser.

## Environment files (safe to commit)

| File | Purpose |
|------|---------|
| `Backend/.env.example` | All API settings + Postgres vars for Docker |
| `Frontend/.env.example` | Nuxt public config for local dev |
| `.env.example` | Optional Compose overrides (`COMPOSE_PROJECT_NAME`, replicas) |

Copy examples to `.env` locally. Verify before Docker:

```powershell
python Backend\app\scripts\check_env_docker.py
```

## Secrets (never commit)

- `Backend/.env`
- `Backend/credentials/*.json`
- Root `.env` (optional overrides only)

## Telegram

Use the **same** `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID` on each machine, but run **only one** `telegram-bot` container at a time (same token).

```powershell
docker compose logs telegram-bot -f
```

## Commands

```powershell
.\docker-update.ps1              # build + start
.\docker-update.ps1 -NoBuild      # restart only
.\docker-update.ps1 -Prod         # with docker-compose.prod.yml
.\docker-update.ps1 -BackendReplicas 2
docker compose ps
docker compose logs celery-worker --tail 30
```

## Docs

- [docs/DEPLOY-FROM-GITHUB.md](docs/DEPLOY-FROM-GITHUB.md) — clone on another PC (what is / is not in Git)
- [docs/NGINX-UBUNTU.md](docs/NGINX-UBUNTU.md) — nginx on Ubuntu (HTTPS, `/api` proxy)
- [Backend/README.md](Backend/README.md) — API and Docker details
