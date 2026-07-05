from app.infra.db.session import get_pool
from app.modules.notifications.db.notification_queries import (
    claim_retryable_notifications,
)


async def retry_scheduled_notifications(*, limit: int = 100):
    """
    Claims retryable notifications whose retry time has arrived
    and enqueues them for delivery.

    Returns:
        Number of notifications claimed and enqueued.
    """

    pool = get_pool()

    async with pool.acquire() as conn:
        async with conn.transaction():
            return await claim_retryable_notifications(conn, limit)
