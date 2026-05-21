# LAN / Wi-Fi deploy (automatic IP — nothing to edit by hand)

## You do **not** need to change IP in `.env` when DHCP changes

| Part | Automatic behavior |
|------|---------------------|
| **Browser / API** | Frontend calls `/api/v1` on whatever host you opened (e.g. `http://192.168.1.20:8080`). |
| **CORS** | `CORS_ALLOW_LAN=true` allows any private LAN IP and port. |
| **New PC** | Run the start script once; it detects that PC’s IP and starts Docker. |
| **IP changed** | Open the **new** URL on Wi-Fi — no rebuild. Optional: `start-lan.ps1 -watch` prints the new URL. |

## Start (recommended)

**Windows** — double-click or PowerShell:

```powershell
.\start-lan.ps1
```

First time or after code changes (Redis, Celery, PDF, API):

```powershell
.\docker-update.ps1
```

Or:

```powershell
.\start-lan.ps1 -build
```

## Docker services

| Service | Role |
|---------|------|
| **nginx** | SPA + proxy `/api/` and `/uploads/` to backend |
| **backend** | FastAPI (checkout, PDF sync, cache) |
| **db** | PostgreSQL |
| **redis** | Cache + Celery broker/result |
| **celery-worker** | Telegram notify, PDF backup tasks, Google backup |
| **telegram-bot** | Command polling (one instance only) |
| **celery-beat** | Optional daily report (`--beat` or `docker compose --profile beat up -d`) |

### Load balancer (nginx → multiple API containers)

Nginx uses upstream `ecom_backend` (`nginx/conf.d/00-upstream.conf`, `least_conn`).  
Set replicas in root `.env` (auto-written by deploy script):

```env
BACKEND_REPLICAS=2
```

Then rebuild and start:

```powershell
.\docker-update.ps1
```

Or one-off:

```powershell
python scripts/deploy_lan.py --build --backend-replicas 2
```

**Do not** scale `telegram-bot` — Telegram long-polling must run in a single container.

### Telegram bot

In `Backend/.env`:

| Variable | Purpose |
|----------|---------|
| `TELEGRAM_BOT_TOKEN` | From @BotFather |
| `TELEGRAM_CHAT_ID` | Your group or user id (only this chat can use reports) |
| `TELEGRAM_REPORT_ENABLED=true` | `/start`, menus, `/summary`, etc. |
| `TELEGRAM_NOTIFY_ENABLED=true` | Checkout alerts (sent by **celery-worker**, not the bot process) |

Check logs:

```powershell
docker compose logs telegram-bot -f
```

Send `/start` in the configured chat. If you see `Unauthorized`, fix `TELEGRAM_CHAT_ID` (group ids are often negative).

Checkout notifications: confirm `celery-worker` is healthy and logs show no Telegram API errors after a sale.

Shared volume **`backend_uploads`**: product images + invoice PDFs (`uploads/invoices/`).

## Update stack after pulling code

```powershell
.\docker-update.ps1
```

Restart without rebuild:

```powershell
.\docker-update.ps1 -NoBuild
```

Check workers:

```powershell
docker compose ps
docker compose logs celery-worker --tail 50
docker compose exec backend python -c "import reportlab; print('ok')"
```

If your IP changes often while the PC stays on:

```powershell
.\start-lan.ps1 -watch
```

Same without the script:

```powershell
python scripts/deploy_lan.py
python scripts/deploy_lan.py --build
```

## Do **not** use plain `docker compose up` on a new machine

Use `start-lan.ps1` so the script refreshes the root `.env` and prints the correct URL.  
Plain `docker compose up` still **works** for API access on any LAN IP; you just won’t get the printed URL in logs.

## Firewall (once per Windows PC)

Allow inbound **TCP 8080** (and **8443** for HTTPS).

## Port (not host 80)

Docker maps **`8080:80`** — your PC uses **8080**, nginx uses **80 inside the container only**.  
Host port **80 is never used**, so IIS/Apache on :80 is unaffected.

If **8080** is busy, `start-lan.ps1` picks the next free port (8081, 8082, …) automatically.

Custom port:

```powershell
.\start-lan.ps1 --port 9000
```

Or set `PUBLIC_HTTP_PORT=9000` in root `.env` and run `docker compose up -d`.

## New computer (GitHub clone)

```powershell
git clone <your-repo-url>
cd e-comerce
.\scripts\setup-from-github.ps1
# Edit Backend\.env — use the SAME TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID as your other PC
.\docker-update.ps1
```

See [README.md](README.md) for Git push checklist (never commit `Backend/.env` or credential JSON).

## Files

- `Backend/.env` — DB, JWT, Telegram, admin seed (copy once per machine from `.env.example`)
- Root `.env` — **auto-generated** by `deploy_lan.py` (do not edit by hand)
