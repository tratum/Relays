import re
from enum import Enum


class WorkspaceStatus(str, Enum):
    ACTIVE = "ACTIVE"
    SUSPENDED = "SUSPENDED"
    DELETED = "DELETED"


class WorkspaceMemberRoles(str, Enum):
    OWNER = "OWNER"
    MEMBER = "MEMBER"


RESERVED_WORKSPACE_SLUGS = {
    "admin",
    "administrator",
    "api",
    "app",
    "auth",
    "billing",
    "dashboard",
    "docs",
    "help",
    "login",
    "logout",
    "me",
    "register",
    "root",
    "settings",
    "support",
    "system",
    "www",
    "dev",
    "development",
    "prod",
    "production",
    "staging",
    "sandbox",
    "qa",
    "test",
    "testing",
}


def validate_workspace_slug(
    slug: str,
) -> None:
    if not slug:
        raise ValueError("Workspace Name produces an invalid slug")

    if slug in RESERVED_WORKSPACE_SLUGS:
        raise ValueError("The Workspace Name is reserved")


def slugify(value: str) -> str:
    value = value.strip().lower()

    # Replacing whitespace and underscores with hyphens
    value = re.sub(r"[\s_]+", "-", value)

    # Removing everything except letters, numbers and hyphens
    value = re.sub(r"[^a-z0-9-]", "", value)

    # Collapse repeated hyphens
    value = re.sub(r"-+", "-", value)

    # Remove leading/trailing hyphens
    value = value.strip("-")

    return value
