from fastapi import status

from app.core.error_codes import ErrorCode
from app.core.errors import APIException
from app.infra.db.session import get_pool
from app.modules.auth.security.jwt import create_access_token
from app.modules.workspaces.db.users_queries import (
    get_user_by_email,
)
from app.modules.workspaces.db.workspace_members_queries import (
    get_workspace_context,
)


async def login_user(
    email: str,
) -> str:
    pool = get_pool()
    async with pool.acquire() as conn:
        user = await get_user_by_email(conn, email)

        if user is None:
            raise APIException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                code=ErrorCode.UNAUTHORIZED,
                message="Invalid Credentials",
            )

        workspace_context = await get_workspace_context(conn, user["id"])

        if workspace_context is None:
            raise APIException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                code=ErrorCode.UNAUTHORIZED,
                message="User Workspace Not Found",
            )

    access_token = create_access_token(user["id"])

    return access_token
