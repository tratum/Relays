from datetime import datetime, timezone
from typing import Annotated
from uuid import uuid4

from fastapi import APIRouter, HTTPException, Path
from pydantic import UUID4
from starlette.responses import Response

from app.api.v1.schemas import (
    GetNotificationResponseBody,
    NotificationRequestBody,
    NotificationResponseBody,
    NotificationState,
)

router = APIRouter()


@router.get("/health")
async def health_check():
    return {"status": "ok"}


@router.post(
    path="/notifications",
    status_code=201,
    response_model=NotificationResponseBody,
    summary="Relays Notification API",
    description=(
        "Accepts email, SMS, or webhook notifications. "
        "The payload schema is selected automatically using the `channel` field."
    ),
)
async def notify(req: NotificationRequestBody, res: Response):
    notification_id = uuid4()
    state = NotificationState.created
    created_at = datetime.now(timezone.utc)

    # ---- Persistence layer (DB: source of truth) ----
    # await notifications_repo.insert(
    #     id=notification_id,
    #     channel=req.channel,
    #     to=req.to,
    #     payload=req.payload,
    #     state=state,
    #     created_at=created_at,
    # )

    # ---- Enqueue async delivery job (Redis / Celery) ----
    # enqueue_notification(notification_id)

    res.headers["Location"] = f"/v1/notifications/{notification_id}"
    return NotificationResponseBody(
        id=notification_id, state=state, created_at=created_at
    )


@router.get(
    path="/notifications/{notification_id}",
    response_model=GetNotificationResponseBody,
    summary="Get notification status",
    description=(
        "Returns the current lifecycle state and delivery metadata "
        "for a previously created notification."
    ),
)
async def get_notify(
    notification_id: Annotated[
        UUID4,
        Path(description="Notification ID returned during creation"),
    ],
):
    # ---- Fetch from DB (authoritative source) ----
    # notification = await notifications_repo.get_by_id(notification_id)
    #
    # if notification is None:
    #     raise HTTPException(status_code=404, detail="Notification not found")

    # ---- Placeholder response (until DB is wired) ----

    return GetNotificationResponseBody(
        notification_id=notification_id,
        channel="email",
        to="user@example.com",
        state=NotificationState.created,
        attempt_count=0,
        max_attempts=5,
        created_at=datetime.now(timezone.utc),
        queued_at=None,
        last_attempt_at=None,
        next_retry_at=None,
        sent_at=None,
        last_error=None,
        updated_at=datetime.now(timezone.utc),
    )
