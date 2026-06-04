import re
from typing import Annotated

from pydantic import AfterValidator

EMAIL_REGEX = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")


def validate_email(value: str) -> str:
    if not EMAIL_REGEX.fullmatch(value):
        raise ValueError("Invalid email address")

    return value


Email = Annotated[str, AfterValidator(validate_email)]
