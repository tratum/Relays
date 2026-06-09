from datetime import datetime

from pydantic import (
    UUID4,
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
)

from app.modules.workspaces.constants import (
    WorkspaceMemberRoles,
    WorkspaceStatus,
)


class UserBody(BaseModel):
    model_config = ConfigDict(
        frozen=True,
    )

    id: UUID4 = Field(
        ...,
        description="Unique identifier of the user",
        examples=["550e8400-e29b-41d4-a716-446655440000"],
    )
    email: EmailStr = Field(
        ...,
        description="Email address of the user",
        examples=["john.doe@example.com"],
    )
    name: str = Field(
        ...,
        description="Display name of the user",
        examples=["John Doe"],
    )


class WorkspaceBody(BaseModel):
    model_config = ConfigDict(
        frozen=True,
    )

    id: UUID4 = Field(
        ...,
        description="Unique identifier of the workspace",
        examples=["f47ac10b-58cc-4372-a567-0e02b2c3d479"],
    )
    name: str = Field(
        ...,
        description="Human-readable name of the workspace used to identify the tenant within Relays",
        examples=["Acme Corporation"],
    )
    slug: str = Field(
        ...,
        description="Unique URL-friendly identifier generated from the workspace name and used for routing and referencing the workspace",
        examples=["acme-corporation"],
    )
    status: WorkspaceStatus = Field(
        ...,
        description="Current status of the workspace",
        examples=["ACTIVE"],
    )
    created_at: datetime = Field(
        ...,
        description="UTC timestamp when the workspace was created",
        examples=["2026-06-08T12:30:45Z"],
    )


class WorkspaceMemberBody(UserBody):
    model_config = ConfigDict(
        frozen=True,
    )

    role: WorkspaceMemberRoles = Field(
        ...,
        description="Role assigned to the user within the workspace",
        examples=["OWNER"],
    )


class WorkspaceResponseBody(BaseModel):
    model_config = ConfigDict(
        frozen=True,
    )

    user: UserBody = Field(
        ...,
        description="Details of the user who owns the workspace",
    )
    workspace: WorkspaceBody = Field(
        ...,
        description="Details of the workspace",
    )


class WorkspaceMembersResponseBody(BaseModel):
    model_config = ConfigDict(
        frozen=True,
    )

    members: list[WorkspaceMemberBody] = Field(
        ...,
        description="List of users who belong to the workspace",
    )
