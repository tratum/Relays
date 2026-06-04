import asyncio

from app.infra.db.session import init_db

_loop = None
_initialized = False


def get_loop():
    global _loop
    if _loop is None or _loop.is_closed():
        _loop = asyncio.new_event_loop()
        asyncio.set_event_loop(_loop)
    return _loop


async def _run(coro):
    global _initialized

    if not _initialized:
        await init_db()
        _initialized = True

    return await coro


def async_to_sync(coro):
    loop = get_loop()
    return loop.run_until_complete(_run(coro))
