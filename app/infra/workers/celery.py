from datetime import timedelta

from celery import Celery

from app.core.config import config

celery_conn = Celery(
    "relays",
    broker=config.REDIS_URL,
    backend=config.REDIS_URL,
)

celery_conn.autodiscover_tasks(
    ["app.infra.workers"],
)

celery_conn.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    task_track_started=True,
    broker_transport_options={
        "visibility_timeout": 3600,
    },
    beat_schedule={
        "notification-retry-scheduler": {
            "task": "app.infra.workers.tasks.retry_scheduler_task",
            "schedule": timedelta(seconds=10),
            "options": {
                "queue": "scheduler",
            },
        },
    },
)
