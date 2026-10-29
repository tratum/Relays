from uuid import UUID

import asyncpg
from fastapi import status

from app.core.error_codes import ErrorCode
from app.core.errors import APIException
from app.infra.db.session import get_pool

from ..db.billing_periods_queries import insert_billing_period
from ..db.plan_queries import get_plan
from ..db.subscriptions_queries import insert_subscription


async def create_subscription(
    conn: asyncpg.Connection,
    workspace_id: UUID,
    plan_id: int,
    *,
    # TODO: Remove temp flag after payments module is integrated with this module
    payment_verified: bool = False,
):

    if not conn.is_in_transaction():
        raise RuntimeError(
            "create_subscription method must run inside a transaction"
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

    # TODO: Remove temp flag after payments module is integrated with this module
    if plan["price_cents"] > 0 and not payment_verified:
        raise APIException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            code=ErrorCode.CONFLICT,  # swap for a PAYMENT_REQUIRED code if you add one
            message="Payment is required for this plan",
        )

    try:
        sub = await insert_subscription(conn, workspace_id, plan_id)
    except asyncpg.UniqueViolationError:
        raise APIException(
            status_code=status.HTTP_409_CONFLICT,
            code=ErrorCode.CONFLICT,
            message="Workspace already has a subscription",
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


async def create_subscription_standalone(
    workspace_id: UUID,
    plan_id: int,
    *,
    payment_verified: bool = False,
) -> dict:
    """Standalone Create Subscripion Workflow (own connection + transaction)."""
    pool = get_pool()
    async with pool.acquire() as conn:
        async with conn.transaction():
            return await create_subscription(
                conn,
                workspace_id,
                plan_id,
                payment_verified=payment_verified,
            )
