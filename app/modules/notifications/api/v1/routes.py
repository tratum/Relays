from typing import Annotated

from fastapi import (
    APIRouter,
    Depends,
    Header,
    Path,
    Request,
    Response,
    status,
)
from pydantic import UUID4

from app.core.error_codes import ErrorCode
from app.core.errors import APIException, ErrorResponse
from app.infra.db.session import get_pool
from app.infra.guards.api_key import authenticate_api_key
from app.infra.queues.email_queue import EmailQueue

from ...db.notification_queries import (
    get_notification,
    mark_queued,
)
from ...schemas.request import (
    NotificationRequestBody,
)
from ...schemas.response import (
    GetNotificationResponseBody,
    PostNotificationResponseBody,
    build_get_response,
    build_post_response,
)
from ...workflows.notification_submission import submit_notification

router = APIRouter(tags=["Notifications API"])

# --------------------------------------------------
# Health Check
# --------------------------------------------------


@router.get("/notifications/health", summary="Notifications API Health Check")
async def health_check():
    return {"status": "ok"}


# --------------------------------------------------
# Send Notification
# --------------------------------------------------


@router.post(
    path="/notifications",
    summary="Send Notification",
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
    dependencies=[Depends(authenticate_api_key)],
)
async def create_notify(
    req: Request,
    response: Response,
    body: NotificationRequestBody,
    idempotency_key: Annotated[
        UUID4,
        Header(
            alias="Idempotency-Key",
        ),
    ],
):
    pool = get_pool()

    async with pool.acquire() as conn:
        async with conn.transaction():
            notification_record, is_new_request = await submit_notification(
                conn=conn,
                request=body,
                idempotency_key=str(idempotency_key),
                workspace_id=req.state.workspace_id,
                api_key_id=req.state.api_key_id,
            )

        # Queue Processing

        if is_new_request:
            try:
                EmailQueue.enqueue(str(notification_record["id"]))
                async with pool.acquire() as conn:
                    await mark_queued(
                        conn,
                        notification_record["id"],
                    )

            except Exception:
                raise APIException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    code=ErrorCode.INTERNAL_ERROR,
                    message="Failed to Enqueue Notification for Processing. Please retry.",
                )

            response.status_code = (
                status.HTTP_201_CREATED
                if is_new_request
                else status.HTTP_200_OK
            )
            response.headers["Location"] = (
                f"/v1/notifications/{notification_record['id']}"
            )

            return build_post_response(notification_record)


# --------------------------------------------------
# Get Notification Status
# --------------------------------------------------


@router.get(
    path="/notifications/{notification_id}",
    summary="Get Notification Status",
    description=("Returns lifecycle state and delivery metadata."),
    response_model=GetNotificationResponseBody,
    responses={
        404: {"model": ErrorResponse},
        500: {"model": ErrorResponse},
    },
    dependencies=[Depends(authenticate_api_key)],
)
async def get_notify(
    notification_id: Annotated[
        UUID4,
        Path(description=("Notification ID returned during creation.")),
    ],
):
    pool = get_pool()

    async with pool.acquire() as conn:
        result = await get_notification(
            conn,
            notification_id,
        )

    if not result:
        raise APIException(
            status_code=status.HTTP_404_NOT_FOUND,
            code=ErrorCode.NOT_FOUND,
            message="Notification not found. Verify the notification_id and try again.",
        )

    return build_get_response(result)
