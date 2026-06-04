# Ubuntu nginx (no LAN IP in app config)

The app does **not** use static LAN IPs or `CORS_ALLOW_LAN`. Access is only through your **public domain** on nginx (ports 80/443).

## Architecture

```
Browser → nginx (Ubuntu, :443)
            ├─ /          → Frontend/.output/public  (pnpm exec nuxi generate)
            └─ /api/      → http://127.0.0.1:8000     (Docker backend)
```

Docker publishes the API on the host loopback only (`127.0.0.1:8000` in `docker-compose.yml`).

## 1. Build frontend on the server

```bash
cd Frontend
pnpm install
pnpm exec nuxi generate
# static files: Frontend/.output/public
```

## 2. Start Docker stack

```bash
cd /path/to/e-commerce
copy Backend/.env.example Backend/.env   # then edit secrets
python Backend/app/scripts/check_env_docker.py
./docker-update.ps1   # or: docker compose up -d --build
curl http://127.0.0.1:8000/health
```

## 3. Backend/.env for production

```env
APP_ENV=production
APP_DEBUG=false
API_DOCS_ENABLED=false
CORS_ORIGINS=https://YOUR_DOMAIN
FILE_BASE_URL=https://YOUR_DOMAIN
SCHEDULER_ENABLED=false
```

Use **one HTTPS origin** in `CORS_ORIGINS` (your nginx site). The SPA uses relative `/api/v1`, so browser and API share the same host when nginx proxies `/api`.

## 4. Sample nginx site

Replace `YOUR_DOMAIN` and paths.

```nginx
server {
    listen 80;
    server_name YOUR_DOMAIN;
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl http2;
    server_name YOUR_DOMAIN;

    # ssl_certificate /etc/letsencrypt/live/YOUR_DOMAIN/fullchain.pem;
    # ssl_certificate_key /etc/letsencrypt/live/YOUR_DOMAIN/privkey.pem;

    root /var/www/e-commerce/Frontend/.output/public;
    index index.html;

    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /uploads/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location / {
        try_files $uri $uri/ /index.html;
    }
}
```

Enable and reload:

```bash
sudo ln -s /etc/nginx/sites-available/e-commerce /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx
```

Certbot (optional): `sudo certbot --nginx -d YOUR_DOMAIN`

## 5. Checklist

| Item | OK when |
|------|---------|
| API | `curl -s http://127.0.0.1:8000/health` returns `"status":"ok"` |
| Site | `https://YOUR_DOMAIN` loads SPA |
| API via nginx | `https://YOUR_DOMAIN/api/v1/health` returns ok |
| CORS | `CORS_ORIGINS` matches `https://YOUR_DOMAIN` (no `192.168.x`) |
| No LAN code | No `CORS_ALLOW_LAN`, no `HOST_LAN_IP` in repo `.env` |
