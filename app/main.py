import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError

from app.api.v1.routes import router as v1Router
from app.core.config import config, initialize_logging
from app.core.exceptions import (
    StarletteHTTPException,
    global_exception_handler,
    http_exception_handler,
    request_validation_exception_handler,
)
from app.db.session import close_db, init_db
from app.middleware.request_id import RequestIDMiddleware

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
    # logger.info("Initializing Database....")
    logger.info(
        "Initializing database",
        extra={"request_id": "system"},
    )
    try:
        await init_db()
    except Exception:
        logger.exception(
            "Database initialization failed. Shutting down application.",
            extra={"request_id": "system"},
        )
        raise

    yield
    # ---- Shutdown logic here ----
    # e.g., close connections, flush buffers
    # if app.state.some_resource:
    #     await app.state.some_resource.close()
    # logger.info("Closing Database....")
    logger.info(
        "Closing database",
        extra={"request_id": "system"},
    )
    await close_db()


def create_app() -> FastAPI:
    """
    Application factory.

    This function creates and configures the FastAPI app.
    Keeping this as a factory makes the app:
    - testable
    - reusable by ASGI servers
    - safe for workers and migrations
    """

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
    app.include_router(
        v1Router,
        prefix="/v1",
    )

    # ---------------Exception Handlers-----------------
    app.add_exception_handler(
        RequestValidationError, request_validation_exception_handler
    )
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(Exception, global_exception_handler)

    return app


app = create_app()
