#!/usr/bin/env bash
# Hostinger VPS one-time bootstrap for e-comerce (Ubuntu)
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
REPO_URL="${REPO_URL:-https://github.com/Kimheang-code-IT/e-commerce.git}"
APP_DIR="${APP_DIR:-/opt/e-comerce}"

echo "==> Hostinger VPS setup for anyamusicschool.com"
echo "    App dir: $APP_DIR"

if [[ "$(id -u)" -ne 0 ]]; then
  echo "Run as root: sudo $0" >&2
  exit 1
fi

echo "==> Installing packages..."
apt-get update -qq
apt-get install -y -qq git nginx certbot python3-certbot-nginx rsync curl ca-certificates

if ! command -v docker >/dev/null 2>&1; then
  echo "==> Installing Docker..."
  curl -fsSL https://get.docker.com | sh
fi

if ! docker compose version >/dev/null 2>&1; then
  echo "Docker Compose plugin missing. Install docker-compose-plugin." >&2
  exit 1
fi

if [[ ! -d "$APP_DIR/.git" ]]; then
  echo "==> Cloning repository..."
  mkdir -p "$(dirname "$APP_DIR")"
  git clone "$REPO_URL" "$APP_DIR"
fi

cd "$APP_DIR"

if [[ ! -f .env ]]; then
  cp deploy/env/anyamusicschool.production.env .env
  echo "Created .env from template"
fi

if [[ ! -f Backend/.env ]]; then
  cp deploy/env/Backend.production.env Backend/.env
  echo ""
  echo "IMPORTANT: Edit Backend/.env before production use:"
  echo "  nano $APP_DIR/Backend/.env"
  echo "  Set POSTGRES_PASSWORD, DATABASE_URL, JWT_SECRET_KEY"
  echo "  JWT: openssl rand -hex 32"
  echo ""
fi

mkdir -p /var/www/certbot /var/www/anyamusicschool-admin

echo "==> Building and starting Docker stack (may take several minutes)..."
docker compose up -d --build

echo "==> Waiting for backend health..."
for i in $(seq 1 30); do
  if curl -sf http://127.0.0.1:8000/health >/dev/null 2>&1; then
    echo "Backend healthy"
    break
  fi
  sleep 5
  if [[ "$i" -eq 30 ]]; then
    echo "Backend not healthy yet — check: docker compose logs backend" >&2
  fi
done

if [[ -x deploy/scripts/build-admin.sh ]]; then
  echo "==> Building admin static site..."
  chmod +x deploy/scripts/build-admin.sh
  ./deploy/scripts/build-admin.sh
fi

echo "==> Installing nginx HTTP config (before SSL)..."
cp deploy/nginx/anyamusicschool.http.conf /etc/nginx/sites-available/anyamusicschool
ln -sf /etc/nginx/sites-available/anyamusicschool /etc/nginx/sites-enabled/anyamusicschool
rm -f /etc/nginx/sites-enabled/default
nginx -t
systemctl enable nginx
systemctl reload nginx

echo ""
echo "=============================================="
echo " Hostinger setup complete (HTTP phase)"
echo "=============================================="
echo ""
echo "1. Fix DNS in Hostinger hPanel — A records -> 187.127.109.98"
echo "   @, www, admin"
echo ""
echo "2. Edit secrets if you have not yet:"
echo "   nano $APP_DIR/Backend/.env"
echo "   docker compose up -d --build"
echo ""
echo "3. After DNS works, get SSL:"
echo "   certbot --nginx -d anyamusicschool.com -d www.anyamusicschool.com -d admin.anyamusicschool.com"
echo ""
echo "4. First admin: https://admin.anyamusicschool.com/setup"
echo "5. Public site:  https://anyamusicschool.com"
echo ""
docker compose ps
