from datetime import UTC, datetime, timedelta

from fastapi import status

from app.core.error_codes import ErrorCode
from app.core.errors import APIException
from app.infra.db.session import get_pool

from ....workspaces.db.context_queries import (
    get_workspace_context,
)
from ....workspaces.db.users_queries import (
    get_user_by_email,
)
from ...constants import REFRESH_TOKEN_TTL_DAYS
from ...db.login_otp_queries import (
    consume_login_otp,
    delete_login_otp,
    get_login_otp_by_user_id,
)
from ...db.session_queries import create_session
from ...security.jwt import create_access_token
from ...security.otp import (
    hash_otp,
    verify_otp,
)
from ...security.refresh import (
    generate_refresh_token,
    hash_refresh_token,
)


async def authenticate_account(
    email: str,
    otp: str,
):
    pool = get_pool()

    async with pool.acquire() as conn:
        async with conn.transaction():
            user = await get_user_by_email(conn, email)

            if user is None:
                raise APIException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    code=ErrorCode.INVALID_CREDENTIALS,
                    message="Invalid Credentials",
                )

            login_otp = await get_login_otp_by_user_id(
                conn,
                user["id"],
            )

            if login_otp is None:
                raise APIException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    code=ErrorCode.INVALID_OTP,
                    message="Invalid OTP",
                )

            if login_otp["expires_at"] <= datetime.now(UTC):
                await delete_login_otp(
                    conn,
                    user["id"],
                )
                raise APIException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    code=ErrorCode.INVALID_OTP,
                    message="Invalid OTP",
                )

            computed_hash = hash_otp(otp)

            if not verify_otp(
                computed_hash,
                login_otp["otp_hash"],
            ):
                raise APIException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    code=ErrorCode.INVALID_OTP,
                    message="Invalid OTP",
                )

            consumed_otp = await consume_login_otp(
                conn,
                user["id"],
            )

            if consumed_otp is None:
                raise APIException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    code=ErrorCode.INVALID_OTP,
                    message="Invalid OTP",
                )

            workspace_context = await get_workspace_context(
                conn,
                user["id"],
            )

            if workspace_context is None:
                raise APIException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    code=ErrorCode.INVALID_CREDENTIALS,
                    message="Invalid Credentials",
                )

            access_token = create_access_token(
                user["id"],
            )
            refresh_token = generate_refresh_token()
            refresh_token_hash = hash_refresh_token(refresh_token)
            exp_at = datetime.now(UTC) + timedelta(days=REFRESH_TOKEN_TTL_DAYS)

            await create_session(
                conn,
                user["id"],
                refresh_token_hash,
                expires_at=exp_at,
            )

            return {
                "access_token": access_token,
                "refresh_token": refresh_token,
            }
