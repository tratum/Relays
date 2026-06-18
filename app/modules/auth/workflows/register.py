from asyncpg import UniqueViolationError
from fastapi import status

from app.core.error_codes import ErrorCode
from app.core.errors import APIException
from app.infra.db.session import get_pool
from app.modules.workspaces.constants import (
    WorkspaceMemberRoles,
    slugify,
    validate_workspace_slug,
)
from app.modules.workspaces.db.users_queries import (
    create_user,
    get_user_by_email,
)
from app.modules.workspaces.db.workspace_members_queries import (
    create_workspace_member,
)
from app.modules.workspaces.db.workspaces_queries import (
    create_workspace,
    get_workspace_by_slug,
)


async def register_user(
    name: str,
    email: str,
    workspace_name: str,
):
    pool = get_pool()

    try:
        async with pool.acquire() as conn:
            async with conn.transaction():
                existing_user = await get_user_by_email(
                    conn,
                    email,
                )

                if existing_user:
                    raise APIException(
                        status_code=status.HTTP_409_CONFLICT,
                        code=ErrorCode.CONFLICT,
                        message=(
                            "A user has already been registered "
                            "with this email."
                        ),
                    )

                slug = slugify(workspace_name)

                try:
                    validate_workspace_slug(slug)

                except ValueError as exc:
                    raise APIException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        code=ErrorCode.INVALID_REQUEST,
                        message=str(exc),
                    )

                existing_workspace = await get_workspace_by_slug(conn, slug)

                if existing_workspace:
                    raise APIException(
                        status_code=status.HTTP_409_CONFLICT,
                        code=ErrorCode.CONFLICT,
                        message="Workspace name is not available.",
                    )

                user = await create_user(conn, name, email)
                workspace = await create_workspace(conn, workspace_name, slug)

                await create_workspace_member(
                    conn,
                    workspace["id"],
                    user["id"],
                    WorkspaceMemberRoles.OWNER,
                )

                return {
                    "user_id": user["id"],
                    "workspace_id": workspace["id"],
                    "name": user["name"],
                    "email": user["email"],
                    "workspace_name": workspace["name"],
                }

    # Race Condition Safety Net
    except UniqueViolationError:
        raise APIException(
            status_code=status.HTTP_409_CONFLICT,
            code=ErrorCode.CONFLICT,
            message=(
                "A user or workspace with the provided "
                "information already exists."
            ),
        )
