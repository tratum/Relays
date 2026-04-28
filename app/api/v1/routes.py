from typing import Annotated

from fastapi import APIRouter, HTTPException, Path
from pydantic import UUID4
from starlette.responses import Response

from app.api.v1.schemas import (
    GetNotificationResponseBody,
    NotificationRequestBody,
    PostNotificationResponseBody,
    RequestValidationErrorModel,
)
from app.db.queries.notifications import (
    create_notification,
    get_notification,
    mark_queued,
)
from app.db.session import get_pool
from app.queues.email_queue import EmailQueue

router = APIRouter()


# --------------------------------------------------
# Health Check
# --------------------------------------------------
@router.get("/health")
async def health_check():
    return {"status": "ok"}


# --------------------------------------------------
# Create Notification
# --------------------------------------------------
@router.post(
    path="/notifications",
    status_code=201,
    response_model=PostNotificationResponseBody,
    summary="Relays Notification API",
    description=(
        "Accepts email, SMS, or webhook notifications. "
        "The payload schema is selected automatically using the `channel` field."
    ),
    responses={
        400: {"model": RequestValidationErrorModel},
        422: {"model": RequestValidationErrorModel},
    },
)
async def create_notify(req: NotificationRequestBody, res: Response):
    # ----------------------------------------
    # Extract recipient
    # ----------------------------------------
    if req.channel == "email":
        recipient = req.payload.to
    elif req.channel == "sms":
        recipient = req.payload.to
    elif req.channel == "webhook":
        recipient = str(req.payload.url)
    else:
        raise HTTPException(status_code=400, detail="Invalid channel")

    pool = get_pool()

    # ----------------------------------------
    # Persist notification (source of truth)
    # ----------------------------------------
    async with pool.acquire() as conn:
        async with conn.transaction():
            result = await create_notification(
                conn,
                channel=req.channel,
                recipient=recipient,
                payload=req.payload.model_dump(),
                metadata=req.metadata,
            )

    # ----------------------------------------
    # Enqueue job (execution layer)
    # ----------------------------------------
    try:
        EmailQueue.enqueue(result["id"])
    except Exception:
        # Do NOT mark queued if enqueue fails
        raise HTTPException(status_code=500, detail="Queue failure")

    # ----------------------------------------
    # Enqueueing
    # ----------------------------------------
    async with pool.acquire() as conn:
        await mark_queued(conn, result["id"])

    # ----------------------------------------
    # Response
    # ----------------------------------------
    res.headers["Location"] = f"/v1/notifications/{result['id']}"

    return PostNotificationResponseBody(
        notification_id=result["id"],
        created_at=result["created_at"],
    )


# --------------------------------------------------
# Get Notification Status
# --------------------------------------------------
@router.get(
    path="/notifications/{notification_id}",
    response_model=GetNotificationResponseBody,
    summary="Get notification status",
    description="Returns lifecycle state and delivery metadata",
    responses={
        400: {"model": RequestValidationErrorModel},
        422: {"model": RequestValidationErrorModel},
    },
)
async def get_notify(
    notification_id: Annotated[
        UUID4,
        Path(description="Notification ID returned during creation"),
    ],
):
    pool = get_pool()

    async with pool.acquire() as conn:
        result = await get_notification(conn, notification_id)

        if not result:
            raise HTTPException(
                status_code=404,
                detail="Notification not found",
            )

        return {
            "notification_id": result["id"],
            "channel": result["channel"],
            "recipient": result["recipient"],
            "state": result["state"],
            "attempt_count": result["attempt_count"],
            "max_attempts": result["max_attempts"],
            "created_at": result["created_at"],
            "updated_at": result["updated_at"],
            "last_attempt_at": result["last_attempt_at"],
            "sent_at": result["sent_at"],
            "last_error": result["last_error"],
            "queued_at": result["queued_at"],
        }
