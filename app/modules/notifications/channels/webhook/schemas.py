from typing import Any, ClassVar

from pydantic import AnyUrl, BaseModel, ConfigDict, Field


class WebhookPayload(BaseModel):
    url: AnyUrl = Field(
        ...,
        description="A Valid Webhook endpoint URL",
        examples=["https://example.com/webhook"],
    )
    body: dict[str, Any] = Field(
        ...,
        description="JSON payload sent to the webhook",
        examples=[{"event": "user.created"}],
    )

    model_config: ClassVar[ConfigDict] = ConfigDict(extra="forbid")


