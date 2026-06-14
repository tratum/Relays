# app/routes.py

from fastapi import FastAPI

from app.core.constants import API_VERSION
from app.modules.api_keys.api.v1.routes import router as api_keys_router
from app.modules.notifications.api.v1.routes import (
    router as notifications_router,
)
from app.modules.workspaces.api.v1.routes import router as workspaces_router


def register_routes(app: FastAPI) -> None:
    app.include_router(
        notifications_router,
        prefix=API_VERSION,
    )
    app.include_router(
        workspaces_router,
        prefix=API_VERSION,
    )
    app.include_router(
        api_keys_router,
        prefix=API_VERSION,
    )
