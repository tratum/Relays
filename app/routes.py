# app/routes.py

from fastapi import FastAPI

from app.modules.api_keys.api.v1.routes import router as api_keys_router
from app.modules.notifications.api.v1.routes import (
    router as notifications_router,
)
from app.modules.workspaces.api.v1.routes import router as workspaces_router


def register_routes(app: FastAPI) -> None:
    app.include_router(
        notifications_router,
        prefix="/v1",
    )
    app.include_router(
        workspaces_router,
        prefix="/v1",
    )
    app.include_router(
        api_keys_router,
        prefix="/v1",
    )
