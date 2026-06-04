# Deploy on another computer (from GitHub)

## What Git includes

- Source code, `docker-compose.yml`, `docker-update.ps1`
- `Backend/.env.example`, `Frontend/.env.example`, `.env.example`
- `docs/NGINX-UBUNTU.md`

## What Git does **not** include (create on the new machine)

| Item | Action |
|------|--------|
| `Backend/.env` | `cp Backend/.env.example Backend/.env` then edit passwords & secrets |
| `Frontend/.env` | `cp Frontend/.env.example Frontend/.env` (optional for `pnpm dev`) |
| `.env` (repo root) | `cp .env.example .env` (optional Compose project name) |
| `Backend/credentials/*.json` | Copy Google service account JSON manually |
| `Backend/uploads/` | Created at runtime |
| `Frontend/.output/` | Run `pnpm exec nuxi generate` after clone |

## Steps (Ubuntu or Windows with Docker)

```bash
git clone https://github.com/Kimheang-code-IT/e-commerce.git
cd e-commerce

cp Backend/.env.example Backend/.env
cp Frontend/.env.example Frontend/.env
cp .env.example .env   # optional

# Edit Backend/.env — JWT, DB password, domain in CORS_ORIGINS for production
python Backend/app/scripts/check_env_docker.py

docker compose up -d --build
curl http://127.0.0.1:8000/health

cd Frontend && pnpm install && pnpm exec nuxi generate
```

Production HTTPS: [NGINX-UBUNTU.md](NGINX-UBUNTU.md).

## Before `git push` on your dev PC

```bash
git status
```

Ensure you do **not** see `Backend/.env`, `Frontend/.env`, `.env`, or `Backend/credentials/*.json` staged.

If any appear, they are not ignored correctly — do not commit them.
