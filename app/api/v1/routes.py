from datetime import datetime, timezone
from typing import Annotated
from uuid import uuid4

from fastapi import APIRouter, HTTPException, Path
from pydantic import UUID4
from starlette.responses import Response

from app.api.v1.schemas import (
    GetNotificationResponseBody,
    NotificationRequestBody,
    NotificationState,
    PostNotificationResponseBody,
    RequestValidationErrorModel,
)
from app.db.queries.notifications import create_notification, get_notifications

router = APIRouter()


@router.get("/health")
async def health_check():
    return {"status": "ok"}


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
        400: {
            "model": RequestValidationErrorModel,
            "description": "Bad Request",
        },
        422: {
            "model": RequestValidationErrorModel,
            "description": "Validation Error",
        },
    },
)
async def create_notify(req: NotificationRequestBody, res: Response):
    # Extract recipient based on channel
    if req.channel == "email":
        recipient = req.payload.to
    elif req.channel == "sms":
        recipient = req.payload.to
    elif req.channel == "webhook":
        recipient = str(req.payload.url)
    else:
        raise ValueError("Invalid Channel")

    # ---- Persistence layer (DB: source of truth) ----
    result = await create_notification(
        channel=req.channel,
        recipient=recipient,
        payload=req.payload.model_dump(),
        metadata=req.metadata,
    )

    # ---- Response ----
    res.headers["Location"] = f"/v1/notifications/{result['id']}"
    return PostNotificationResponseBody(
        notification_id=result["id"],
        state=result["state"],
        created_at=result["created_at"],
    )

    # ---- Enqueue async delivery job (Redis / Celery) ----
    # enqueue_notification(notification_id)


@router.get(
    path="/notifications/{notification_id}",
    response_model=GetNotificationResponseBody,
    summary="Get notification status",
    description=(
        "Returns the current lifecycle state and delivery metadata "
        "for a previously created notification."
    ),
    responses={
        400: {
            "model": RequestValidationErrorModel,
            "description": "Bad Request",
        },
        422: {
            "model": RequestValidationErrorModel,
            "description": "Validation Error",
        },
    },
)
async def get_notify(
    notification_id: Annotated[
        UUID4,
        Path(description="Notification ID returned during creation"),
    ],
):
    result = await get_notifications(notification_id)
    if not result:
        raise HTTPException(status_code=404, detail="Notification Not found")

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
    }
