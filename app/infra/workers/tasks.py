from app.core.constants import NotificationChannel
from app.infra.queues.notification_queue import NotificationQueue
from app.infra.workers.celery import celery_conn
from app.infra.workers.runtime import async_to_sync
from app.modules.notifications.workflows.notification_delivery import (
    deliver_notification,
)
from app.modules.notifications.workflows.retry_scheduler import (
    retry_scheduled_notifications,
)


@celery_conn.task
def deliver_notification_task(notification_id: str):
    return async_to_sync(deliver_notification(notification_id))


@celery_conn.task
def retry_scheduler_task():
    notifications = async_to_sync(retry_scheduled_notifications())

    for notification in notifications:
        NotificationQueue.enqueue(
            notification_id=str(notification["id"]),
            channel=NotificationChannel(notification["channel"]),
        )

    return len(notifications)
