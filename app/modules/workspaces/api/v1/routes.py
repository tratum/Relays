from typing import Annotated

from fastapi import APIRouter, Path, status
from pydantic import UUID4

from app.core.error_codes import ErrorCode
from app.core.errors import APIException, ErrorResponse
from app.infra.db.session import get_pool

from ...db.workspace_members_queries import get_workspace_members
from ...db.workspaces_queries import get_workspace_by_id
from ...schemas.response import (
    WorkspaceBody,
    WorkspaceMemberBody,
    WorkspaceMembersResponseBody,
)

router = APIRouter(tags=["Workspaces API"])

# -------------
# Health Check
# -------------


@router.get("/workspaces/health", summary="Workspaces API Health Check")
async def health_check():
    return {"status": "ok"}


# --------------
# Get Workspace
# --------------


@router.get(
    path="/workspaces/{workspace_id}",
    summary="Gets Workspace Details",
    description=(
        "Retrieves metadata and current status for a workspace "
        "identified by its unique workspace_id."
    ),
    response_model=WorkspaceBody,
    responses={
        404: {"model": ErrorResponse},
        422: {"model": ErrorResponse},
        500: {"model": ErrorResponse},
    },
)
async def get_workspace_route(
    workspace_id: Annotated[
        UUID4,
        Path(
            description="Unique identifier of the workspace.",
        ),
    ],
):
    pool = get_pool()

    async with pool.acquire() as conn:
        workspace = await get_workspace_by_id(
            conn,
            workspace_id,
        )

    if workspace is None:
        raise APIException(
            status_code=status.HTTP_404_NOT_FOUND,
            code=ErrorCode.NOT_FOUND,
            message="No workspace was found for the provided workspace_id.",
        )

    return workspace


# -----------------------
# Get Workspace Members
# -----------------------


@router.get(
    path="/workspaces/{workspace_id}/members",
    summary="Lists Workspace Members",
    description=(
        "Returns the complete membership roster for a workspace, "
        "including user information and workspace roles."
    ),
    response_model=WorkspaceMembersResponseBody,
    responses={
        404: {"model": ErrorResponse},
        422: {"model": ErrorResponse},
        500: {"model": ErrorResponse},
    },
)
async def get_workspace_members_route(
    workspace_id: Annotated[
        UUID4,
        Path(
            description="Unique identifier of the workspace.",
        ),
    ],
):
    pool = get_pool()

    async with pool.acquire() as conn:
        workspace = await get_workspace_by_id(
            conn,
            workspace_id,
        )
        members = await get_workspace_members(
            conn,
            workspace_id,
        )

    if workspace is None:
        raise APIException(
            status_code=status.HTTP_404_NOT_FOUND,
            code=ErrorCode.NOT_FOUND,
            message="No workspace was found for the provided workspace_id.",
        )

    return WorkspaceMembersResponseBody(
        members=[
            WorkspaceMemberBody.model_validate(member) for member in members
        ]
    )
