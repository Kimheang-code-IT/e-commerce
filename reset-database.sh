#!/usr/bin/env bash
# Delete ALL data in the ecommerce database and recreate empty tables.
#
# Usage (on server, from repo root):
#   chmod +x reset-database.sh
#   ./reset-database.sh
#
# Requires: docker compose, backend container running.

set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT"

if ! docker compose ps backend --status running >/dev/null 2>&1; then
  echo "Backend container is not running. Start the stack first:" >&2
  echo "  docker compose up -d backend db redis" >&2
  exit 1
fi

echo "==> Wiping all database data (PostgreSQL)..."
docker compose exec -T backend python app/scripts/reset_db.py --yes
echo "==> Done."
