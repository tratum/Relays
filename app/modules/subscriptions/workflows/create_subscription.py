from uuid import UUID

from fastapi import status

from app.core.error_codes import ErrorCode
from app.core.errors import APIException
from app.infra.db.session import get_pool

from ..db.billing_periods_queries import insert_billing_period
from ..db.plan_queries import get_plan
from ..db.subscriptions_queries import (
    get_subscription_by_workspace,
    insert_subscription,
)


async def create_subscription(
    workspace_id: UUID,
    plan_id: int,
):
    pool = get_pool()

    async with pool.acquire() as conn:
        existing_sub = await get_subscription_by_workspace(
            conn,
            workspace_id,
        )

        if existing_sub is not None:
            raise APIException(
                status_code=status.HTTP_409_CONFLICT,
                code=ErrorCode.CONFLICT,
                message="Workspace already has a subscription",
            )

        plan = await get_plan(conn, plan_id)

        if plan is None:
            raise APIException(
                status_code=status.HTTP_404_NOT_FOUND,
                code=ErrorCode.NOT_FOUND,
                message="Subscription plan not found",
            )

        if not plan["is_active"]:
            raise APIException(
                status_code=status.HTTP_409_CONFLICT,
                code=ErrorCode.CONFLICT,
                message="Subscription plan is inactive",
            )

        async with conn.transaction():
            sub = await insert_subscription(
                conn,
                workspace_id,
                plan_id,
            )

            billing_period = await insert_billing_period(
                conn,
                sub["id"],
                sub["started_at"],
            )

    return {
        "subscription": sub,
        "billing_period": billing_period,
    }
