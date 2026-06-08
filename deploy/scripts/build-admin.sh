#!/usr/bin/env bash
# Build Frontend static admin for admin.anyamusicschool.com
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
OUT_DIR="${1:-/var/www/anyamusicschool-admin}"

cd "$ROOT/Frontend"

export NUXT_PUBLIC_SITE_URL=https://admin.anyamusicschool.com
export NUXT_PUBLIC_API_BASE=/api/v1
export NUXT_PUBLIC_USE_BACKEND_API=true

pnpm install --frozen-lockfile
pnpm exec nuxi generate

sudo mkdir -p "$OUT_DIR"
sudo rsync -a --delete .output/public/ "$OUT_DIR/"
sudo chown -R www-data:www-data "$OUT_DIR"

echo "Admin static files deployed to $OUT_DIR"
