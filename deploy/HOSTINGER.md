# Complete Hostinger VPS deployment — anyamusicschool.com

This project needs **Hostinger VPS** (not shared Web Hosting). You need Docker, PostgreSQL, Redis, and a Node app — shared hosting cannot run this stack.

| What | Hostinger product |
|------|-------------------|
| Domain `anyamusicschool.com` | Domain (any registrar; can manage DNS in Hostinger) |
| App server | **VPS** — Ubuntu 22.04 or 24.04 |
| Your VPS | `srv1740865` — IP **`187.127.109.98`** |

## Final result

| URL | App | Login |
|-----|-----|-------|
| https://anyamusicschool.com | Public catalog (`website_business`) | No |
| https://admin.anyamusicschool.com | Admin POS (`Frontend`) | Yes — `/login` or `/setup` (first user) |

---

## Part 1 — Hostinger hPanel (browser)

### 1.1 VPS firewall

1. Log in to [Hostinger hPanel](https://hpanel.hostinger.com)
2. **VPS** → your server (`srv1740865`)
3. **Security** → **Firewall**
4. Allow inbound: **22** (SSH), **80** (HTTP), **443** (HTTPS)
5. Save

### 1.2 DNS (domain must point to your VPS)

1. hPanel → **Domains** → `anyamusicschool.com` → **DNS / DNS Zone**
2. Delete or edit old A records that point elsewhere (e.g. `2.57.91.91`)
3. Add or update:

| Type | Name | Points to | TTL |
|------|------|-----------|-----|
| A | `@` | `187.127.109.98` | 300 |
| A | `www` | `187.127.109.98` | 300 |
| A | `admin` | `187.127.109.98` | 300 |

4. Wait 5–60 minutes. Check:

```bash
ping anyamusicschool.com
# must show 187.127.109.98
```

### 1.3 SSH access

1. VPS → **SSH access** — note root password or add your SSH key
2. Connect from your PC:

```bash
ssh root@187.127.109.98
```

---

## Part 2 — One-time server setup (SSH)

### Option A — automated script

```bash
cd /opt
git clone https://github.com/Kimheang-code-IT/e-commerce.git e-comerce
cd e-comerce
chmod +x deploy/scripts/hostinger-setup.sh
./deploy/scripts/hostinger-setup.sh
```

Then edit secrets (required):

```bash
nano Backend/.env
# Set POSTGRES_PASSWORD, DATABASE_URL password, JWT_SECRET_KEY
# Generate JWT: openssl rand -hex 32
```

Restart stack:

```bash
cd /opt/e-comerce
docker compose up -d --build
```

### Option B — manual steps

```bash
# Packages
apt update
apt install -y git nginx certbot python3-certbot-nginx rsync curl
# Docker (official)
curl -fsSL https://get.docker.com | sh

# App
mkdir -p /opt && cd /opt
git clone https://github.com/Kimheang-code-IT/e-commerce.git e-comerce
cd e-comerce

cp deploy/env/anyamusicschool.production.env .env
cp deploy/env/Backend.production.env Backend/.env
nano Backend/.env   # passwords + JWT

docker compose up -d --build
```

Wait until healthy:

```bash
docker compose ps
curl -s http://127.0.0.1:8000/health
curl -s -o /dev/null -w "%{http_code}\n" http://127.0.0.1:3001/
```

---

## Part 3 — Admin static files

```bash
cd /opt/e-comerce
chmod +x deploy/scripts/build-admin.sh
./deploy/scripts/build-admin.sh
ls /var/www/anyamusicschool-admin/index.html
```

---

## Part 4 — Nginx + free SSL (Let's Encrypt)

**HTTP first** (certificates do not exist yet):

```bash
cd /opt/e-comerce
mkdir -p /var/www/certbot
cp deploy/nginx/anyamusicschool.http.conf /etc/nginx/sites-available/anyamusicschool
ln -sf /etc/nginx/sites-available/anyamusicschool /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default
nginx -t && systemctl reload nginx
```

**HTTPS with Certbot:**

```bash
certbot --nginx \
  -d anyamusicschool.com \
  -d www.anyamusicschool.com \
  -d admin.anyamusicschool.com
```

Follow prompts (email, agree, redirect HTTP → HTTPS: **Yes**).

Optional — use repo HTTPS config after certbot:

```bash
cp deploy/nginx/anyamusicschool.conf /etc/nginx/sites-available/anyamusicschool
nginx -t && systemctl reload nginx
```

---

## Part 5 — First admin user

1. Open https://admin.anyamusicschool.com/setup  
   (or `/login` if a user already exists)
2. Create the first administrator account
3. Log in and manage products — they appear on https://anyamusicschool.com

---

## Part 6 — Verify everything

| Check | Command or URL |
|-------|----------------|
| API | `curl -s https://anyamusicschool.com/api/v1/catalog/categories` |
| Public site | https://anyamusicschool.com |
| Khmer | https://anyamusicschool.com/km |
| Sitemap | https://anyamusicschool.com/sitemap.xml |
| Admin | https://admin.anyamusicschool.com/login |
| Docker | `docker compose ps` (all healthy / up) |

**Google Search Console:** add `https://anyamusicschool.com`, submit  
`https://anyamusicschool.com/sitemap.xml`

---

## Part 7 — Updates after code changes

```bash
cd /opt/e-comerce
git pull
docker compose up -d --build website backend
./deploy/scripts/build-admin.sh
```

---

## Hostinger troubleshooting

### DNS still wrong IP

```bash
dig +short anyamusicschool.com
# must be 187.127.109.98 — fix A records in hPanel DNS
```

### `nginx -t` fails — missing SSL files

Use `anyamusicschool.http.conf` first, run certbot, then HTTPS config.

### Website build fails (pnpm / Node)

Already fixed in repo — pull latest and rebuild:

```bash
git pull
docker compose build website --no-cache
docker compose up -d website
```

### Admin build — `pnpm: command not found`

Use Docker script (no host pnpm):

```bash
./deploy/scripts/build-admin.sh
```

### Port 80/443 blocked

Check Hostinger VPS **Firewall** in hPanel (Part 1.1).

### Certbot fails

- DNS must point to `187.127.109.98` first
- Port 80 must be open
- No other service using port 80: `ss -tlnp | grep ':80'`

### Database empty after first deploy

Normal — use https://admin.anyamusicschool.com/setup to create admin, then add products in admin UI.

---

## Optional — Telegram & Google backup

Edit `Backend/.env` on the server:

```env
TELEGRAM_BOT_TOKEN=...
TELEGRAM_CHAT_ID=...
TELEGRAM_NOTIFY_ENABLED=true
GOOGLE_SHEET_ID=...
GOOGLE_SERVICE_ACCOUNT_FILE=/app/credentials/your-file.json
GOOGLE_BACKUP_ENABLED=true
```

Upload credentials:

```bash
# Copy JSON to server, e.g. Backend/credentials/
docker compose restart backend celery-worker telegram-bot
```

---

## Security checklist

- [ ] Strong `POSTGRES_PASSWORD` and `JWT_SECRET_KEY` in `Backend/.env`
- [ ] `APP_ENV=production`, `API_DOCS_ENABLED=false`
- [ ] `Backend/.env` never committed to git
- [ ] HTTPS enabled on both domains
- [ ] Only ports 22, 80, 443 open in Hostinger firewall

---

## Quick reference

```bash
ssh root@187.127.109.98
cd /opt/e-comerce
docker compose ps
docker compose logs backend --tail 50
docker compose logs website --tail 50
systemctl status nginx
certbot renew --dry-run
```
