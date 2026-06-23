from asyncpg import UniqueViolationError
from fastapi import status

from app.core.error_codes import ErrorCode
from app.core.errors import APIException
from app.infra.db.session import get_pool
from app.modules.auth.security.jwt import (
    create_access_token,
    decode_registration_token,
)

from ....workspaces.constants import (
    WorkspaceMemberRoles,
    slugify,
    validate_workspace_slug,
)
from ....workspaces.db.users_queries import (
    create_user,
    get_user_by_email,
)
from ....workspaces.db.workspace_members_queries import (
    create_workspace_membership,
)
from ....workspaces.db.workspaces_queries import (
    create_workspace,
    get_workspace_by_slug,
)


async def create_account(
    registration_token: str,
    name: str,
    workspace_name: str,
) -> str:
    payload = decode_registration_token(registration_token)
    ## Exceptions have already been handled in /security/jwt.py
    email = payload.email
    slug = slugify(workspace_name)

    try:
        validate_workspace_slug(slug)
    except ValueError as exc:
        raise APIException(
            status_code=status.HTTP_400_BAD_REQUEST,
            code=ErrorCode.INVALID_REQUEST,
            message=str(exc),
        )

    pool = get_pool()

    try:
        async with pool.acquire() as conn:
            async with conn.transaction():
                existing_user = await get_user_by_email(conn, email)
                if existing_user:
                    raise APIException(
                        status_code=status.HTTP_409_CONFLICT,
                        code=ErrorCode.CONFLICT,
                        message=(
                            "A user has already been registered with this email."
                        ),
                    )

                existing_workspace = await get_workspace_by_slug(conn, slug)
                if existing_workspace:
                    raise APIException(
                        status_code=status.HTTP_409_CONFLICT,
                        code=ErrorCode.CONFLICT,
                        message="Workspace Name is not available.",
                    )

                user = await create_user(conn, name, email)
                workspace = await create_workspace(conn, workspace_name, slug)

                await create_workspace_membership(
                    conn,
                    workspace["id"],
                    user["id"],
                    WorkspaceMemberRoles.OWNER,
                )

                access_token = create_access_token(user["id"])

        return access_token

    except UniqueViolationError:
        raise APIException(
            status_code=status.HTTP_409_CONFLICT,
            code=ErrorCode.CONFLICT,
            message="Account Creation conflict detected",
        )
