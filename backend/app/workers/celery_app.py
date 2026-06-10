from celery import Celery
from app.core.config import settings

celery_app = Celery(
    "viralflux",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=["app.workers.tasks.video_tasks", "app.workers.tasks.analytics_tasks"]
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone=settings.TIMEZONE,
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    task_routes={
        "app.workers.tasks.video_tasks.*": {"queue": "video"},
        "app.workers.tasks.analytics_tasks.*": {"queue": "analytics"},
    }
)
