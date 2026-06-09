import re
from enum import Enum


class WorkspaceStatus(str, Enum):
    ACTIVE = "ACTIVE"
    SUSPENDED = "SUSPENDED"
    DELETED = "DELETED"


class WorkspaceMemberRoles(str, Enum):
    OWNER = "OWNER"
    MEMBER = "MEMBER"


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
