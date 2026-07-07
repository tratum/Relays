from app.core.constants import NotificationChannel


class NotificationQueue:
    """
    Routes notifications to their channel-specific Celery queues.
    """

    @staticmethod
    def enqueue(
        notification_id: str,
        channel: NotificationChannel,
    ) -> None:
        from app.infra.workers.tasks import deliver_notification_task

        deliver_notification_task.apply_async(  # pyright: ignore[reportFunctionMemberAccess]
            args=(notification_id,),
            queue=channel.value,
        )
