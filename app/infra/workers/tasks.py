from app.infra.workers.celery import celery_conn
from app.infra.workers.runtime import async_to_sync
from app.modules.notifications.workflows.notification_delivery import (
    PermanentFailureException,
    deliver_notification,
)


@celery_conn.task(bind=True, max_retries=5)
def send_email_task(self, notification_id: str):
    try:
        return async_to_sync(deliver_notification(notification_id))

    # Do NOT retry
    except PermanentFailureException:
        raise

    # Retry with exponential backoff
    except Exception as exc:
        countdown = 2**self.request.retries
        raise self.retry(exc=exc, countdown=countdown)
