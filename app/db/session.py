import json

import asyncpg

from app.core.config import config
from app.db.migration_runner import run_migrations

# Global Connection Pool
pool: asyncpg.Pool | None = None


# EXTREMELY IMPORTANT
async def setup_connection(conn):  # Registering JSONB Codec
    await conn.set_type_codec(
        "jsonb",
        schema="pg_catalog",
        encoder=json.dumps,
        decoder=json.loads,
    )


def get_pool() -> asyncpg.Pool:
    if pool is None:
        raise RuntimeError("Database not initialized")
    return pool


async def init_db():
    global pool

    if pool is not None:
        return  # already intialised

    pool = await asyncpg.create_pool(
        dsn=config.DATABASE_URL,
        min_size=5,
        max_size=10,
        command_timeout=60,
        max_inactive_connection_lifetime=300,
        init=setup_connection,  ## Runs Per-Connection
    )

    # Warming Up DB Pools
    async with pool.acquire() as conn:
        await conn.execute("SELECT 1")
        await conn.fetch("SELECT NOW()")
        await run_migrations(conn)


async def close_db():
    global pool

    if pool is None:
        return

    await pool.close()
    pool = None
