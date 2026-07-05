from typing import Any


async def create_notification(
    conn,
    workspace_id,
    api_key_id,
    channel: str,
    provider: str,
    recipient: str,
    payload: dict[str, Any],
    metadata: dict[str, Any] | None = None,
) -> dict:
    query = """
    INSERT INTO notifications (
        workspace_id,
        api_key_id,
        channel,
        provider,
        recipient,
        payload,
        metadata
    )
    VALUES (
        $1,
        $2,
        $3,
        $4,
        $5,
        $6::jsonb,
        $7::jsonb
    )
    RETURNING
        id,
        state,
        created_at;
    """

    row = await conn.fetchrow(
        query,
        workspace_id,
        api_key_id,
        channel,
        provider,
        recipient,
        payload,
        metadata,
    )

    if row is None:
        raise RuntimeError("Insert failed.")

    return dict(row)


async def get_notification(conn, notification_id):
    query = """
    SELECT
        id,
        workspace_id,
        api_key_id,
        channel,
        provider,
        recipient,
        payload,
        metadata,
        state,
        attempt_count,
        max_attempts,
        next_retry_at,
        queued_at,
        last_attempt_at,
        last_error,
        sent_at,
        created_at,
        updated_at
    FROM notifications
    WHERE id = $1;
    """

    row = await conn.fetchrow(query, notification_id)
    return dict(row) if row else None


async def mark_queued(conn, notification_id):
    query = """
    UPDATE notifications
    SET
        state = 'queued',
        queued_at = now(),
        updated_at = now()
    WHERE
        id = $1
        AND state = 'created'
    RETURNING *;
    """

    row = await conn.fetchrow(query, notification_id)
    return dict(row) if row else None


async def mark_sent(conn, notification_id):
    query = """
    UPDATE notifications
    SET
        state = 'sent',
        sent_at = now(),
        last_attempt_at = now(),
        updated_at = now(),
        next_retry_at = NULL
    WHERE id = $1
    RETURNING *;
    """

    row = await conn.fetchrow(query, notification_id)
    return dict(row) if row else None


async def mark_failed(
    conn,
    notification_id,
    error: str,
):
    query = """
    UPDATE notifications
    SET
        state = 'failed',
        last_error = $2,
        last_attempt_at = now(),
        updated_at = now(),
        next_retry_at = NULL
    WHERE id = $1
    RETURNING *;
    """

    row = await conn.fetchrow(
        query,
        notification_id,
        error,
    )

    return dict(row) if row else None


async def increment_attempt_count(
    conn,
    notification_id,
) -> int:
    query = """
    UPDATE notifications
    SET
        attempt_count = attempt_count + 1,
        last_attempt_at = now(),
        updated_at = now()
    WHERE id = $1
    RETURNING attempt_count;
    """

    row = await conn.fetchrow(
        query,
        notification_id,
    )

    if row is None:
        raise RuntimeError(f"Notification {notification_id} not found.")

    return row["attempt_count"]


async def schedule_retry(
    conn,
    notification_id,
    next_retry_at,
):
    query = """
    UPDATE notifications
    SET
        state = 'queued',
        next_retry_at = $2,
        updated_at = now()
    WHERE id = $1
    RETURNING *;
    """

    row = await conn.fetchrow(query, notification_id, next_retry_at)

    return dict(row) if row else None


async def claim_retryable_notifications(conn, limit: int = 100):
    query = """
    WITH claimed AS (
        SELECT id
        FROM notifications
        WHERE
          state = 'queued'
          AND next_retry_at IS NOT NULL
          AND next_retry_at <= now()
        ORDER BY
          next_retry_at ASC,
          created_at ASC
        LIMIT $1
        FOR UPDATE SKIP LOCKED
    )
    UPDATE notifications n
    SET
      state = 'processing',
      next_retry_at = NULL,
      updated_at = now()
    FROM claimed
    WHERE n.id = claimed.id
    RETURNING n.*;
    """

    rows = await conn.fetchrow(query, limit)

    return [dict(row) for row in rows]
