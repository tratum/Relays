from fastapi import status

from app.core.error_codes import ErrorCode
from app.core.errors import APIException
from app.infra.db.session import get_pool

from ...db.session_queries import (
    get_session_by_refresh_token_hash,
    revoke_session,
)
from ...security.refresh import (
    hash_refresh_token,
)


async def logout(
    refresh_token: str,
):
    pool = get_pool()

    async with pool.acquire() as conn:
        async with conn.transaction():
            computed_hash = hash_refresh_token(refresh_token)

            session = await get_session_by_refresh_token_hash(
                conn,
                computed_hash,
            )

            if session is None:
                raise APIException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    code=ErrorCode.INVALID_REFRESH_TOKEN,
                    message="Invalid refresh token",
                )

            revoked_session = await revoke_session(
                conn,
                session["id"],
            )

            if revoked_session is None:
                raise APIException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    code=ErrorCode.INVALID_REFRESH_TOKEN,
                    message="Invalid refresh token",
                )
