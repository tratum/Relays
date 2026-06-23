from fastapi import status

from app.core.error_codes import ErrorCode
from app.core.errors import APIException
from app.infra.db.session import get_pool

from ...workspaces.db.context_queries import get_current_user_context


async def get_current_user(user_id):
    pool = get_pool()
    async with pool.acquire() as conn:
        context = await get_current_user_context(conn, user_id)

        if context is None:
            raise APIException(
                status_code=status.HTTP_404_NOT_FOUND,
                code=ErrorCode.NOT_FOUND,
                message="User not found",
            )

        return context
