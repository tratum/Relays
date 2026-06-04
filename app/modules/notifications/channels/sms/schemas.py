from typing import ClassVar

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
)

from .validators import Phone


class SMSPayload(BaseModel):
    to: Phone = Field(
        ...,
        min_length=4,
        description="Recipient Phone Number in E.164 format",
        examples=["+14155552671"],
    )
    message: str = Field(
        ...,
        min_length=1,
        max_length=160,
        description="SMS message body (max 160 characters)",
        examples=["Your verification code is 1234"],
    )

    model_config: ClassVar[ConfigDict] = ConfigDict(extra="forbid")
