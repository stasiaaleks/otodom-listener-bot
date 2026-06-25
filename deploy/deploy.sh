#!/usr/bin/env bash
set -euo pipefail

# TODO: add repo pulling, etc. Currently a draft

cd "$(dirname "$0")/.."

if [[ ! -f .env ]]; then
  echo "Missing .env -- copy .env.sample to .env and fill it in first." >&2
  exit 1
fi

# Rebuild and restart in the background.
docker compose up -d --build

# TODO: add a health gate, e.g. poll http://127.0.0.1:8000/health until 200.
echo "Deployed. Check: curl -s http://127.0.0.1:8000/health"
