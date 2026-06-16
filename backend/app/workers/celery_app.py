from celery import Celery
from celery.schedules import crontab
from app.core.config import settings

celery_app = Celery(
    "viralflux",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=[
        "app.workers.tasks.video_tasks",
        "app.workers.tasks.analytics_tasks",
        "app.workers.tasks.schedule_tasks",
    ],
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
        "app.workers.tasks.schedule_tasks.*": {"queue": "video"},
    },
    beat_schedule={
        "scan-schedules-every-5-min": {
            "task": "app.workers.tasks.schedule_tasks.scan_schedules",
            "schedule": 300.0,  # every 5 minutes
        },
        "sync-analytics-daily": {
            "task": "app.workers.tasks.analytics_tasks.sync_analytics",
            "schedule": crontab(hour=2, minute=0),  # daily at 02:00
        },
    },
)
