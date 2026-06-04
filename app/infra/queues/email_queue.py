from app.infra.workers.tasks import send_email_task


class EmailQueue:
    @staticmethod
    def enqueue(notification_id: str):
        send_email_task.apply_async(
            args=[notification_id],
        )
