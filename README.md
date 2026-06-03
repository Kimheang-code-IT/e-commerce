# E-Commerce (POS + reports + Telegram)

**Docker** runs the API, PostgreSQL, Redis, Celery, and Telegram bot. **Host nginx** (you install) serves the SPA and HTTPS on ports 80/443, proxying to `http://127.0.0.1:8000`.

## Push to GitHub (this machine)

**Never commit secrets.** These stay local only (already in `.gitignore`):

- `Backend/.env`
- `.env` (auto-generated LAN IP)
- `Backend/credentials/*.json`

```powershell
git add .
git status
git commit -m "Docker stack; host nginx for SPA and TLS"
git push origin main
```

## Deploy on another computer

**Requirements:** Docker, Python 3.11+ (for deploy script), Git. **Host nginx** for browsers to reach the app.

```powershell
git clone https://github.com/YOUR_USER/e-comerce.git
cd e-comerce
.\scripts\setup-from-github.ps1
```

Or manually:

1. Copy `Backend/.env.example` → `Backend/.env` (DB, JWT, Telegram, Google backup).
2. Place Google service account JSON at `Backend/credentials/` if using backup.
3. Start Docker:

```powershell
.\docker-update.ps1
```

4. Build frontend and configure host nginx — see [host-nginx-examples/domank-dontrey.in.conf.sample](host-nginx-examples/domank-dontrey.in.conf.sample).

```bash
cd Frontend && pnpm install && pnpm exec nuxi generate
```

5. Open your site via nginx (e.g. `https://domank-dontrey.in/` or `http://<LAN-IP>/`). First run with no users: `/setup`.

### Telegram (same bot everywhere)

| Setting | Role |
|---------|------|
| `TELEGRAM_BOT_TOKEN` | From @BotFather — same on each machine |
| `TELEGRAM_CHAT_ID` | Same chat id on each machine |
| `TELEGRAM_REPORT_ENABLED=true` | Menus via `telegram-bot` |
| `TELEGRAM_NOTIFY_ENABLED=true` | Checkout alerts via `celery-worker` |

```powershell
docker compose logs telegram-bot -f
```

### Updates after `git pull`

```powershell
.\docker-update.ps1
```

Rebuild frontend if `NUXT_PUBLIC_*` changed; reload host nginx.

## Docs

- [DEPLOY-LAN.md](DEPLOY-LAN.md) — Docker + LAN + host nginx
- [docs/PRODUCTION.md](docs/PRODUCTION.md) — production checklist
- [host-nginx-examples/](host-nginx-examples/) — sample nginx config
- [docs/PERFORMANCE-SECURITY.md](docs/PERFORMANCE-SECURITY.md) — Redis, Celery, rate limits

## Quick commands

```powershell
docker compose ps
curl http://127.0.0.1:8000/health
docker compose logs celery-worker --tail 30
.\docker-update.ps1 -NoBuild
.\docker-update.ps1 -BackendReplicas 2
```
