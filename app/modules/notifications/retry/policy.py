import random
from datetime import UTC, datetime, timedelta

from app.core.config import config


def calculate_next_retry_time(
    *,
    attempt_number: int,
) -> datetime:
    """
    Calculates the next retry time using exponential backoff
    with Full Jitter.

    Formula:
        delay = random(0, min(base * 2^(attempt-1), max_delay))
    """

    if attempt_number < 1:
        raise ValueError("Attempt Number must be greater than or equal to 1")

    exponential_delay = config.INITIAL_RETRY_DELAY_SECONDS * (
        2 ** (attempt_number - 1)
    )
    capped_delay = min(exponential_delay, config.MAX_RETRY_DELAY_SECONDS)
    delay = random.randint(0, capped_delay)

    return datetime.now(UTC) + timedelta(seconds=delay)
