# E-Commerce (POS + reports + Telegram)

**Docker** runs the API on `http://127.0.0.1:8000` (localhost only).

**nginx** on the host serves:
- `anyamusicschool.com` → public catalog (`website_business` via Docker)
- `admin.anyamusicschool.com` → admin SPA (`Frontend` static build)

## Requirements

- Docker + Docker Compose
- Python 3.11+ (env check script)
- Node 22+ and pnpm (optional — admin build can use Docker via `build-admin.sh`)

## Quick start

```powershell
git clone https://github.com/Kimheang-code-IT/e-commerce.git
cd e-commerce
copy Backend\.env.example Backend\.env
copy .env.example .env
```

Edit `Backend\.env` (database password, `JWT_SECRET_KEY`, Telegram, Google backup).

```powershell
python Backend\app\scripts\check_env_docker.py
.\docker-update.ps1
curl http://127.0.0.1:8000/health
```

First run with no users: open admin `/setup` in the browser.

## Scripts

| Script | Purpose |
|--------|---------|
| `docker-update.ps1` / `docker-update.cmd` | Build + start Docker stack |
| `build-admin.sh` | Build admin SPA on Linux server (Docker) → `/var/www/anyamusicschool-admin` |
| `build-admin.ps1` | Build admin SPA on Windows |

```powershell
.\docker-update.ps1              # build + start
.\docker-update.ps1 -NoBuild     # restart only
.\docker-update.ps1 -Prod        # with docker-compose.prod.yml
```

On the server:

```bash
docker compose up -d --build
./build-admin.sh
```

## Environment files (safe to commit)

| File | Purpose |
|------|---------|
| `Backend/.env.example` | API settings + Postgres vars for Docker |
| `Frontend/.env.example` | Nuxt public config for local dev |
| `website_business/.env.example` | Public site URL + API base |
| `.env.example` | Compose overrides (`COMPOSE_PROJECT_NAME`, `NUXT_PUBLIC_*`) |

## Secrets (never commit)

- `Backend/.env`
- `Backend/credentials/*.json`
- Root `.env` (optional overrides)

## Production domains

| URL | App |
|-----|-----|
| https://anyamusicschool.com | Public catalog |
| https://admin.anyamusicschool.com | Admin (login required) |

Set in root `.env`:

```env
NUXT_PUBLIC_SITE_URL=https://anyamusicschool.com
NUXT_PUBLIC_API_BASE=https://anyamusicschool.com/api/v1
```

Set in `Backend/.env`:

```env
CORS_ORIGINS=https://anyamusicschool.com,https://admin.anyamusicschool.com
FILE_BASE_URL=https://anyamusicschool.com
```
