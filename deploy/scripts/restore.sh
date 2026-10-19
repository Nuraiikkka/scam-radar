#!/usr/bin/env bash
set -euo pipefail

if [ "$#" -ne 1 ]; then
  echo "usage: $0 backups/scamradar-YYYYMMDD-HHMMSS.sql.gz"
  exit 1
fi

cd "$(dirname "$0")/.."
set -a
. ./.env
set +a

backup_file="$1"
if [ ! -f "$backup_file" ]; then
  echo "file not found: $backup_file"
  exit 1
fi

read -r -p "This replaces the current database with $backup_file. Type yes to continue: " answer
if [ "$answer" != "yes" ]; then
  echo "cancelled"
  exit 1
fi

docker compose -f docker-compose.prod.yml stop api worker
gunzip -c "$backup_file" | docker compose -f docker-compose.prod.yml exec -T postgres \
  psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -v ON_ERROR_STOP=1
docker compose -f docker-compose.prod.yml start api worker
echo "restore finished"
