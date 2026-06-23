import logging
from datetime import UTC, datetime, timedelta

from asyncpg import UniqueViolationError
from fastapi import status

from app.core.constants import SYSTEM_REQUEST_ID
from app.core.error_codes import ErrorCode
from app.core.errors import APIException
from app.infra.db.session import get_pool

from ....auth.constants import OTP_EXPIRY_MINUTES
from ....workspaces.db.users_queries import get_user_by_email
from ...db.registration_otp_queries import (
    create_registration_otp,
    delete_registration_otp,
    get_registration_otp_by_email,
)
from ...security.otp import (
    generate_otp,
    hash_otp,
)

logger = logging.getLogger(__name__)


async def request_registration_otp(
    email: str,
) -> None:
    pool = get_pool()

    try:
        async with pool.acquire() as conn:
            async with conn.transaction():
                existing_user = await get_user_by_email(conn, email)

                if existing_user is not None:
                    raise APIException(
                        status_code=status.HTTP_409_CONFLICT,
                        code=ErrorCode.CONFLICT,
                        message=(
                            "An account already exists for this email address."
                        ),
                    )

                existing_otp = await get_registration_otp_by_email(conn, email)

                if existing_otp is not None:
                    await delete_registration_otp(
                        conn,
                        email,
                    )

                otp = generate_otp()
                otp_hash = hash_otp(otp)
                expires_at = datetime.now(UTC) + timedelta(
                    minutes=OTP_EXPIRY_MINUTES,
                )

                await create_registration_otp(
                    conn,
                    email,
                    otp_hash,
                    expires_at,
                )

                logger.info(
                    f"Generated Registration OTP | email={email} | otp={otp}",
                    extra={"request_id": SYSTEM_REQUEST_ID},
                )

                # TODO:
                # Send OTP Email
                # await send_registration_otp_email(
                #     email=email,
                #     otp=otp,
                # )

    except UniqueViolationError:
        raise APIException(
            status_code=status.HTTP_409_CONFLICT,
            code=ErrorCode.CONFLICT,
            message=(
                "Unable to generate a verification code at this time. "
                "Please try again."
            ),
        )
