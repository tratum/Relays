import asyncpg

from app.core.config import settings

# Global Connection Pool
pool: asyncpg.Pool | None = None

def get_pool() -> asyncpg.Pool:
    if pool is None:
        raise RuntimeError("Database not initialized")
    return pool

async def init_db():
    global pool

    if pool is not None:
        return  # already intialised

    pool = await asyncpg.create_pool(
        dsn=settings.DATABASE_URL,
        min_size=5,
        max_size=10,
        command_timeout=60,
    )

    # Warming Up DB Pools
    async with pool.acquire() as conn:
        await conn.execute("SELECT 1")
        await conn.fetch("SELECT NOW()")


async def close_db():
    global pool

    if pool is None:
        return

    await pool.close()
    pool = None
