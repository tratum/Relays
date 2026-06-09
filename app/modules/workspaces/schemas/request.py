from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.modules.workspaces.validators import (
    UserName,
    WorkspaceName,
)


class WorkspaceRequestBody(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
    )
    workspace_name: WorkspaceName = Field(
        ...,
        description=(
            "Human-readable name of the workspace. "
            "This name is used to generate the workspace slug."
        ),
        examples=[
            "Acme",
            "Acme Corporation",
            "Relays Production",
        ],
    )
    email: EmailStr = Field(
        ...,
        description="Email address associated with the Workspace",
        examples=["jhon.doe@example.com"],
    )
    name: UserName = Field(
        ...,
        description="User Name associated with the Workspace",
        examples=["Jhon Doe"],
    )
