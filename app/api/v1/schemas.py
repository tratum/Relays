import re
from datetime import datetime, timezone
from enum import Enum
from typing import Annotated, Any, ClassVar, Literal

from pydantic import (
    UUID4,
    AnyUrl,
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
)


class NotificationState(str, Enum):
    created = "created"
    queued = "queued"
    processing = "processing"
    sent = "sent"
    failed = "failed"


# ------------------
# Payload schemas
# ------------------


class EmailPayload(BaseModel):
    subject: str | None = Field(
        None,
        max_length=255,
        description="Email subject line",
        examples=["Welcome to Relays"],
    )
    body: str = Field(
        ...,
        min_length=1,
        description="Email body content",
        examples=["Hello! Your notification has been sent."],
    )

    model_config: ClassVar[ConfigDict] = ConfigDict(extra="forbid")


class SMSPayload(BaseModel):
    message: str = Field(
        ...,
        min_length=1,
        max_length=160,
        description="SMS message body (max 160 characters)",
        examples=["Your verification code is 1234"],
    )

    model_config: ClassVar[ConfigDict] = ConfigDict(extra="forbid")


class WebhookPayload(BaseModel):
    url: AnyUrl = Field(
        ...,
        description="Webhook endpoint URL",
        examples=["https://example.com/webhook"],
    )
    body: dict[str, Any] = Field(
        ...,
        description="JSON payload sent to the webhook",
        examples=[{"event": "user.created"}],
    )

    model_config: ClassVar[ConfigDict] = ConfigDict(extra="forbid")


# ----------------------------
# Base request schema
# ----------------------------


class BaseNotificationRequest(BaseModel):
    to: str = Field(
        ...,
        min_length=1,
        description="Channel-specific recipient identifier",
        examples=["user@example.com", "+14155552671", "billing-service"],
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Optional metadata for tracing or auditing",
        examples=[{"source": "signup-service"}],
    )

    model_config: ClassVar[ConfigDict] = ConfigDict(extra="forbid")


# ----------------------------
# Channel-specific requests
# ----------------------------


class EmailNotificationRequest(BaseNotificationRequest):
    channel: Literal["email"] = Field(
        ...,
        description="Email notification channel",
    )
    payload: EmailPayload

    @field_validator("to")
    @classmethod
    def validate_email_recipient(cls, v: str) -> str:
        if not re.fullmatch(
            r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}",
            v,
        ):
            raise ValueError("Invalid email address")
        return v


class SMSNotificationRequest(BaseNotificationRequest):
    channel: Literal["sms"] = Field(
        ...,
        description="SMS notification channel",
    )
    payload: SMSPayload

    @field_validator("to")
    @classmethod
    def validate_phone_number(cls, v: str) -> str:
        # E.164-like format
        if not re.fullmatch(r"\+?[1-9]\d{7,14}", v):
            raise ValueError("Invalid phone number")
        return v


class WebhookNotificationRequest(BaseNotificationRequest):
    channel: Literal["webhook"] = Field(
        ...,
        description="Webhook notification channel",
    )
    payload: WebhookPayload

    @field_validator("to")
    @classmethod
    def validate_webhook_target(cls, v: str) -> str:
        # Logical identifier or service name
        if not re.fullmatch(r"[a-zA-Z0-9_-]{3,50}", v):
            raise ValueError("Invalid webhook recipient identifier")
        return v


# ----------------------------
# ------ POST response -------
# ----------------------------

NotificationRequestBody = Annotated[
    EmailNotificationRequest
    | SMSNotificationRequest
    | WebhookNotificationRequest,
    Field(discriminator="channel"),
]


class NotificationResponseBody(BaseModel):
    notification_id: UUID4 = Field(
        ...,
        description="Notification ID (UUID4)",
    )
    state: NotificationState = Field(
        default=NotificationState.created,
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


# ----------------------------
# ------ GET response -------
# ----------------------------


class GetNotificationResponseBody(BaseModel):
    notification_id: UUID4 = Field(
        ...,
        description="Unique identifier for the notification",
    )
    channel: Literal["email", "sms", "webhook"] = Field(
        ...,
        description="Delivery channel for the notification",
    )
    to: str = Field(
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
    queued_at: datetime | None = Field(
        None,
        description="UTC timestamp when the notification was queued for delivery",
    )
    last_attempt_at: datetime | None = Field(
        None,
        description="UTC timestamp of the most recent delivery attempt",
    )
    next_retry_at: datetime | None = Field(
        None,
        description="UTC timestamp when the next retry is scheduled, if applicable",
    )
    sent_at: datetime | None = Field(
        None,
        description="UTC timestamp when the notification was successfully delivered",
    )
    last_error: str | None = Field(
        None,
        description="Error message from the most recent failed attempt, if any",
    )
    updated_at: datetime = Field(
        ...,
        description="UTC timestamp when the notification was last updated",
    )

    model_config: ClassVar[ConfigDict] = ConfigDict(extra="forbid")
