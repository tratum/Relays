from typing import Any

## Unused Code Removed


async def record_delivery_attempt(
    conn,
    *,
    notification_id,
    attempt_number: int,
    status: str,
    provider_response: dict[str, Any] | None = None,
    error_message: str | None = None,
    provider_error_code: str | None = None,
    provider_message_id: str | None = None,
):
    query = """
    INSERT INTO delivery_attempts (
        notification_id,
        attempt_number,
        status,
        error_message,
        provider_error_code,
        provider_message_id,
        provider_response
    )
    VALUES (
        $1,
        $2,
        $3,
        $4,
        $5,
        $6,
        $7::jsonb
    )
    RETURNING id;
    """

    row = await conn.fetchrow(
        query,
        notification_id,
        attempt_number,
        status,
        error_message,
        provider_error_code,
        provider_message_id,
        provider_response,
    )

    if row is None:
        raise RuntimeError("Failed to record delivery attempt.")
