import re
from typing import Annotated

from pydantic import AfterValidator

PHONE_REGEX = re.compile(r"\+?[1-9]\d{7,14}")


def validate_phone(phone: str) -> str:
    if not PHONE_REGEX.fullmatch(phone):
        raise ValueError("Invalid phone number")

    return phone


Phone = Annotated[str, AfterValidator(validate_phone)]
