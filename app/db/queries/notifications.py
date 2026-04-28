async def create_notification(
    conn,
    channel: str,
    recipient: str,
    payload: dict,
    metadata: dict | None = None,
) -> dict:
    query = """
    INSERT INTO notifications (channel, recipient, payload, metadata)
    VALUES ($1, $2, $3::jsonb, $4::jsonb)
    RETURNING id, state, created_at;
    """

    row = await conn.fetchrow(
        query,
        channel,
        recipient,
        payload,
        metadata,
    )

    if row is None:
        raise RuntimeError("Insert failed: no row returned")

    return dict(row)


async def get_notification(conn, notification_id):
    row = await conn.fetchrow(
        "SELECT * FROM notifications WHERE id = $1",
        notification_id,
    )
    return dict(row) if row else None


async def mark_processing(conn, notification_id):
    query = """
    UPDATE notifications
    SET state = 'processing',
        updated_at = now()
    WHERE id = $1
    AND state IN ('created', 'queued')
    RETURNING *;
    """
    row = await conn.fetchrow(query, notification_id)
    return dict(row) if row else None


async def mark_queued(conn, notification_id):
    query = """
    UPDATE notifications
    SET state = 'queued',
        queued_at = now(),
        updated_at = now()
    WHERE id = $1
    AND state IN ('created', 'processing');
    """
    await conn.execute(query, notification_id)


async def mark_sent(conn, notification_id):
    query = """
    UPDATE notifications
    SET state = 'sent',
        sent_at = now(),
        updated_at = now(),
        last_attempt_at = now()
    WHERE id = $1;
    """
    await conn.execute(
        query,
        notification_id,
    )


async def mark_failed(conn, notification_id, error):
    query = """
    UPDATE notifications
    SET state = 'failed',
        last_error = $2,
        last_attempt_at = now(),
        updated_at = now()
    WHERE id = $1;
    """
    await conn.execute(query, notification_id, error)


## Deprecated: This function was used for DB-driven retry scheduling (next_retry_at model).
# Retries are now fully managed by Celery with exponential backoff.
# Do not use this function to avoid double incrementing attempt_count and inconsistent state.

# async def schedule_retry(conn, notification_id, next_retry, error):
#     query = """
#     UPDATE notifications
#     SET attempt_count = attempt_count + 1,
#         next_retry_at = $2,
#         last_error = $3,
#         state = 'queued',
#         queued_at = now(),
#         last_attempt_at = now(),
#         updated_at = now()
#     WHERE id = $1
#     """
#     await conn.execute(query, notification_id, next_retry, error)


async def increment_attempt_count(conn, notification_id) -> int:
    query = """
    UPDATE notifications
    SET attempt_count = attempt_count + 1,
        last_attempt_at = now(),
        updated_at = now()
    WHERE id = $1
    RETURNING attempt_count;
    """
    row = await conn.fetchrow(query, notification_id)
    if not row:
        raise RuntimeError(f"Notification {notification_id} not found")
    return row["attempt_count"]
