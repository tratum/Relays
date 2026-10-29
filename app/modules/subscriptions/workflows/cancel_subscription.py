from uuid import UUID

import asyncpg
from core.error_codes import ErrorCode
from core.errors import APIException
from fastapi import status
from infra.db.session import get_pool

from ..db.subscriptions_queries import cancel_subscription as cancel_sub
from ..db.subscriptions_queries import get_subscription_by_workspace


async def cancel_subscription(
    conn: asyncpg.Connection,
    workspace_id: UUID,
) -> dict:

    sub = await get_subscription_by_workspace(
        conn,
        workspace_id,
    )

    if sub is None:
        raise APIException(
            status_code=status.HTTP_404_NOT_FOUND,
            code=ErrorCode.NOT_FOUND,
            message="Workspace has no subscription",
        )

    if sub["status"] == "cancelled":
        raise APIException(
            status_code=status.HTTP_409_CONFLICT,
            code=ErrorCode.CONFLICT,
            message="Subscription is already cancelled",
        )

    cancelled = await cancel_sub(
        conn,
        sub["id"],
    )

    # Query only cancels active subs if there is no record then the sub has been cacelled between our read and our update.
    if cancelled is None:
        raise APIException(
            status_code=status.HTTP_409_CONFLICT,
            code=ErrorCode.CONFLICT,
            message="Subscription is already cancelled",
        )

    return {"subscription": cancelled}


async def cancel_subscription_standalone(workspace_id: UUID) -> dict:
    """Own connection + transaction."""
    pool = get_pool()
    async with pool.acquire() as conn, conn.transaction():
        return await cancel_subscription(conn, workspace_id)
