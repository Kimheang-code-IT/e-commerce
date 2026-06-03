# Deploy on a new computer (clone from GitHub)

Use this checklist after `git clone` on **Windows**, **WSL**, or another PC. Data and secrets are **not** in Git — you copy or recreate them locally.

**Repository:** `https://github.com/Kimheang-code-IT/e-commerce.git`  
**Branch:** `main`

---

## 1. Requirements

| Software | Purpose |
|----------|---------|
| [Git](https://git-scm.com/) | Clone the repo |
| [Docker Desktop](https://www.docker.com/products/docker-desktop/) | API, PostgreSQL, Redis, Celery, Telegram bot |
| Python 3.11+ | `scripts/deploy_lan.py`, env checks |
| Node.js 20+ and pnpm | Build frontend static files |
| Host nginx (optional for browser access) | SPA + HTTPS on ports 80/443 |

---

## 2. Clone and first-time setup

### Windows (PowerShell)

```powershell
git clone https://github.com/Kimheang-code-IT/e-commerce.git
cd e-commerce
git checkout main
.\scripts\setup-from-github.ps1
```

### Linux / WSL

```bash
git clone https://github.com/Kimheang-code-IT/e-commerce.git
cd e-commerce
git checkout main
cp Backend/.env.example Backend/.env
cp .env.deploy.example .env
mkdir -p Backend/credentials
```

---

## 3. Secrets and config (required before Docker)

Edit **`Backend/.env`** (never committed to Git).

### Option A — Copy from your working PC (easiest)

Copy these files to the **same paths** on the new PC (USB, secure share, etc.):

| File | Required |
|------|----------|
| `Backend/.env` | Yes — DB password, JWT, Telegram, Google |
| `Backend/credentials/*.json` | If you use Google Sheets backup |

Use the **same** `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID` if you want the same bot.

**Important:** Run **only one** `telegram-bot` container in the world for that token (one PC at a time). A second PC polling the same token causes Telegram `409 Conflict`.

### Option B — Fresh install (new shop / new server)

1. Copy `Backend/.env.example` → `Backend/.env`
2. Set strong values:
   - `POSTGRES_PASSWORD` and matching `DATABASE_URL` (host must be `db` inside Docker)
   - `JWT_SECRET_KEY` — long random string (64+ chars)
   - `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID` from @BotFather
3. Optional Google backup: JSON in `Backend/credentials/` and `GOOGLE_SHEET_ID` in `.env`

Validate:

```powershell
python Backend/scripts/check_env_docker.py
```

Must print `Backend .env Docker alignment: OK`.

---

## 4. Start Docker (API stack)

```powershell
.\docker-update.ps1
```

Or:

```powershell
python scripts/deploy_lan.py --build
```

Check:

```powershell
docker compose ps
curl http://127.0.0.1:8000/health
```

Expected: JSON with `"status":"ok"` and database/redis checks.

**First admin user:** open the site (see step 5) and go to **`/setup`** if no users exist.

---

## 5. Frontend (SPA)

From project root:

```bash
cd Frontend
pnpm install
# Set public URL baked into the app (match your domain or LAN):
# Windows PowerShell:
$env:NUXT_PUBLIC_SITE_URL="https://domank-dontrey.in"
$env:NUXT_PUBLIC_API_BASE="/api/v1"
pnpm exec nuxi generate
```

Output folder: **`Frontend/.output/public`** — host nginx must use this as `root`.

---

## 6. Host nginx (you install — not in Docker)

1. Install nginx on the host (WSL: `sudo apt install nginx`).
2. Copy and edit [`host-nginx-examples/domank-dontrey.in.conf.sample`](../host-nginx-examples/domank-dontrey.in.conf.sample):
   - Set `frontend_root` to the full path of `Frontend/.output/public`
3. Enable site and reload nginx.
4. HTTPS: `sudo certbot --nginx -d domank-dontrey.in` (DNS + router ports 80/443).

**LAN only (no domain yet):** use `http://<LAN-IP>/` after nginx listens on port 80.

Firewall: allow **TCP 80** and **443** on the new PC.

---

## 7. Copy database from old PC (optional)

Only if you need **existing products, users, invoices** on the new machine.

On **old PC** (while Docker postgres is running):

```powershell
docker exec ecom-postgres pg_dump -U ecom-admin ecommerce > backup.sql
```

Copy `backup.sql` to the new PC. On **new PC** after first `docker compose up` (empty DB):

```powershell
Get-Content backup.sql | docker exec -i ecom-postgres psql -U ecom-admin -d ecommerce
```

Or use [`Backend/app/scripts/reset_db.py`](../Backend/app/scripts/reset_db.py) only if you want an **empty** database.

---

## 8. Verify deployment

```powershell
.\scripts\verify-deploy.ps1
```

| Check | Command |
|-------|---------|
| API health | `curl http://127.0.0.1:8000/health` |
| Via nginx | `curl http://127.0.0.1/health` (if nginx configured) |
| Telegram | `docker compose logs telegram-bot --tail 20` — send `/start` |
| Celery | `docker compose logs celery-worker --tail 20` |

---

## 9. Updates after `git pull`

```powershell
git pull origin main
.\docker-update.ps1
```

If `NUXT_PUBLIC_*` changed, rebuild frontend and reload nginx.

---

## 10. Troubleshooting

| Problem | Fix |
|---------|-----|
| `check_env_docker.py` fails | `DATABASE_URL` host = `db`, password matches `POSTGRES_PASSWORD` |
| Port 8000 in use | Stop other apps or change publish port in `docker-compose.yml` |
| Telegram 409 | Stop `telegram-bot` on the other PC |
| Blank page in browser | Build frontend (`nuxi generate`); check nginx `root` path |
| CORS error on LAN | `CORS_ALLOW_LAN=true` or add `http://<LAN-IP>` to `CORS_ORIGINS` |
| Old data missing | Restore `pg_dump` (section 7) — volumes are per machine |

---

## Quick reference

| What | Where |
|------|--------|
| Docker stack | `docker-compose.yml` |
| Production limits | `docker-compose.prod.yml` |
| LAN IP in root `.env` | `python scripts/deploy_lan.py` |
| Nginx sample | `host-nginx-examples/` |
| More detail | [DEPLOY-LAN.md](../DEPLOY-LAN.md), [PRODUCTION.md](PRODUCTION.md) |
