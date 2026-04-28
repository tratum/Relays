from celery import Celery

from app.core.config import config

celery_conn = Celery(
    "relays",
    broker=config.REDIS_URL,
    backend=config.REDIS_URL,
)

celery_conn.autodiscover_tasks(["app.workers"])

celery_conn.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    task_track_started=True,
    broker_transport_options={"visibility_timeout": 3600},
    task_routes={
        "app.workers.tasks.send_email_task": {"queue": "email"},
    },
)
