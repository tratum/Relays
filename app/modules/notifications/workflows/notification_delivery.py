from app.infra.db.session import get_pool

from ..channels.email.schemas import EmailPayload
from ..constants import (
    DeliveryStatus,
    NotificationState,
)
from ..db.delivery_attempts_queries import (
    record_delivery_attempt,
)
from ..db.notification_queries import (
    get_notification,
    increment_attempt_count,
    mark_failed,
    mark_sent,
    schedule_retry,
)
from ..providers.email.registry import (
    email_provider_registry,
)
from ..providers.email.result import (
    ProviderResult,
)
from ..retry.policy import (
    calculate_next_retry_time,
)


class PermanentFailureException(Exception):
    """Notification can no longer be processed."""


def validate_delivery_eligibility(notification: dict) -> None:
    if notification["state"] in (
        NotificationState.SENT,
        NotificationState.FAIL,
    ):
        raise PermanentFailureException(
            f"Notification {notification['id']} has already reached a terminal state."
        )

    if notification["attempt_count"] >= notification["max_attempts"]:
        raise PermanentFailureException(
            f"Notification {notification['id']} has exhausted all retry attempts."
        )


async def persist_delivery_result(
    notification: dict,
    result: ProviderResult,
) -> None:
    pool = get_pool()

    async with pool.acquire() as conn:
        async with conn.transaction():
            attempt_number = await increment_attempt_count(
                conn,
                notification["id"],
            )

            await record_delivery_attempt(
                conn,
                notification_id=notification["id"],
                attempt_number=attempt_number,
                status=result.status,
                provider=result.provider,
                provider_message_id=result.provider_message_id,
                provider_error_code=result.provider_error_code,
                error_message=result.error_message,
                raw_provider_response=result.raw_provider_response,
            )

            match result.status:
                case DeliveryStatus.SUCCESS:
                    await mark_sent(
                        conn,
                        notification["id"],
                    )

                case DeliveryStatus.PERMANENT_FAILURE:
                    await mark_failed(
                        conn,
                        notification["id"],
                        result.error_message or "Unknown Provider Error",
                    )

                case DeliveryStatus.TEMPORARY_FAILURE:
                    if attempt_number >= notification["max_attempts"]:
                        await mark_failed(
                            conn,
                            notification["id"],
                            result.error_message
                            or "Maximum retry attempts reached.",
                        )
                        return

                    next_retry_at = calculate_next_retry_time(
                        attempt_number=attempt_number,
                    )

                    await schedule_retry(
                        conn,
                        notification["id"],
                        next_retry_at,
                    )

                case _:
                    raise RuntimeError(
                        f"Unsupported delivery status: {result.status!r}"
                    )


async def deliver_notification(
    notification_id: str,
) -> None:
    pool = get_pool()

    async with pool.acquire() as conn:
        notification = await get_notification(
            conn,
            notification_id,
        )

    if notification is None:
        return

    validate_delivery_eligibility(
        notification,
    )

    payload = EmailPayload.model_validate(
        notification["payload"],
    )

    provider = email_provider_registry.get(
        notification["provider"],
    )

    result = await provider.send(
        payload,
    )

    await persist_delivery_result(
        notification,
        result,
    )
