from typing import Annotated

from fastapi import APIRouter, Header, HTTPException, Path
from pydantic import UUID4
from starlette.responses import Response

from app.api.v1.schemas import (
    GetNotificationResponseBody,
    NotificationRequestBody,
    PostNotificationResponseBody,
    RequestValidationErrorModel,
)
from app.core.utils import canonical_hash
from app.db.queries.idempotency import (
    complete_idempotency,
    get_idem_keys,
    insert_idem_keys,
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
# POST Notification
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
async def create_notify(
    req: NotificationRequestBody,
    res: Response,
    idempotency_key: str | None = Header(None, alias="Idempotency-Key"),
):
    if req.channel == "email":
        recipient = req.payload.to
    elif req.channel == "sms":
        recipient = req.payload.to
    elif req.channel == "webhook":
        recipient = str(req.payload.url)
    else:
        raise HTTPException(
            status_code=400,
            detail="Invalid channel. Supported values are 'email', 'sms', or 'webhook'.",
        )

    api_key_id = 1  # Temporary Until AUTH System is configured
    method = "POST"
    path = "/v1/notifications"
    request_hash = canonical_hash(req.model_dump())

    pool = get_pool()

    if not idempotency_key:
        raise HTTPException(
            status_code=400,
            detail="Missing required header: Idempotency-Key. Provide a unique key for each request.",
        )

    async with pool.acquire() as conn:
        async with conn.transaction():
            inserted = await insert_idem_keys(
                conn,
                idempotency_key,
                request_hash,
                api_key_id,
                method,
                path,
            )

            # NEW REQUEST
            if inserted:
                result = await create_notification(
                    conn,
                    channel=req.channel,
                    recipient=recipient,
                    payload=req.payload.model_dump(),
                    metadata=req.metadata,
                )
                await complete_idempotency(
                    conn,
                    inserted["id"],
                    result["id"],
                )
                is_new = True

            # EXISTING REQUEST
            else:
                existing = await get_idem_keys(
                    conn,
                    idempotency_key,
                    api_key_id,
                    method,
                    path,
                )

                # Idempotency Fails
                if not existing:
                    raise HTTPException(
                        status_code=500,
                        detail="Unable to process idempotent request due to an internal error. Please retry.",
                    )

                # HASH MISMATCH
                if existing["request_hash"] != request_hash:
                    raise HTTPException(
                        status_code=409,
                        detail="This Idempotency-Key has already been used with a different request payload. Use a new Idempotency-Key for different requests.",
                    )

                # notification_id BEING NULL
                if not existing["notification_id"]:
                    raise HTTPException(
                        status_code=409,
                        detail="This request is still being processed. Retry the request with the same Idempotency-Key.",
                    )

                # INCONSISTENT IDEMPOTENCY STATE
                notification = await get_notification(
                    conn,
                    existing["notification_id"],
                )
                if not notification:
                    raise HTTPException(
                        status_code=500,
                        detail="The request could not be completed due to an internal inconsistency. Please retry.",
                    )

                result = notification
                is_new = False

    # ENQUEUE JOB FOR NEW REQUESTS
    if is_new:
        try:
            EmailQueue.enqueue(result["id"])
            # MARKING STATUS = queued FOR NEW REQUESTS
            async with pool.acquire() as conn:
                await mark_queued(conn, result["id"])
        except Exception:
            # DO NOT MARK queued if enqueue fails
            raise HTTPException(
                status_code=500,
                detail="Failed to enqueue notification for processing. Please retry.",
            )

    # RESPONSE

    # Status code correctness
    if is_new:
        res.status_code = 201
    else:
        res.status_code = 200

    res.headers["Location"] = f"/v1/notifications/{result['id']}"

    return PostNotificationResponseBody(
        notification_id=result["id"],
        created_at=result["created_at"],
    )


# --------------------------------------------------
# Get Notification
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
                detail="Notification not found. Verify the notification_id and try again.",
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
