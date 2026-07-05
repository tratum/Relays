from datetime import datetime
from typing import ClassVar

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
)

from ....channels.email.validators import Email


class MailRelaySender(BaseModel):
    email: Email = Field(
        ...,
        description="Sender email address.",
    )
    name: str = Field(
        ...,
        description="Sender display name.",
    )

    model_config: ClassVar[ConfigDict] = ConfigDict(
        extra="forbid",
    )


class MailRelayRecipient(BaseModel):
    email: Email = Field(
        ...,
        description="Recipient email address.",
    )
    name: str | None = Field(
        default=None,
        description="Recipient display name.",
    )

    model_config: ClassVar[ConfigDict] = ConfigDict(
        extra="forbid",
    )


class MailRelaySendRequest(BaseModel):
    from_: MailRelaySender = Field(
        ...,
        serialization_alias="from",
        description="Sender information.",
    )

    to: list[MailRelayRecipient] = Field(
        ...,
        min_length=1,
        description="List of recipients.",
    )

    subject: str = Field(
        ...,
        description="Email subject.",
    )

    html_part: str | None = Field(
        default=None,
        description="HTML email body.",
    )

    text_part: str | None = Field(
        default=None,
        description="Plain text email body.",
    )

    text_part_auto: bool = Field(
        default=True,
        description="Automatically generate a plain text body from the HTML body.",
    )

    model_config: ClassVar[ConfigDict] = ConfigDict(
        extra="forbid",
    )


class MailRelaySendResponse(BaseModel):
    id: int = Field(
        ...,
        description="MailRelay message identifier.",
    )

    created_at: datetime = Field(
        ...,
        description="Timestamp when MailRelay accepted the email.",
    )

    email: Email = Field(
        ...,
        description="Recipient email address.",
    )

    subscriber_id: int | None = Field(
        None,
        description="MailRelay subscriber identifier.",
    )

    model_config: ClassVar[ConfigDict] = ConfigDict(
        extra="forbid",
    )


class MailRelayErrorResponse(BaseModel):
    error: str = Field(
        ...,
        description="MailRelay error message.",
    )

    model_config: ClassVar[ConfigDict] = ConfigDict(
        extra="forbid",
    )
