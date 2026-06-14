import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.core.config import config
from app.core.constants import SYSTEM_REQUEST_ID
from app.core.exceptions import (
    register_exception_handlers,
)
from app.core.logging import initialize_logging
from app.infra.db.session import (
    close_db,
    init_db,
)
from app.infra.middleware.request_id import (
    RequestIDMiddleware,
)
from app.routes import register_routes

initialize_logging()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def app_lifespan(app: FastAPI):
    """
    Lifespan context for application startup/shutdown.

    This runs once when FastAPI starts, then yields, and
    runs cleanup code after shutdown.
    """
    # ---- Startup logic here ----
    # e.g., warm up DB pools, preload configs, validate connections
    # You can also attach to app.state if needed:
    # app.state.some_resource = some_client

    logger.info(
        "Initializing database",
        extra={"request_id": SYSTEM_REQUEST_ID},
    )
    try:
        await init_db()
    except Exception:
        logger.exception(
            "Database initialization failed. Shutting down application.",
            extra={"request_id": SYSTEM_REQUEST_ID},
        )
        raise
    yield
    # ---- Shutdown logic here ----
    # e.g., close connections, flush buffers
    # if app.state.some_resource:
    #     await app.state.some_resource.close()
    logger.info(
        "Closing database",
        extra={"request_id": SYSTEM_REQUEST_ID},
    )
    await close_db()


def create_app() -> FastAPI:
    app = FastAPI(
        title="Relays",
        description="API-First Notification Delivery Platform",
        version=config.VERSION,
        docs_url="/docs" if config.ENABLE_DOCS else None,
        redoc_url=None,
        lifespan=app_lifespan,
    )

    # ---------------Middleware-----------------
    app.add_middleware(RequestIDMiddleware)

    # ---------------Routers-----------------
    register_routes(app)

    # ---------------Exception Handlers-----------------
    register_exception_handlers(app)

    return app


app = create_app()
