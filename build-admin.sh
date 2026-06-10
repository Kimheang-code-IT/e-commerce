#!/usr/bin/env bash
# Deploy: git pull + website_business (Docker) + admin static + backend API
#
# Usage (on server):
#   chmod +x build-admin.sh
#   ./build-admin.sh
#
# Options:
#   --no-pull       Skip git pull
#   --admin-only    Rebuild admin static only (no Docker)
#   --website-only  Rebuild website_business container only (no admin)
#
# Env overrides:
#   ADMIN_OUT_DIR=/var/www/anyamusicschool-admin
#   GIT_BRANCH=main
#   COMPOSE_FILE=docker-compose.yml

set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT"

ADMIN_OUT_DIR="${ADMIN_OUT_DIR:-/var/www/anyamusicschool-admin}"
GIT_BRANCH="${GIT_BRANCH:-main}"
ADMIN_IMAGE_TAG="${ADMIN_IMAGE_TAG:-ecom-admin-build:latest}"
COMPOSE_FILE="${COMPOSE_FILE:-docker-compose.yml}"

SKIP_PULL=0
ADMIN_ONLY=0
WEBSITE_ONLY=0

for arg in "$@"; do
  case "$arg" in
    --no-pull) SKIP_PULL=1 ;;
    --admin-only) ADMIN_ONLY=1 ;;
    --website-only) WEBSITE_ONLY=1 ;;
    -h|--help)
      sed -n '2,14p' "$0"
      exit 0
      ;;
    *)
      echo "Unknown option: $arg (try --help)" >&2
      exit 1
      ;;
  esac
done

if [[ "$ADMIN_ONLY" -eq 1 && "$WEBSITE_ONLY" -eq 1 ]]; then
  echo "Use only one of --admin-only or --website-only." >&2
  exit 1
fi

if ! command -v docker >/dev/null 2>&1; then
  echo "docker is required." >&2
  exit 1
fi

if ! docker compose version >/dev/null 2>&1; then
  echo "docker compose plugin is required." >&2
  exit 1
fi

compose() {
  docker compose -f "$COMPOSE_FILE" "$@"
}

load_root_env() {
  if [[ -f "$ROOT/.env" ]]; then
  set -a
  # shellcheck disable=SC1091
  source "$ROOT/.env"
  set +a
  fi
}

git_pull() {
  if [[ "$SKIP_PULL" -eq 1 ]]; then
    echo "==> Skipping git pull (--no-pull)"
    return
  fi

  if [[ ! -d "$ROOT/.git" ]]; then
    echo "==> Not a git repo — skipping pull"
    return
  fi

  echo "==> Git sync ($GIT_BRANCH)"
  git fetch origin "$GIT_BRANCH"
  # Deploy server must mirror the repo (no local edits / chmod drift). Discard working-tree changes.
  git reset --hard "origin/$GIT_BRANCH"
  echo "    at $(git log -1 --oneline)"
}

deploy_docker_stack() {
  if [[ "$ADMIN_ONLY" -eq 1 ]]; then
    return
  fi

  load_root_env

  local services=(backend website)
  if [[ "$WEBSITE_ONLY" -eq 0 ]]; then
    services+=(celery-worker celery-beat)
  fi

  echo "==> Docker build: ${services[*]}"
  compose build "${services[@]}"

  echo "==> Docker up: ${services[*]}"
  compose up -d "${services[@]}"

  echo "==> Waiting for API health..."
  local i
  for i in $(seq 1 36); do
    if curl -sf http://127.0.0.1:8000/health >/dev/null 2>&1; then
      echo "    API healthy"
      break
    fi
    if [[ "$i" -eq 36 ]]; then
      echo "API not healthy — check: docker compose logs backend --tail 50" >&2
      exit 1
    fi
    sleep 5
  done

  if [[ "$WEBSITE_ONLY" -eq 0 ]]; then
    echo "==> Website container (website_business)"
    local code i
    code="000"
    for i in $(seq 1 12); do
      code="$(curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1:3001/ 2>/dev/null || echo 000)"
      if [[ "$code" != "000" ]]; then
        break
      fi
      sleep 5
    done
    echo "    http://127.0.0.1:3001/ → HTTP $code"
    if [[ "$code" == "000" ]]; then
      echo "    website not responding — check: docker compose logs website --tail 50" >&2
    fi
  fi
}

build_admin_image() {
  local -a build_args=(
    -f "$ROOT/Frontend/Dockerfile"
    -t "$ADMIN_IMAGE_TAG"
    --build-arg "NUXT_PUBLIC_SITE_URL=https://admin.anyamusicschool.com"
    --build-arg "NUXT_PUBLIC_API_BASE=/api/v1"
    --build-arg "NUXT_PUBLIC_USE_BACKEND_API=true"
    "$ROOT/Frontend"
  )

  if docker build "${build_args[@]}"; then
    return 0
  fi

  echo "==> Admin image export failed (often stale BuildKit cache) — pruning and retrying with --no-cache" >&2
  docker builder prune -f >/dev/null 2>&1 || true
  docker build --no-cache "${build_args[@]}"
}

deploy_admin_static() {
  if [[ "$WEBSITE_ONLY" -eq 1 ]]; then
    return
  fi

  echo "==> Building admin (Frontend static)"
  build_admin_image

  local container tmp_dir
  container="$(docker create "$ADMIN_IMAGE_TAG")"
  trap 'docker rm -f "$container" >/dev/null 2>&1 || true' RETURN

  tmp_dir="$(mktemp -d)"
  docker cp "$container:/app/.output/public/." "$tmp_dir/"
  docker rm -f "$container" >/dev/null 2>&1 || true
  trap - RETURN

  echo "==> Deploy admin → $ADMIN_OUT_DIR"
  sudo mkdir -p "$ADMIN_OUT_DIR"
  sudo rsync -a --delete "$tmp_dir/" "$ADMIN_OUT_DIR/"
  sudo chown -R www-data:www-data "$ADMIN_OUT_DIR"
  rm -rf "$tmp_dir"

  if [[ -f "$ADMIN_OUT_DIR/index.html" ]]; then
    echo "    admin index.html OK"
  else
    echo "admin deploy failed — index.html missing" >&2
    exit 1
  fi
}

print_summary() {
  echo ""
  echo "=============================================="
  echo " Deploy complete"
  echo "=============================================="
  compose ps 2>/dev/null || docker compose ps
  echo ""
  echo " Public site:  https://anyamusicschool.com"
  echo " Admin:        https://admin.anyamusicschool.com"
  echo ""
}

main() {
  echo "Deploy from: $ROOT"
  echo ""

  git_pull
  deploy_docker_stack
  deploy_admin_static
  print_summary
}

main
