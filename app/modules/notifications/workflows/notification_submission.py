from typing import Any

from fastapi import HTTPException, status

from app.core.hashing import canonical_hash
from app.core.idempotency import (
    complete_idempotency,
    get_idem_keys,
    insert_idem_keys,
)

from ..db.notification_queries import (
    create_notification,
    get_notification,
)
from ..schemas.request import NotificationRequestBody

API_KEY_ID = 1
HTTP_METHOD = "POST"
NOTIFICATIONS_PATH = "/v1/notifications"


def resolve_recipient(
    request: NotificationRequestBody,
) -> str:
    """
    Extracts a channel-specific recipient
    into a normalized string representation.
    """

    match request.channel:
        case "email" | "sms":
            return request.payload.to

        case "webhook":
            return str(request.payload.url)

        case _:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Unsupported notification channel.",
            )


async def submit_notification(
    conn,
    request: NotificationRequestBody,
    idempotency_key: str,
) -> tuple[dict[str, Any], bool]:
    recipient = resolve_recipient(
        request,
    )

    request_hash = canonical_hash(
        request.model_dump(mode="json"),
    )

    idempotency_record = await insert_idem_keys(
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

    if idempotency_record:
        notification_record = await create_notification(
            conn,
            channel=request.channel,
            recipient=recipient,
            payload=request.payload.model_dump(mode="json"),
            metadata=request.metadata,
        )

        await complete_idempotency(
            conn,
            idempotency_record["id"],
            notification_record["id"],
        )

        return notification_record, True

    # --------------------------------------------------
    # EXISTING REQUEST
    # --------------------------------------------------

    existing_idempotency_record = await get_idem_keys(
        conn,
        idempotency_key,
        API_KEY_ID,
        HTTP_METHOD,
        NOTIFICATIONS_PATH,
    )

    # --------------------------------------------------
    # IDEMPOTENCY FAILURE
    # --------------------------------------------------

    if not existing_idempotency_record:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=(
                "Unable to process idempotent request "
                "due to an internal error. "
                "Please retry."
            ),
        )

    # --------------------------------------------------
    # HASH MISMATCH
    # --------------------------------------------------

    if existing_idempotency_record["request_hash"] != request_hash:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "This Idempotency-Key has already "
                "been used with a different request "
                "payload. Use a new Idempotency-Key "
                "for different requests."
            ),
        )

    # --------------------------------------------------
    # REQUEST STILL PROCESSING
    # --------------------------------------------------

    if not existing_idempotency_record["notification_id"]:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "This request is still being "
                "processed. Retry the request "
                "with the same Idempotency-Key."
            ),
        )

    notification_record = await get_notification(
        conn,
        existing_idempotency_record["notification_id"],
    )

    # --------------------------------------------------
    # INCONSISTENT STATE
    # --------------------------------------------------

    if not notification_record:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=(
                "The request could not be completed "
                "due to an internal inconsistency. "
                "Please retry."
            ),
        )

    return notification_record, False
