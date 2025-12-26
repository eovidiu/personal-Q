#!/bin/sh
set -e

case "${SERVICE_TYPE:-api}" in
  api)
    echo "Starting API server..."
    exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}
    ;;
  worker)
    echo "Starting Celery worker..."
    exec celery -A app.workers.celery_app worker --loglevel=info
    ;;
  beat)
    echo "Starting Celery beat..."
    exec celery -A app.workers.celery_app beat --loglevel=info
    ;;
  *)
    echo "Unknown SERVICE_TYPE: ${SERVICE_TYPE}"
    exit 1
    ;;
esac
