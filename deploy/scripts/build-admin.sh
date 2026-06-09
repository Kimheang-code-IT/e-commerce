#!/usr/bin/env bash
# Build Frontend static admin for admin.anyamusicschool.com (Docker — no host pnpm required)
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
OUT_DIR="${1:-/var/www/anyamusicschool-admin}"
IMAGE_TAG="ecom-admin-build:latest"

if ! command -v docker >/dev/null 2>&1; then
  echo "docker is required. Install Docker or build locally and upload .output/public." >&2
  exit 1
fi

echo "Building admin image..."
docker build \
  -f "$ROOT/Frontend/Dockerfile" \
  -t "$IMAGE_TAG" \
  --build-arg NUXT_PUBLIC_SITE_URL=https://admin.anyamusicschool.com \
  --build-arg NUXT_PUBLIC_API_BASE=/api/v1 \
  --build-arg NUXT_PUBLIC_USE_BACKEND_API=true \
  "$ROOT/Frontend"

CONTAINER="$(docker create "$IMAGE_TAG")"
trap 'docker rm -f "$CONTAINER" >/dev/null 2>&1 || true' EXIT

TMP_DIR="$(mktemp -d)"
docker cp "$CONTAINER:/app/.output/public/." "$TMP_DIR/"

sudo mkdir -p "$OUT_DIR"
sudo rsync -a --delete "$TMP_DIR/" "$OUT_DIR/"
sudo chown -R www-data:www-data "$OUT_DIR"
rm -rf "$TMP_DIR"

echo "Admin static files deployed to $OUT_DIR"
