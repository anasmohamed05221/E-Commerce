#!/bin/sh
alembic upgrade head
PYTHONPATH=/app celery -A core.celery_app worker --loglevel=info --concurrency=1 &
PYTHONPATH=/app celery -A core.celery_app beat --loglevel=info --schedule /tmp/celerybeat-schedule &
exec gunicorn main:app -w 1 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000