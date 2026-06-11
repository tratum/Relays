from typing import Annotated

from pydantic import AfterValidator

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


def validate_name(value: str) -> str:
    value = value.strip()

    if not value:
        raise ValueError("Name cannot be empty")

    if len(value) > 255:
        raise ValueError("Name cannot exceed 255 characters")

    return value


def validate_workspace_name(value: str) -> str:
    value = value.strip()

    if not value:
        raise ValueError(
            "Workspace name cannot be empty. Please provide a workspace name."
        )

    if len(value) > 255:
        raise ValueError("Workspace name cannot exceed 255 characters")

    if value.lower() in RESERVED_WORKSPACE_NAMES:
        raise ValueError(
            f'"{value}" is a reserved workspace name. Please choose a different name.'
        )

    return value


UserName = Annotated[str, AfterValidator(validate_name)]
WorkspaceName = Annotated[str, AfterValidator(validate_workspace_name)]
