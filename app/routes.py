# app/routes.py

from fastapi import FastAPI

from app.modules.notifications.api.v1.routes import (
    router as notifications_router,
)


def register_routes(app: FastAPI) -> None:
    app.include_router(
        notifications_router,
        prefix="/v1",
    )
