from typing import Annotated

from asyncpg import UniqueViolationError
from fastapi import APIRouter, Path, status
from pydantic import UUID4

from app.core.error_codes import ErrorCode
from app.core.errors import APIException, ErrorResponse
from app.infra.db.session import get_pool

from ...constants import WorkspaceMemberRoles, slugify
from ...db.users_queries import (
    create_user,
    get_user_by_email,
)
from ...db.workspace_members_queries import (
    create_workspace_member,
    get_workspace_members,
)
from ...db.workspaces_queries import (
    create_workspace,
    get_workspace,
    get_workspace_by_slug,
)
from ...schemas.request import WorkspaceRequestBody
from ...schemas.response import (
    WorkspaceBody,
    WorkspaceMemberBody,
    WorkspaceMembersResponseBody,
    WorkspaceResponseBody,
)

router = APIRouter(tags=["Workspaces API"])

# -------------
# Health Check
# -------------


@router.get("/workspaces/health", summary="Workspaces API Health Check")
async def health_check():
    return {"status": "ok"}


# ------------------
# Create Workspace
# ------------------


@router.post(
    path="/workspaces",
    summary="Creates a Workspace",
    description=(
        "Creates a new workspace and assigns the creator as the "
        "workspace OWNER. A new user, workspace, and membership "
        "are created atomically within a single transaction."
    ),
    status_code=status.HTTP_201_CREATED,
    response_model=WorkspaceResponseBody,
    responses={
        400: {"model": ErrorResponse},
        401: {"model": ErrorResponse},
        403: {"model": ErrorResponse},
        404: {"model": ErrorResponse},
        409: {"model": ErrorResponse},
        500: {"model": ErrorResponse},
    },
)
async def create_workspace_route(
    req: WorkspaceRequestBody,
):
    pool = get_pool()

    try:
        async with pool.acquire() as conn:
            async with conn.transaction():
                # -----------------------------------------
                # Validate Email
                # -----------------------------------------

                existing_user = await get_user_by_email(
                    conn,
                    req.email,
                )

                if existing_user:
                    raise APIException(
                        status_code=status.HTTP_409_CONFLICT,
                        code=ErrorCode.CONFLICT,
                        message="A user with this email already exists.",
                    )

                # -----------------------------------------
                # Generate + Validate Slug
                # -----------------------------------------

                slug = slugify(req.workspace_name)
                existing_workspace = await get_workspace_by_slug(
                    conn,
                    slug,
                )

                if existing_workspace:
                    raise APIException(
                        status_code=status.HTTP_409_CONFLICT,
                        code=ErrorCode.CONFLICT,
                        message="A workspace with this name already exists.",
                    )

                user = await create_user(
                    conn,
                    req.name,
                    req.email,
                )
                workspace = await create_workspace(
                    conn,
                    req.workspace_name,
                    slug,
                )

                ## Creating OWNER Membership
                await create_workspace_member(
                    conn,
                    workspace["id"],
                    user["id"],
                    WorkspaceMemberRoles.OWNER,
                )

                return {
                    "user": user,
                    "workspace": workspace,
                }

    ## Just a Safety Net for Race Conditions
    except UniqueViolationError:
        raise APIException(
            status_code=status.HTTP_409_CONFLICT,
            code=ErrorCode.CONFLICT,
            message="A user or workspace with the provided information already exists.",
        )


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
        workspace = await get_workspace(
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
        workspace = await get_workspace(
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
