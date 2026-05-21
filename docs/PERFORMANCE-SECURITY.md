# Performance & security improvements

## Checkout speed

- **Row locks** (`SELECT FOR UPDATE`) on products during checkout — prevents overselling under concurrent POS.
- **Advisory lock** for `DNS-*` invoice numbers — safe sequential allocation.
- **No duplicate cache SCAN on API** — Redis invalidation runs in Celery `refresh_checkout_caches_task` only.
- **`INVOICE_PDF_SYNC`** (default `true`) — set `false` in `.env` for fastest checkout; PDF via Celery + `GET /api/v1/pos/invoice/{no}/pdf`.

## Redis cache

- Product list, categories, dashboard, stock tier (unchanged).
- Invalidation after checkout (Celery) and delivery status updates.

## Celery

- **Idempotency fix**: lock before run, mark done after success, clear lock on failure so retries work.
- Tasks: PDF, print, Telegram, cache/backup.

## Security

- **Invoice PDFs** are not served under public `/uploads` — only `/uploads/products` for images; PDFs via authenticated API.
- **Rate limits** (Redis): login and checkout POST endpoints.
- **Security headers** (API + nginx).
- **RBAC**: `pos:create` → `pos:checkout`; `backup:manage` for backup/test routes.
- **Task status**: only `checkout-{pdf|print|notify|cache}-{id}` with `pos:view`.
- **Telegram test-message**: requires login + `backup:manage`.
- **sellerId**: only users with `user:view` (typically admin) can assign another seller.
- **Production**: exception details hidden when `APP_ENV=production`.

## Deploy

After pulling changes:

```powershell
.\docker-update.ps1
```

Add new variables from `Backend/.env.example` to `Backend/.env`.
