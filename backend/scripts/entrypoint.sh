#!/bin/sh
set -e

case "$1" in
  api)
    alembic upgrade head
    exec gunicorn app.main:app \
      --worker-class uvicorn.workers.UvicornWorker \
      --workers "${SCAMRADAR_API_WORKERS:-2}" \
      --bind 0.0.0.0:8000 \
      --forwarded-allow-ips "*" \
      --timeout 120 \
      --graceful-timeout 30 \
      --access-logfile -
    ;;
  worker)
    python -m app.workers.warmup
    exec celery -A app.workers.celery_app worker --beat \
      --loglevel INFO \
      --concurrency "${SCAMRADAR_WORKER_CONCURRENCY:-2}" \
      --schedule /data/media/celerybeat-schedule
    ;;
  migrate)
    exec alembic upgrade head
    ;;
  warmup)
    exec python -m app.workers.warmup
    ;;
  *)
    exec "$@"
    ;;
esac
