import json

from pydantic import UUID4

from app.db.session import get_pool


async def create_notification(
    channel: str,
    recipient: str,
    payload: dict,
    metadata: dict | None = None,
) -> dict:
    pool = get_pool()
    query = """
    INSERT INTO notifications (channel, recipient, payload, metadata)
    VALUES ($1, $2, $3, $4)
    RETURNING id, state, created_at;
    """

    row = await pool.fetchrow(
        query,
        channel,
        recipient,
        json.dumps(payload),
        json.dumps(metadata) if metadata else None,
    )

    if row is None:
        raise RuntimeError("Insert failed: no row returned")

    return dict(row)


async def get_notifications(notification_id: UUID4):
    pool = get_pool()
    query = """
    SELECT id, channel, recipient, state, attempt_count, max_attempts, created_at, last_attempt_at, sent_at, last_error, updated_at
    FROM notifications
    WHERE id = $1;
    """

    row = await pool.fetchrow(query, notification_id)
    return dict(row) if row else None
