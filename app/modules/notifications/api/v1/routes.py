from typing import Annotated, Any

from fastapi import APIRouter, Header, HTTPException, Path, Response, status
from pydantic import UUID4

from app.core.errors import ErrorResponse
from app.core.hashing import canonical_hash
from app.infra.db.session import get_pool
from app.infra.queues.email_queue import EmailQueue
from app.modules.notifications.db.idempotency_queries import (
    complete_idempotency,
    get_idem_keys,
    insert_idem_keys,
)
from app.modules.notifications.db.notification_queries import (
    create_notification,
    get_notification,
    mark_queued,
)
from app.modules.notifications.schemas.requests import (
    NotificationRequestBody,
)
from app.modules.notifications.schemas.responses import (
    GetNotificationResponseBody,
    PostNotificationResponseBody,
)

router = APIRouter(tags=["notifications"])


# --------------------------------------------------
# Constants
# --------------------------------------------------

API_KEY_ID = 1  # Temporary Until Auth System Exists

HTTP_METHOD = "POST"

NOTIFICATIONS_PATH = "/v1/notifications"


# --------------------------------------------------
# Helpers
# --------------------------------------------------


def resolve_recipient(
    req: NotificationRequestBody,
) -> str:
    """
    Extracts a channel-specific recipient
    into a normalized string representation.
    """

    match req.channel:
        case "email" | "sms":
            return req.payload.to

        case "webhook":
            return str(req.payload.url)

        case _:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Unsupported notification channel.",
            )


def build_post_response(
    row: dict[str, Any],
) -> PostNotificationResponseBody:
    return PostNotificationResponseBody(
        notification_id=row["id"],
        created_at=row["created_at"],
    )


