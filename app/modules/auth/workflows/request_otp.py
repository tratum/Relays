import logging
from datetime import UTC, datetime, timedelta

from app.infra.db.session import get_pool
from app.modules.auth.constants import OTP_EXPIRY_MINUTES
from app.modules.auth.db.login_otp_queries import (
    create_login_otp,
    delete_login_otp,
)
from app.modules.auth.security.otp import (
    generate_otp,
    hash_otp,
)
from app.modules.workspaces.db.users_queries import (
    get_user_by_email,
)

logger = logging.getLogger(__name__)


async def request_otp(email: str):
    pool = get_pool()

    async with pool.acquire() as conn:
        async with conn.transaction():
            user = await get_user_by_email(conn, email)

            ## Implementing this Approach to Prevent User Enumeration
            if user is not None:
                await delete_login_otp(conn, user["id"])

                otp = generate_otp()
                otp_hash = hash_otp(otp)
                expires_at = datetime.now(UTC) + timedelta(
                    minutes=OTP_EXPIRY_MINUTES
                )

                await create_login_otp(
                    conn,
                    user["id"],
                    otp_hash,
                    expires_at,
                )

                logger.info(
                    "Generated login OTP",
                    extra={
                        "user_id": str(user["id"]),
                        "otp": otp,
                    },
                )
