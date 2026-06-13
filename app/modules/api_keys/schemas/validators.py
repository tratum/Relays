from datetime import UTC, datetime
from typing import Annotated

from pydantic import AfterValidator


def validate_key_name(value: str) -> str:
    value = value.strip()

    if not value:
        raise ValueError("API-Key Name cannot be empty")

    if len(value) > 100:
        raise ValueError("API-Key Name cannot exceed 100 characters")

    return value


def validate_expires_at(
    value: datetime | None,
) -> datetime | None:
    if value is None:
        return value

    if value.tzinfo is None:
        raise ValueError("expires_at must be timezone-aware")

    if value <= datetime.now(UTC):
        raise ValueError("expires_at must be a future timestamp")

    return value


KeyName = Annotated[str, AfterValidator(validate_key_name)]
ExpiresAt = Annotated[datetime | None, AfterValidator(validate_expires_at)]