def build_get_response(
    row: dict[str, Any],
) -> GetNotificationResponseBody:
    return GetNotificationResponseBody(
        notification_id=row["id"],
        channel=row["channel"],
        recipient=row["recipient"],
        state=row["state"],
        attempt_count=row["attempt_count"],
        max_attempts=row["max_attempts"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
        queued_at=row["queued_at"],
        last_attempt_at=row["last_attempt_at"],
        sent_at=row["sent_at"],
        last_error=row["last_error"],
    )


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
    summary="Relays Notification API",
    description=(
        "Accepts email, SMS, or webhook notifications. "
        "The payload schema is selected automatically "
        "using the `channel` field."
    ),
    response_model=PostNotificationResponseBody,
    status_code=status.HTTP_201_CREATED,
    responses={
        400: {"model": ErrorResponse},
        401: {"model": ErrorResponse},
        403: {"model": ErrorResponse},
        404: {"model": ErrorResponse},
        409: {"model": ErrorResponse},
        500: {"model": ErrorResponse},
    },
)
async def create_notify(
    req: NotificationRequestBody,
    response: Response,
    idempotency_key: Annotated[
        str,
        Header(
            alias="Idempotency-Key",
            min_length=1,
        ),
    ],
):
    # --------------------------------------------------
    # Request Preparation
    # --------------------------------------------------

    pool = get_pool()

    recipient = resolve_recipient(req)

    request_hash = canonical_hash(req.model_dump(mode="json"))

    is_new = False

    result: dict[str, Any]

    # --------------------------------------------------
    # Idempotency + Persistence
    # --------------------------------------------------

    async with pool.acquire() as conn:
        async with conn.transaction():
            inserted = await insert_idem_keys(
                conn,
                idempotency_key,
                request_hash,
                API_KEY_ID,
                HTTP_METHOD,
                NOTIFICATIONS_PATH,
            )

            # --------------------------------------------------
            # NEW REQUEST
            # --------------------------------------------------

            if inserted:
                result = await create_notification(
                    conn,
                    channel=req.channel,
                    recipient=recipient,
                    payload=req.payload.model_dump(mode="json"),
                    metadata=req.metadata,
                )

                await complete_idempotency(
                    conn,
                    inserted["id"],
                    result["id"],
                )

                is_new = True

            # --------------------------------------------------
            # EXISTING REQUEST
            # --------------------------------------------------

            else:
                existing = await get_idem_keys(
                    conn,
                    idempotency_key,
                    API_KEY_ID,
                    HTTP_METHOD,
                    NOTIFICATIONS_PATH,
                )

                # --------------------------------------------------
                # IDEMPOTENCY FAILURE
                # --------------------------------------------------

                if not existing:
                    raise HTTPException(
                        status_code=500,
                        detail=(
                            "Unable to process "
                            "idempotent request due to "
                            "an internal error. "
                            "Please retry."
                        ),
                    )

                # --------------------------------------------------
                # HASH MISMATCH
                # --------------------------------------------------

                if existing["request_hash"] != request_hash:
                    raise HTTPException(
                        status_code=409,
                        detail=(
                            "This Idempotency-Key has "
                            "already been used with a "
                            "different request payload. "
                            "Use a new Idempotency-Key "
                            "for different requests."
                        ),
                    )

                # --------------------------------------------------
                # notification_id STILL NULL
                # --------------------------------------------------

                if not existing["notification_id"]:
                    raise HTTPException(
                        status_code=409,
                        detail=(
                            "This request is still "
                            "being processed. Retry "
                            "the request with the "
                            "same Idempotency-Key."
                        ),
                    )

                notification = await get_notification(
                    conn,
                    existing["notification_id"],
                )

                # --------------------------------------------------
                # INCONSISTENT IDEMPOTENCY STATE
                # --------------------------------------------------

                if not notification:
                    raise HTTPException(
                        status_code=500,
                        detail=(
                            "The request could not "
                            "be completed due to an "
                            "internal inconsistency. "
                            "Please retry."
                        ),
                    )

                result = notification

    # --------------------------------------------------
    # Queue Processing
    # --------------------------------------------------

    # ENQUEUE JOBS ONLY FOR NEW REQUESTS

    if is_new:
        try:
            EmailQueue.enqueue(str(result["id"]))

            # MARK STATUS = queued
            # ONLY AFTER SUCCESSFUL ENQUEUE

            async with pool.acquire() as conn:
                await mark_queued(
                    conn,
                    result["id"],
                )

        except Exception as exc:
            raise HTTPException(
                status_code=500,
                detail=(
                    "Failed to enqueue notification "
                    "for processing. Please retry."
                ),
            ) from exc

    # --------------------------------------------------
    # Response
    # --------------------------------------------------

    # 201 -> Newly Created Notification
    # 200 -> Idempotent Replay

    response.status_code = (
        status.HTTP_201_CREATED if is_new else status.HTTP_200_OK
    )

    response.headers["Location"] = f"/v1/notifications/{result['id']}"

    return build_post_response(result)


# --------------------------------------------------
# Get Notification Status
# --------------------------------------------------


@router.get(
    path="/notifications/{notification_id}",
    summary="Get notification status",
    description=("Returns lifecycle state and delivery metadata."),
    response_model=GetNotificationResponseBody,
    responses={
        404: {"model": ErrorResponse},
        500: {"model": ErrorResponse},
    },
)
async def get_notify(
    notification_id: Annotated[
        UUID4,
        Path(description=("Notification ID returned during creation.")),
    ],
):
    pool = get_pool()

    # --------------------------------------------------
    # Fetch Notification
    # --------------------------------------------------

    async with pool.acquire() as conn:
        result = await get_notification(
            conn,
            notification_id,
        )

    # --------------------------------------------------
    # Not Found
    # --------------------------------------------------

    if not result:
        raise HTTPException(
            status_code=404,
            detail=(
                "Notification not found. "
                "Verify the notification_id "
                "and try again."
            ),
        )

    # --------------------------------------------------
    # Build Response
    # --------------------------------------------------

    return build_get_response(result)
