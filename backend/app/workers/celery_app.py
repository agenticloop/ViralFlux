import asyncio

from celery import Celery
from celery.schedules import crontab
from celery.signals import worker_process_init

from app.core.config import settings


@worker_process_init.connect
def _dispose_engine_after_fork(**_kwargs):
    """Dispose the SQLAlchemy async engine pool after Celery forks a worker.

    The parent process creates the asyncpg connection pool bound to its event
    loop. After fork the child inherits those connections, but asyncio.run()
    inside a task creates a *new* event loop — asyncpg then refuses to reuse
    the parent-loop connections and raises "future attached to a different loop".
    Disposing here drops all inherited connections so asyncpg lazily opens fresh
    ones on the child's own loop.
    """
    from app.core.database import engine

    asyncio.run(engine.dispose())

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
