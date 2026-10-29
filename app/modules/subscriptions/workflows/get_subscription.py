from uuid import UUID

import asyncpg
from core.error_codes import ErrorCode
from fastapi import status

from app.core.errors import APIException
from app.infra.db.session import get_pool

from ..db.billing_periods_queries import get_current_billing_period
from ..db.features_queries import get_plan_features
from ..db.plan_queries import get_plan
from ..db.subscriptions_queries import get_subscription_by_workspace


async def get_subscription(
    conn: asyncpg.Connection,
    workspace_id: UUID,
) -> dict:
    sub = await get_subscription_by_workspace(conn, workspace_id)

    if sub is None:
        raise APIException(
            status_code=status.HTTP_404_NOT_FOUND,
            code=ErrorCode.NOT_FOUND,
            message="Workspace has no subscription",
        )

    plan = await get_plan(conn, sub["plan_id"])
    features = await get_plan_features(conn, sub["plan_id"])
    billing_period = await get_current_billing_period(conn, sub["id"])

    return {
        "subscription": sub,
        "plan": plan,
        "features": features,
        "current_period": billing_period,  # None if renewal hasn't caught up
    }


async def get_subscription_standalone(workspace_id: UUID) -> dict:
    pool = get_pool()
    async with pool.acquire() as conn:
        return await get_subscription(conn, workspace_id)
