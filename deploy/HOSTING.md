# Hosting: anyamusicschool.com

| URL | App | Access |
|-----|-----|--------|
| https://anyamusicschool.com | `website_business` | Public — SEO + sitemap |
| https://admin.anyamusicschool.com | `Frontend` | Staff only — nginx IP allowlist |

Backend API and uploads are **not** exposed directly; nginx proxies `/api/v1/` and `/uploads/` on both hosts.

---

## 1. DNS

Point these A records to your server IP:

| Host | Type | Value |
|------|------|-------|
| `@` | A | your-server-ip |
| `www` | A | your-server-ip |
| `admin` | A | your-server-ip |

---

## 2. Server packages (Ubuntu)

```bash
sudo apt update
sudo apt install -y docker.io docker-compose-plugin nginx certbot python3-certbot-nginx rsync
sudo usermod -aG docker $USER
# log out and back in
```

---

## 3. Clone and configure env

```bash
git clone <your-repo> /opt/e-comerce
cd /opt/e-comerce
```

**Root `.env`** (docker compose):

```bash
cp deploy/env/anyamusicschool.production.env .env
```

**Backend** (secrets — edit passwords and JWT):

```bash
cp deploy/env/Backend.production.env Backend/.env
# Edit DATABASE_URL, POSTGRES_PASSWORD, JWT_SECRET_KEY
```

---

## 4. Start Docker stack

```bash
docker compose up -d --build
docker compose ps
curl -s http://127.0.0.1:8000/health
curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:3001/
```

Services:

- Backend API → `127.0.0.1:8000`
- Public site → `127.0.0.1:3001`
- Postgres / Redis / Celery / Telegram bot

---

## 5. Build and deploy admin (static)

On the server:

```bash
chmod +x deploy/scripts/build-admin.sh
./deploy/scripts/build-admin.sh
```

Or on Windows before upload:

```powershell
.\deploy\scripts\build-admin.ps1
# Upload Frontend\.output\public → server:/var/www/anyamusicschool-admin
```

---

## 6. Nginx + TLS

```bash
sudo mkdir -p /var/www/certbot
sudo cp deploy/nginx/anyamusicschool.conf /etc/nginx/sites-available/anyamusicschool
sudo ln -sf /etc/nginx/sites-available/anyamusicschool /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default

# IP allowlist for admin — REQUIRED before going live
sudo cp deploy/nginx/admin-allowlist.conf.example /etc/nginx/snippets/admin-allowlist.conf
sudo nano /etc/nginx/snippets/admin-allowlist.conf
# Add: allow YOUR_OFFICE_IP;
# Keep: deny all;

sudo nginx -t
sudo systemctl reload nginx

sudo certbot --nginx \
  -d anyamusicschool.com \
  -d www.anyamusicschool.com \
  -d admin.anyamusicschool.com
```

---

## 7. Verify

| Check | URL |
|-------|-----|
| Public home | https://anyamusicschool.com |
| Khmer locale | https://anyamusicschool.com/km |
| Sitemap | https://anyamusicschool.com/sitemap.xml |
| Robots | https://anyamusicschool.com/robots.txt |
| API health (via nginx) | https://anyamusicschool.com/api/v1/... |
| Admin login | https://admin.anyamusicschool.com (from allowed IP only) |

**Google Search Console:** add `https://anyamusicschool.com`, submit sitemap  
`https://anyamusicschool.com/sitemap.xml`

---

## 8. Updates

```bash
cd /opt/e-comerce
git pull
docker compose up -d --build website backend
./deploy/scripts/build-admin.sh
```

---

## Security notes

- Admin uses `robots.txt` Disallow + `noindex` meta — not for public search.
- `admin.anyamusicschool.com` must use the IP allowlist; do not remove `deny all`.
- Keep `API_DOCS_ENABLED=false` in production.
- Use strong `JWT_SECRET_KEY` and database passwords.
