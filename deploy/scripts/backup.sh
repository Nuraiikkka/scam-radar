#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."
set -a
. ./.env
set +a

keep_days="${BACKUP_KEEP_DAYS:-14}"
stamp=$(date -u +%Y%m%d-%H%M%S)
target="backups/scamradar-${stamp}.sql.gz"
mkdir -p backups

docker compose -f docker-compose.prod.yml exec -T postgres \
  pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB" --no-owner --clean --if-exists \
  | gzip > "$target"

if [ ! -s "$target" ]; then
  echo "backup failed: $target is empty"
  exit 1
fi

find backups -name 'scamradar-*.sql.gz' -mtime "+${keep_days}" -delete
echo "backup written to $target"
