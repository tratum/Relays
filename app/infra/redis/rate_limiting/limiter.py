from time import time
from uuid import uuid4

from app.infra.redis.session import get_redis


async def sliding_window_limiter(
    *,
    key: str,
    limit: int,
    window_seconds: int,
) -> bool:
    """
    Check whether a request is allowed under a sliding-window
    rate limit algorithm.

    Returns:
        True  -> Request is allowed.
        False -> Rate limit exceeded.
    """
    redis = get_redis()

    now = time()
    window_start = now - window_seconds

    # Remove requests that no longer belong to the active window.
    await redis.zremrangebyscore(
        key,
        "-inf",
        window_start,
    )

    request_count = await redis.zcount(
        key,
        window_start,
        "+inf",
    )

    if request_count >= limit:
        return False

    # Store the current request using the timestamp as the score
    # and a UUID as the member to guarantee uniqueness.
    await redis.zadd(
        key,
        {
            str(uuid4()): now,
        },
    )

    # Expire the key automatically once it has been inactive for
    # an entire window.
    await redis.expire(
        key,
        window_seconds,
    )

    return True
