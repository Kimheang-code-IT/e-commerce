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

**Full checklist:** [docs/DEPLOY-NEW-PC.md](docs/DEPLOY-NEW-PC.md)  
**Secrets to copy:** [SECRETS.example.md](SECRETS.example.md)

**Requirements:** Docker Desktop, Python 3.11+, Git, Node/pnpm (frontend build), host nginx (browser access).

```powershell
git clone https://github.com/Kimheang-code-IT/e-commerce.git
cd e-commerce
git checkout main
.\scripts\setup-from-github.ps1
```

1. Edit **`Backend/.env`** (or copy from your old PC — see `SECRETS.example.md`).
2. `python Backend/scripts/check_env_docker.py` → must say OK.
3. `.\docker-update.ps1`
4. Build frontend: `cd Frontend; pnpm install; pnpm exec nuxi generate`
5. Configure host nginx: [host-nginx-examples/domank-dontrey.in.conf.sample](host-nginx-examples/domank-dontrey.in.conf.sample)
6. `.\scripts\verify-deploy.ps1`

First visit with empty database: open **`/setup`** to create the admin user.

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

- **[docs/DEPLOY-NEW-PC.md](docs/DEPLOY-NEW-PC.md)** — clone and deploy on a new PC (start here)
- [SECRETS.example.md](SECRETS.example.md) — what to copy from the old machine
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
