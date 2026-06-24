from redis.asyncio import Redis

_redis: Redis | None = None


def set_redis(
    redis: Redis,
):
    global _redis
    _redis = redis


def get_redis() -> Redis:
    if _redis is None:
        raise RuntimeError("Redis Client not initialized")

    return _redis
