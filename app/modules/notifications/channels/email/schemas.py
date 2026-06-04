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
        description="Recipient Email",
        examples=["user@example.com"],
    )
    cc: list[Email] | None = Field(
        None,
        description="List of CC email recipients",
        examples=[["cc1@example.com", "cc2@example.com"]],
    )
    bcc: list[Email] | None = Field(
        None,
        description="List of BCC email recipients",
        examples=[["bcc1@example.com", "bcc2@example.com"]],
    )
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
