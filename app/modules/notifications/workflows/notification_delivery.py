from app.infra.db.session import get_pool

from ..constants import (
    DeliveryStatus,
    NotificationState,
)
from ..db.delivery_attempts_queries import record_delivery_attempt
from ..db.notification_queries import (
    get_notification,
    increment_attempt_count,
    mark_failed,
    mark_processing,
    mark_sent,
)
from ..providers.email.fake import (
    FakeMailProvider,
)


class PermanentFailureException(Exception):
    """Notification can no longer be retried."""


# --------------------------------------------------
# Validation
# --------------------------------------------------


def validate_notification(notification: dict) -> None:
    if notification["state"] in (
        NotificationState.SENT,
        NotificationState.FAIL,
    ):
        raise PermanentFailureException("Notification already completed")

    if notification["attempt_count"] >= notification["max_attempts"]:
        raise PermanentFailureException("Max attempts reached")


# --------------------------------------------------
# Success Handling
# --------------------------------------------------


async def handle_success(
    notification_id: str,
    provider_response: dict,
):
    pool = get_pool()

    async with pool.acquire() as conn:
        async with conn.transaction():
            attempt_number = await increment_attempt_count(
                conn,
                notification_id,
            )

            await record_delivery_attempt(
                conn,
                notification_id=notification_id,
                attempt_number=attempt_number,
                status=DeliveryStatus.SUCCESS,
                provider_message_id="",
                provider_response=provider_response,
            )

            await mark_sent(
                conn,
                notification_id,
            )


# --------------------------------------------------
# Failure Handling
# --------------------------------------------------


async def handle_failure(
    notification_id: str,
    claimed: dict,
    error: Exception,
):
    pool = get_pool()

    error_message = str(error)

    can_retry = FakeMailProvider.can_retry(
        error,
        claimed,
    )

    async with pool.acquire() as conn:
        async with conn.transaction():
            attempt_number = await increment_attempt_count(
                conn,
                notification_id,
            )

            await record_delivery_attempt(
                conn,
                notification_id=notification_id,
                attempt_number=attempt_number,
                status=(
                    DeliveryStatus.TEMPORARY_FAILURE
                    if can_retry
                    else DeliveryStatus.PERMANENT_FAILURE
                ),
                provider_response=None,
                error_message=error_message,
                provider_error_code=None,
                provider_message_id=None,
            )

            if not can_retry or attempt_number >= claimed["max_attempts"]:
                await mark_failed(
                    conn,
                    notification_id,
                    error_message,
                )

                raise PermanentFailureException(error_message)


# --------------------------------------------------
# Notification Processing
# --------------------------------------------------


async def deliver_notification(
    notification_id: str,
):
    pool = get_pool()

    async with pool.acquire() as conn:
        notification = await get_notification(
            conn,
            notification_id,
        )

        # Guard Rails

        if not notification:
            return

        validate_notification(
            notification,
        )

        claimed = await mark_processing(
            conn,
            notification_id,
        )

        # Allow retry workers to continue
        # processing an already claimed record

        if not claimed:
            claimed = notification

    try:
        provider_response = await FakeMailProvider.send(
            claimed,
            claimed["attempt_count"] + 1,
        )

        await handle_success(
            notification_id,
            provider_response,
        )

    except Exception as exc:
        await handle_failure(
            notification_id,
            claimed,
            exc,
        )

        raise
