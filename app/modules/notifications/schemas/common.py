from typing import Any, ClassVar

from pydantic import BaseModel, ConfigDict, Field


class BaseNotificationRequest(BaseModel):
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Optional metadata",
    )

    model_config: ClassVar[ConfigDict] = ConfigDict(
        extra="forbid"
    )