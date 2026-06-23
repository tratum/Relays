from datetime import UTC, datetime

from fastapi import status

from app.core.error_codes import ErrorCode
from app.core.errors import APIException
from app.infra.db.session import get_pool

from ...db.registration_otp_queries import (
    consume_registration_otp,
    delete_registration_otp,
    get_registration_otp_by_email,
)
from ...security.jwt import create_registration_token
from ...security.otp import (
    hash_otp,
    verify_otp,
)


async def verify_registration_otp(
    email: str,
    otp: str,
) -> str:
    pool = get_pool()

    async with pool.acquire() as conn:
        async with conn.transaction():
            registration_otp = await get_registration_otp_by_email(conn, email)

            if registration_otp is None:
                raise APIException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    code=ErrorCode.INVALID_OTP,
                    message="Invalid OTP",
                )

            if registration_otp["expires_at"] <= datetime.now(UTC):
                await delete_registration_otp(conn, email)
                raise APIException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    code=ErrorCode.INVALID_OTP,
                    message="Invalid OTP",
                )

            computed_hash = hash_otp(otp)

            if not verify_otp(
                computed_hash,
                registration_otp["otp_hash"],
            ):
                raise APIException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    code=ErrorCode.INVALID_OTP,
                    message="Invalid OTP",
                )

            consumed_otp = await consume_registration_otp(conn, email)

            if consumed_otp is None:
                raise APIException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    code=ErrorCode.INVALID_OTP,
                    message="Invalid OTP",
                )

            registration_token = create_registration_token(email)

            return registration_token
