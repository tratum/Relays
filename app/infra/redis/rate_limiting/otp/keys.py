def otp_login_cooldown_key(
    email: str,
) -> str:
    return f"otp:login:cooldown:{email}"


def otp_login_hour_key(
    email: str,
) -> str:
    return f"otp:login:hour:{email}"


def otp_login_day_key(
    email: str,
) -> str:
    return f"otp:login:day:{email}"


def otp_registration_cooldown_key(
    email: str,
) -> str:
    return f"otp:register:cooldown:{email}"


def otp_registration_hour_key(
    email: str,
) -> str:
    return f"otp:register:hour:{email}"


def otp_registration_day_key(
    email: str,
) -> str:
    return f"otp:register:day:{email}"
