from datetime import datetime

from pydantic import (
    UUID4,
    BaseModel,
    ConfigDict,
    Field,
)

from ..constants import APIKeyStatus


class APIKeysResponseBody(BaseModel):
    model_config = ConfigDict(
        frozen=True,
    )

    id: UUID4 = Field(
        ...,
        description="Unique identifier of the API key.",
        examples=["8f5a21c5-f49d-4c7e-b3f0-f2c6dfb0d1a2"],
    )

    name: str = Field(
        ...,
        description="Human-readable name assigned to the API key.",
        examples=["production"],
    )

    key_prefix: str = Field(
        ...,
        description="Public prefix used to identify the API key ",
        examples=["rly_a1b2c3d"],
    )

    api_key: str = Field(
        ...,
        description=(
            "Raw API key used for authenticating requests. "
            "This value is returned only once during key creation "
            "and must be stored securely by the client."
        ),
        examples=["rly_a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t"],
    )

    status: APIKeyStatus = Field(
        ...,
        description="Current status of the API key.",
        examples=["active"],
    )

    expires_at: datetime | None = Field(
        default=None,
        description=(
            "Timestamp after which the API key becomes unusable. "
            "Null indicates the API key does not expire."
        ),
        examples=[
            "2027-01-01T00:00:00Z",
        ],
    )

    created_at: datetime = Field(
        ...,
        description="Timestamp indicating when the API key was created.",
        examples=[
            "2026-06-11T12:00:00Z",
        ],
    )


class APIKeyListResponseBody(BaseModel):
    model_config = ConfigDict(
        frozen=True,
    )

    id: UUID4 = Field(
        ...,
        description="Unique identifier of the API key.",
        examples=["8f5a21c5-f49d-4c7e-b3f0-f2c6dfb0d1a2"],
    )

    name: str = Field(
        ...,
        description="Human-readable name assigned to the API key.",
        examples=["production"],
    )

    key_prefix: str = Field(
        ...,
        description="Public prefix used to identify the API key ",
        examples=["rly_a1b2c3d"],
    )

    status: APIKeyStatus = Field(
        ...,
        description="Current lifecycle status of the API key. ",
        examples=["active"],
    )

    expires_at: datetime | None = Field(
        default=None,
        description=(
            "Timestamp after which the API key becomes unusable. "
            "Null indicates the API key does not expire."
        ),
        examples=[
            "2027-01-01T00:00:00Z",
        ],
    )

    last_used_at: datetime | None = Field(
        default=None,
        description=(
            "Timestamp of the most recent successful authentication "
            "performed using this API key."
        ),
        examples=[
            "2026-06-11T15:45:30Z",
        ],
    )

    revoked_at: datetime | None = Field(
        default=None,
        description=(
            "Timestamp when the API key was revoked. "
            "Null indicates the key has not been revoked."
        ),
        examples=[
            "2026-07-01T09:00:00Z",
        ],
    )

    created_at: datetime = Field(
        ...,
        description="Timestamp indicating when the API key was created.",
        examples=[
            "2026-06-11T12:00:00Z",
        ],
    )

    updated_at: datetime = Field(
        ...,
        description=(
            "Timestamp indicating when the API key metadata was last modified."
        ),
        examples=[
            "2026-06-15T18:30:00Z",
        ],
    )
