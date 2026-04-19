from celery import Celery
from core.config import settings

celery_app = Celery(
    "ecommerce",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
)

celery_app.conf.update(
    task_serializer="json",
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    task_always_eager=settings.CELERY_TASK_ALWAYS_EAGER,
    result_expires=3600
)

celery_app.autodiscover_tasks(["tasks"])