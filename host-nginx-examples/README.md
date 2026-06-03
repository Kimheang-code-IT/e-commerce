# Host nginx examples

These files are **not** used by Docker Compose. Copy and edit them on your WSL/Linux server.

1. Start Docker: `docker compose up -d` (API at `127.0.0.1:8000`)
2. Build SPA: `cd Frontend && pnpm exec nuxi generate`
3. Install nginx + certbot on the host
4. Copy `domank-dontrey.in.conf.sample` → `/etc/nginx/sites-available/`
5. `sudo certbot --nginx -d domank-dontrey.in`

See [docs/PRODUCTION.md](../docs/PRODUCTION.md) and [DEPLOY-LAN.md](../DEPLOY-LAN.md).
