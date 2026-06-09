#!/usr/bin/env bash
# Run on Hostinger VPS as root after: cd /opt/e-comerce && git pull
# Full deploy: docker stack + admin build + nginx HTTP
set -euo pipefail

cd /opt/e-comerce

echo "=== 1/5 Pull latest code ==="
git pull

echo "=== 2/5 Check Backend/.env ==="
if grep -q 'CHANGE_ME' Backend/.env 2>/dev/null; then
  echo "ERROR: Edit Backend/.env first — replace CHANGE_ME passwords and JWT_SECRET_KEY"
  echo "  nano /opt/e-comerce/Backend/.env"
  echo "  JWT: openssl rand -hex 32"
  exit 1
fi

echo "=== 3/5 Docker build + start ==="
docker compose up -d --build

echo "=== 4/5 Build admin ==="
chmod +x deploy/scripts/build-admin.sh
./deploy/scripts/build-admin.sh

echo "=== 5/5 Nginx HTTP config ==="
mkdir -p /var/www/certbot
cp deploy/nginx/anyamusicschool.http.conf /etc/nginx/sites-available/anyamusicschool
ln -sf /etc/nginx/sites-available/anyamusicschool /etc/nginx/sites-enabled/anyamusicschool
rm -f /etc/nginx/sites-enabled/default
nginx -t && systemctl reload nginx

echo ""
echo "=== Health checks ==="
curl -sf http://127.0.0.1:8000/health && echo " API OK" || echo " API FAILED"
curl -s -o /dev/null -w " Website HTTP %{http_code}\n" http://127.0.0.1:3001/
test -f /var/www/anyamusicschool-admin/index.html && echo " Admin static OK" || echo " Admin static MISSING"
docker compose ps

echo ""
echo "=== Next steps ==="
echo "1. Hostinger DNS: @, www, admin -> 187.127.109.98"
echo "2. SSL: certbot --nginx -d anyamusicschool.com -d www.anyamusicschool.com -d admin.anyamusicschool.com"
echo "3. First user: https://admin.anyamusicschool.com/setup"
echo "4. Public site: https://anyamusicschool.com"
