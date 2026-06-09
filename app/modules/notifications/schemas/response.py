from datetime import datetime, timezone
from typing import Any, ClassVar, Literal

from pydantic import (
    UUID4,
    BaseModel,
    ConfigDict,
    Field,
)

from app.modules.notifications.constants import (
    NotificationState,
)


class PostNotificationResponseBody(BaseModel):
    notification_id: UUID4 = Field(
        ...,
        description="Notification ID (UUID4)",
    )
    state: NotificationState = Field(
        default=NotificationState.CREATED,
        title="Notification lifecycle state",
        description=(
            "Current lifecycle state of the notification. "
            "A notification transitions through defined states such as "
            "`created`, `queued`, `processing`, `sent`, or `failed`, "
            "which are tracked by Relays to represent its delivery progress."
        ),
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="UTC creation time (RFC3339)",
    )

    model_config: ClassVar[ConfigDict] = ConfigDict(extra="forbid")


class GetNotificationResponseBody(BaseModel):
    notification_id: UUID4 = Field(
        ...,
        description="Unique identifier for the notification",
    )
    channel: Literal["email", "sms", "webhook"] = Field(
        ...,
        description="Delivery channel for the notification",
    )
    recipient: str = Field(
        ...,
        description="Recipient identifier for the selected channel",
    )
    state: NotificationState = Field(
        ...,
        description="Current lifecycle state of the notification",
    )
    attempt_count: int = Field(
        ...,
        description="Number of delivery attempts made so far",
    )
    max_attempts: int = Field(
        ...,
        description="Maximum number of delivery attempts allowed",
    )
    created_at: datetime = Field(
        ...,
        description="UTC timestamp when the notification was created",
    )
    updated_at: datetime = Field(
        ...,
        description="UTC timestamp when the notification was last updated",
    )
    queued_at: datetime | None = Field(
        None,
        description="UTC timestamp when the notification was queued for delivery",
    )
    last_attempt_at: datetime | None = Field(
        None,
        description="UTC timestamp of the most recent delivery attempt",
    )
    # next_retry_at: datetime | None = Field(
    #     None,
    #     description="UTC timestamp when the next retry is scheduled, if applicable",
    # )
    sent_at: datetime | None = Field(
        None,
        description="UTC timestamp when the notification was successfully delivered",
    )
    last_error: str | None = Field(
        None,
        description="Error message from the most recent failed attempt, if any",
    )

    model_config: ClassVar[ConfigDict] = ConfigDict(extra="forbid")


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
