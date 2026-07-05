from ..constants import DeliveryStatus, EmailNotificationProviders


async def record_delivery_attempt(
    conn,
    *,
    notification_id,
    attempt_number: int,
    status: DeliveryStatus,
    provider: EmailNotificationProviders,
    raw_provider_response: dict | None = None,
    error_message: str | None = None,
    provider_error_code: str | None = None,
    provider_message_id: str | None = None,
) -> None:
    query = """
    INSERT INTO delivery_attempts (
        notification_id,
        attempt_number,
        status,
        provider,
        error_message,
        provider_error_code,
        provider_message_id,
        raw_provider_response
    )
    VALUES (
        $1,
        $2,
        $3,
        $4,
        $5,
        $6,
        $7,
        $8::jsonb
    )
    RETURNING id;
    """

    row = await conn.fetchrow(
        query,
        notification_id,
        attempt_number,
        status,
        provider,
        error_message,
        provider_error_code,
        provider_message_id,
        raw_provider_response,
    )

    if row is None:
        raise RuntimeError("Failed to record delivery attempt.")
