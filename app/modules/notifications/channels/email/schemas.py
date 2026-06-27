from typing import ClassVar

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
)

from .validators import Email


class EmailPayload(BaseModel):
    to: Email = Field(
        ...,
        min_length=4,
        description="Recipient email address.",
        examples=["user@example.com"],
    )
    cc: list[Email] | None = Field(
        None,
        description="List of CC recipients.",
        examples=[["cc1@example.com", "cc2@example.com"]],
    )
    bcc: list[Email] | None = Field(
        None,
        description="List of BCC recipients.",
        examples=[["bcc1@example.com", "bcc2@example.com"]],
    )
    subject: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Subject line of the email.",
        examples=["Welcome to Relays"],
    )
    html_body: str = Field(
        ...,
        min_length=1,
        description="HTML content of the email body.",
        examples=[
            "<h1>Welcome to Relays</h1><p>Your account has been created successfully.</p>"
        ],
    )

    model_config: ClassVar[ConfigDict] = ConfigDict(extra="forbid")
