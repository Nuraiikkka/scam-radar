#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."
compose="docker compose -f docker-compose.prod.yml"

for attempt in $(seq 1 60); do
  status=$($compose ps --format '{{.Service}} {{.Health}}' api web | grep -c healthy || true)
  if [ "$status" = "2" ]; then
    echo "api and web are healthy"
    exit 0
  fi
  sleep 5
done

echo "services did not become healthy in time"
$compose ps
$compose logs --tail 50 api web
exit 1
