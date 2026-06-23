from fastapi import Request, status

from app.core.error_codes import ErrorCode
from app.core.errors import APIException
from app.infra.db.session import get_pool
from app.modules.auth.security.jwt import decode_access_token
from app.modules.workspaces.db.context_queries import (
    get_workspace_context,
)


async def authenticate_jwt(
    req: Request,
):
    authorization = req.headers.get("Authorization")

    if not authorization:
        raise APIException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            code=ErrorCode.UNAUTHORIZED,
            message="Missing Authorization header",
        )

    scheme, _, jwt_token = authorization.partition(" ")

    if scheme.lower() != "bearer" or not jwt_token:
        raise APIException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            code=ErrorCode.UNAUTHORIZED,
            message="Invalid Authorization header",
        )

    jwt_token = jwt_token.strip()
    payload = decode_access_token(jwt_token)
    pool = get_pool()

    async with pool.acquire() as conn:
        workspace_context = await get_workspace_context(
            conn,
            payload.sub,
        )

    if workspace_context is None:
        raise APIException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            code=ErrorCode.UNAUTHORIZED,
            message="User's Workspace Not Found",
        )

    req.state.user_id = workspace_context["user_id"]
    req.state.workspace_id = workspace_context["workspace_id"]
    req.state.workspace_role = workspace_context["role"]
