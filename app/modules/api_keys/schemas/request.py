from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
)

from ..schemas.validators import ExpiresAt, KeyName


class APIKeysRequestBody(BaseModel):
    model_config = ConfigDict(
        frozen=True,
    )

    name: KeyName = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Human-readable API key name.",
        examples=["production"],
    )

    expires_at: ExpiresAt | None = Field(
        default=None,
        description="Optional expiration timestamp.",
        examples=["2027-01-01T00:00:00Z"],
    )
