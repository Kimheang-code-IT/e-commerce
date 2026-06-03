# E-Commerce (POS + reports + Telegram)

LAN/Wi-Fi deploy with **Docker**: nginx (SPA + load balancer), FastAPI, PostgreSQL, Redis, Celery, Telegram polling bot.

## Push to GitHub (this machine)

**Never commit secrets.** These stay local only (already in `.gitignore`):

- `Backend/.env`
- `.env` (auto-generated LAN IP)
- `Backend/credentials/*.json`

```powershell
git add .
git status
# Confirm Backend/.env and credentials are NOT listed
git commit -m "Docker LAN deploy, Celery, nginx LB, Telegram polling"
git push origin main
```

## Deploy on another computer

**Requirements:** Windows 10/11, [Docker Desktop](https://www.docker.com/products/docker-desktop/), Python 3.11+ (for deploy script), Git.

```powershell
git clone https://github.com/YOUR_USER/e-comerce.git
cd e-comerce
.\scripts\setup-from-github.ps1
```

Or manually:

1. Copy `Backend/.env.example` → `Backend/.env` and fill in DB password, JWT secret, **your existing** `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID` (same bot on every PC).
2. Optional: copy `.env.deploy.example` → `.env` and set `BACKEND_REPLICAS=2` for nginx load balancing.
3. Place Google service account JSON at `Backend/credentials/google-service-account.json` if using backup.
4. Allow firewall **TCP 8080** (and 8443 for HTTPS).
5. Run:

```powershell
.\docker-update.ps1
```

Open the URL printed (e.g. `http://192.168.x.x:8080/`). On first run (no users), open `/setup` to create the administrator account.

### Telegram (same bot everywhere)

| Setting | Role |
|---------|------|
| `TELEGRAM_BOT_TOKEN` | From @BotFather — **use the same value on each machine** |
| `TELEGRAM_CHAT_ID` | Your group/user id — **same on each machine** |
| `TELEGRAM_REPORT_ENABLED=true` | Report menus via `telegram-bot` container |
| `TELEGRAM_NOTIFY_ENABLED=true` | Checkout alerts via `celery-worker` |

Bot uses **send-only** replies (no edit/delete message APIs). Menus may send multiple messages as you tap buttons.

```powershell
docker compose logs telegram-bot -f
```

Send `/start` in the configured chat.

### Updates after `git pull`

```powershell
.\docker-update.ps1
```

## Docs

- [DEPLOY-LAN.md](DEPLOY-LAN.md) — LAN IP, load balancer, firewall, ports
- [docs/PERFORMANCE-SECURITY.md](docs/PERFORMANCE-SECURITY.md) — Redis, Celery, rate limits

## Quick commands

```powershell
docker compose ps
docker compose logs celery-worker --tail 30
.\docker-update.ps1 -NoBuild
.\docker-update.ps1 -BackendReplicas 2
```
