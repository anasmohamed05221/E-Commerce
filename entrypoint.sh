#!/bin/sh
alembic upgrade head
PYTHONPATH=/app celery -A core.celery_app worker --loglevel=info --concurrency=1 &
exec gunicorn main:app -w 1 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000