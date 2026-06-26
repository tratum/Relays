import logging
from datetime import UTC, datetime, timedelta

from asyncpg import UniqueViolationError
from fastapi import status

from app.core.constants import SYSTEM_REQUEST_ID
from app.core.error_codes import ErrorCode
from app.core.errors import APIException
from app.infra.db.session import get_pool
from app.infra.redis.rate_limiting.otp.limiter import OTPFlow, otp_rate_limit

from ....workspaces.db.users_queries import (
    get_user_by_email,
)
from ...constants import OTP_EXPIRY_MINUTES
from ...db.login_otp_queries import (
    create_login_otp,
    delete_login_otp,
)
from ...security.otp import (
    generate_otp,
    hash_otp,
)

logger = logging.getLogger(__name__)


async def request_login_otp(
    email: str,
) -> None:
    pool = get_pool()

    rate_limit = await otp_rate_limit(email=email, flow=OTPFlow.LOGIN)

    if not rate_limit:
        raise APIException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            code=ErrorCode.RATE_LIMIT_EXCEEDED,
            message="Too many OTP requests. Please try again later.",
        )

    try:
        async with pool.acquire() as conn:
            async with conn.transaction():
                user = await get_user_by_email(conn, email)

            # Prevent User Enumeration
            if user is None:
                return

            await delete_login_otp(
                conn,
                user["id"],
            )

            otp = generate_otp()
            otp_hash = hash_otp(otp)
            expires_at = datetime.now(UTC) + timedelta(
                minutes=OTP_EXPIRY_MINUTES,
            )

            await create_login_otp(
                conn,
                user["id"],
                otp_hash,
                expires_at,
            )

            logger.info(
                f"Generated Registration OTP | email={email} | otp={otp}",
                extra={"request_id": SYSTEM_REQUEST_ID},
            )

            # TODO:
            # Send OTP email

    except UniqueViolationError:
        raise APIException(
            status_code=status.HTTP_409_CONFLICT,
            code=ErrorCode.CONFLICT,
            message=(
                "Unable to generate a verification code at this time. "
                "Please try again."
            ),
        )
