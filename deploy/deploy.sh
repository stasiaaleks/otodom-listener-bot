#!/usr/bin/env bash

# sudo deploy/deploy.sh  # update + restart
# sudo deploy/deploy.sh --install   # also install prerequisites
set -euo pipefail

APP_DIR="$(cd "$(dirname "$0")/.." && pwd)"   # -> /opt/otodom-bot on the VM
BRANCH="${BRANCH:-main}"
HEALTH_URL="http://127.0.0.1:8000/health"

cd "$APP_DIR"

log() { printf '\n\033[1;34m==>\033[0m %s\n' "$*"; }

[[ $EUID -eq 0 ]] || { echo "Run as root (sudo $0 ...)"; exit 1; }

install_prereqs() {
  log "Installing prerequisites (git, curl, docker + compose plugin)"
  apt-get update
  apt-get install -y ca-certificates curl git
  if ! command -v docker >/dev/null 2>&1; then
    curl -fsSL https://get.docker.com | sh   # installs docker engine + compose v2
  fi
  systemctl enable --now docker
}

wait_for_db() {
  log "Waiting for Postgres to accept connections"
  for _ in $(seq 1 30); do
    if docker compose exec -T db pg_isready -q; then return 0; fi
    sleep 1
  done
  echo "Postgres did not become ready in time" >&2
  exit 1
}

migrate() {
  log "Applying database migrations"
  docker compose up -d db
  wait_for_db
  # No standalone migration tool yet
  echo "  (no migration tool configured; schema is created on app startup)"
}

[[ "${1:-}" == "--install" ]] && install_prereqs

[[ -f .env ]] || { echo "Missing $APP_DIR/.env"; exit 1; }

log "Pulling latest code ($BRANCH)"
git fetch --prune origin
git checkout "$BRANCH"
git pull --ff-only origin "$BRANCH"

log "Building images"
docker compose build

migrate

log "Restarting containers"
docker compose up -d --remove-orphans

if systemctl is-active --quiet nginx; then
  log "Reloading nginx"
  nginx -t && systemctl reload nginx
else
  log "nginx not running — skipping (run deploy/setup-tls.sh for first-time TLS)"
fi

log "Waiting for app health at $HEALTH_URL"
for _ in $(seq 1 30); do
  if curl -fsS "$HEALTH_URL" >/dev/null 2>&1; then
    log "Deployed and healthy."
    exit 0
  fi
  sleep 2
done

echo "Health check failed after timeout — recent app logs:" >&2
docker compose logs --tail=50 app >&2
exit 1
