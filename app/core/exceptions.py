import logging

from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

logger = logging.getLogger(__name__)


async def request_validation_exception_handler(
    req: Request, exc: RequestValidationError
):
    first_error = exc.errors()[0]
    message = first_error.get("msg", "Invalid Request")
    request_id = getattr(req.state, "request_id", None)

    return JSONResponse(
        status_code=400,
        content={
            "error": {
                "code": "invalid_request",
                "message": message,
                "request_id": request_id,
            }
        },
    )


async def http_exception_handler(req: Request, exc: StarletteHTTPException):
    request_id = getattr(req.state, "request_id", None)

    if exc.status_code == 404:
        code = "not_found"
        message = (
            exc.detail if isinstance(exc.detail, str) else "Resource not found"
        )

    elif exc.status_code == 401:
        code = "unauthorized"
        message = exc.detail or "Unauthorized"

    elif exc.status_code == 403:
        code = "forbidden"
        message = exc.detail or "Forbidden"

    else:
        code = "http_error"
        message = str(exc.detail) if exc.detail else "HTTP error"

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": code,
                "message": message,
                "request_id": request_id,
            }
        },
    )


async def global_exception_handler(request: Request, exc: Exception):
    request_id = getattr(request.state, "request_id", None)

    # Log the full error (VERY important)
    logger.exception(
        "Unhandled Exception",
        extra={"request_id": request_id},
    )

    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "code": "internal_error",
                "message": "Unexpected error",
                "request_id": request_id,
            }
        },
    )
