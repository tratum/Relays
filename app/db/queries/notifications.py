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
        metadata if metadata else None,
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
        last_attempt_at = now(),
        attempt_count = attempt_count + 1
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
        attempt_count = attempt_count + 1,
        last_attempt_at = now(),
        updated_at = now()
    WHERE id = $1;
    """
    await conn.execute(query, notification_id, error)


async def schedule_retry(conn, notification_id, next_retry, error):
    query = """
    UPDATE notifications
    SET attempt_count = attempt_count + 1,
        next_retry_at = $2,
        last_error = $3,
        state = 'queued',
        queued_at = now(),
        last_attempt_at = now(),
        updated_at = now()
    WHERE id = $1
    """
    await conn.execute(query, notification_id, next_retry, error)
