from enum import StrEnum

from ...rate_limiting.limiter import sliding_window_limiter
from .constants import (
    OTP_COOLDOWN_LIMIT,
    OTP_COOLDOWN_WINDOW_SECONDS,
    OTP_DAILY_LIMIT,
    OTP_DAILY_WINDOW_SECONDS,
    OTP_HOURLY_LIMIT,
    OTP_HOURLY_WINDOW_SECONDS,
)
from .keys import (
    otp_login_cooldown_key,
    otp_login_day_key,
    otp_login_hour_key,
    otp_registration_cooldown_key,
    otp_registration_day_key,
    otp_registration_hour_key,
)


class OTPFlow(StrEnum):
    LOGIN = "login"
    REGISTRATION = "registration"


async def otp_rate_limit(*, email: str, flow: OTPFlow) -> bool:
    """
    Apply OTP rate limits for the specified flow.

    A request is permitted only if it satisfies:
    - Cooldown limit
    - Hourly limit
    - Daily limit
    """

    if flow == OTPFlow.LOGIN:
        cooldown_key = otp_login_cooldown_key(email)
        hourly_key = otp_login_hour_key(email)
        daily_key = otp_login_day_key(email)

    elif flow == OTPFlow.REGISTRATION:
        cooldown_key = otp_registration_cooldown_key(email)
        hourly_key = otp_registration_hour_key(email)
        daily_key = otp_registration_day_key(email)

    else:
        raise ValueError(f"Unsupported OTP flow: {flow}")

    if not await sliding_window_limiter(
        key=cooldown_key,
        limit=OTP_COOLDOWN_LIMIT,
        window_seconds=OTP_COOLDOWN_WINDOW_SECONDS,
    ):
        return False

    if not await sliding_window_limiter(
        key=hourly_key,
        limit=OTP_HOURLY_LIMIT,
        window_seconds=OTP_HOURLY_WINDOW_SECONDS,
    ):
        return False

    if not await sliding_window_limiter(
        key=daily_key,
        limit=OTP_DAILY_LIMIT,
        window_seconds=OTP_DAILY_WINDOW_SECONDS,
    ):
        return False

    return True
