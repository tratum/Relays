from typing import Annotated

from pydantic import (
    AfterValidator,
    EmailStr,
)

RESERVED_WORKSPACE_NAMES = {
    "owner",
    "member",
    "api",
    "admin",
    "support",
    "billing",
    "settings",
    "dashboard",
    "auth",
    "login",
    "signup",
}


def validate_email_address(
    value: EmailStr,
) -> EmailStr:
    return value.strip().lower()


def validate_user_name(
    value: str,
) -> str:
    value = " ".join(value.strip().split())

    if not value:
        raise ValueError("User name cannot be empty")

    if len(value) < 2:
        raise ValueError("User name must contain at least 2 characters")

    if len(value) > 255:
        raise ValueError("User name cannot exceed 255 characters")

    return value


def validate_workspace_name(
    value: str,
) -> str:
    value = " ".join(value.strip().split())

    if not value:
        raise ValueError(
            "Workspace name cannot be empty. Please provide a workspace name."
        )

    if len(value) < 3:
        raise ValueError("Workspace name must contain at least 3 characters")

    if len(value) > 255:
        raise ValueError("Workspace name cannot exceed 255 characters")

    if value.lower() in RESERVED_WORKSPACE_NAMES:
        raise ValueError(
            f'"{value}" is a reserved workspace name. Please choose a different name.'
        )

    return value


def validate_otp_code(
    value: str,
) -> str:
    value = value.strip()

    if len(value) != 6:
        raise ValueError("OTP must contain exactly 6 digits")

    if not value.isdigit():
        raise ValueError("OTP must contain only digits")

    return value


def validate_refresh_token(
    value: str,
) -> str:
    value = value.strip()

    if not value:
        raise ValueError("Refresh token cannot be empty")

    return value


EmailAddress = Annotated[
    EmailStr,
    AfterValidator(validate_email_address),
]

UserName = Annotated[
    str,
    AfterValidator(validate_user_name),
]

WorkspaceName = Annotated[
    str,
    AfterValidator(validate_workspace_name),
]

OTPCode = Annotated[
    str,
    AfterValidator(validate_otp_code),
]

RefreshToken = Annotated[
    str,
    AfterValidator(validate_refresh_token),
]
