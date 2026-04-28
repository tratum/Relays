from app.services.notification_processor import (
    PermanentFailureException,
    process_notification,
)
from app.workers.celery import celery_conn
from app.workers.runtime import async_to_sync


@celery_conn.task(bind=True, max_retries=5)
def send_email_task(self, notification_id: str):
    try:
        return async_to_sync(process_notification(notification_id))

    # Do NOT retry
    except PermanentFailureException:
        raise

    # Retry with exponential backoff
    except Exception as exc:
        countdown = 2**self.request.retries
        raise self.retry(exc=exc, countdown=countdown)
