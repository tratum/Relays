from datetime import UTC, datetime, timedelta

from fastapi import status

from app.core.error_codes import ErrorCode
from app.core.errors import APIException
from app.infra.db.session import get_pool

from .....modules.workspaces.db.users_queries import (
    get_user_by_id,
)
from ...constants import (
    REFRESH_TOKEN_TTL_DAYS,
)
from ...db.session_queries import (
    get_session_by_refresh_token_hash,
    revoke_session,
    rotate_session_refresh_token,
)
from ...security.jwt import (
    create_access_token,
)
from ...security.refresh import (
    generate_refresh_token,
    hash_refresh_token,
)


async def refresh_access_token(
    refresh_token: str,
):
    pool = get_pool()

    async with pool.acquire() as conn:
        async with conn.transaction():
            computed_hash = hash_refresh_token(
                refresh_token,
            )

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

            if session["expires_at"] <= datetime.now(UTC):
                await revoke_session(
                    conn,
                    session["id"],
                )

                raise APIException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    code=ErrorCode.REFRESH_TOKEN_EXPIRED,
                    message="Refresh token expired",
                )

            user = await get_user_by_id(
                conn,
                session["user_id"],
            )

            if user is None:
                raise APIException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    code=ErrorCode.INVALID_REFRESH_TOKEN,
                    message="Invalid refresh token",
                )

            new_refresh_token = generate_refresh_token()
            new_refresh_token_hash = hash_refresh_token(
                new_refresh_token,
            )
            expires_at = datetime.now(UTC) + timedelta(
                days=REFRESH_TOKEN_TTL_DAYS
            )

            rotated_session = await rotate_session_refresh_token(
                conn,
                session["id"],
                new_refresh_token_hash,
                expires_at,
            )

            if rotated_session is None:
                raise APIException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    code=ErrorCode.INVALID_REFRESH_TOKEN,
                    message="Invalid refresh token",
                )

            access_token = create_access_token(
                user["id"],
            )

            return {
                "access_token": access_token,
                "refresh_token": new_refresh_token,
            }
