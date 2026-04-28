from app.core.utils import NotificationState
from app.db.queries.delivery_attempts import (
    failed_delivery_attempt,
    succesfull_delivery_attempt,
)
from app.db.queries.notifications import (
    get_notification,
    increment_attempt_count,
    mark_failed,
    mark_processing,
    mark_sent,
)
from app.db.session import get_pool
from app.services.providers.mail import MailProvider


class PermanentFailureException(Exception):
    pass


async def process_notification(notification_id: str):
    pool = get_pool()

    async with pool.acquire() as conn:
        notification = await get_notification(conn, notification_id)

        # GUARD RAILS
        if not notification:
            return

        if notification["state"] in (
            NotificationState.SENT,
            NotificationState.FAIL,
        ):
            return

        if notification["attempt_count"] >= notification["max_attempts"]:
            raise PermanentFailureException("Max attempts reached")

        claimed = await mark_processing(conn, notification_id)

        if not claimed:
            claimed = notification  ## allowing retry to proceed even if already processing

    # Succesful Notification Delivery
    try:
        attempt_count = claimed["attempt_count"] + 1
        provider_response = await MailProvider.send(
            claimed,
            attempt_count,
        )

        async with pool.acquire() as conn:
            async with conn.transaction():
                attempt_number = await increment_attempt_count(
                    conn, notification_id
                )
                await succesfull_delivery_attempt(
                    conn,
                    notification_id,
                    attempt_number,
                    provider_response,
                )
                await mark_sent(conn, notification_id)
        return

    # Failed Notification Delivery
    except Exception as e:
        error_message = str(e)
        can_retry = MailProvider.can_retry(e, claimed)

        async with pool.acquire() as conn:
            async with conn.transaction():
                attempt_number = await increment_attempt_count(
                    conn, notification_id
                )
                await failed_delivery_attempt(
                    conn,
                    notification_id,
                    attempt_number,
                    "temporary_failure" if can_retry else "permanent_failure",
                    error_message,
                )

                if not can_retry or attempt_number >= claimed["max_attempts"]:
                    await mark_failed(conn, notification_id, error_message)
                    raise PermanentFailureException(error_message)

        raise
