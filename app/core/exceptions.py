import logging
from typing import cast

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.types import ExceptionHandler

from app.core.config import config
from app.core.error_codes import ErrorCode
from app.core.errors import APIException, build_error
from app.core.logging import log_extra

logger = logging.getLogger(__name__)


async def request_validation_exception_handler(
    request: Request,
    exc: RequestValidationError,
) -> JSONResponse:
    request_id = getattr(
        request.state,
        "request_id",
        None,
    )

    errors = exc.errors()

    logger.warning(
        "Request validation failed",
        extra=log_extra(
            request_id,
            path=request.url.path,
            method=request.method,
            errors=errors,
        ),
    )

    first_error = errors[0]

    if config.DEBUG:
        location = ".".join(
            str(part)
            for part in first_error.get(
                "loc",
                [],
            )
        )

        message = f"{location}: {first_error.get('msg', 'Invalid Request')}"
    else:
        message = first_error.get(
            "msg",
            "Invalid Request",
        )

    return JSONResponse(
        status_code=400,
        content=build_error(
            code=ErrorCode.INVALID_REQUEST,
            message=message,
            request_id=request_id,
        ),
    )


async def api_exception_handler(
    request: Request,
    exc: APIException,
) -> JSONResponse:
    request_id = getattr(
        request.state,
        "request_id",
        None,
    )

    logger.warning(
        "API Exception",
        extra=log_extra(
            request_id,
            path=request.url.path,
            method=request.method,
            status_code=exc.status_code,
            error_code=exc.code,
        ),
    )

    return JSONResponse(
        status_code=exc.status_code,
        content=build_error(
            code=exc.code,
            message=exc.message,
            request_id=request_id,
        ),
    )


async def http_exception_handler(
    request: Request,
    exc: StarletteHTTPException,
) -> JSONResponse:
    request_id = getattr(
        request.state,
        "request_id",
        None,
    )

    if exc.status_code == 404:
        code = ErrorCode.NOT_FOUND
        message = (
            exc.detail if isinstance(exc.detail, str) else "Resource not found"
        )

    elif exc.status_code == 401:
        code = ErrorCode.UNAUTHORIZED
        message = exc.detail if isinstance(exc.detail, str) else "Unauthorized"

    elif exc.status_code == 403:
        code = ErrorCode.FORBIDDEN
        message = exc.detail if isinstance(exc.detail, str) else "Forbidden"

    elif exc.status_code == 409:
        code = ErrorCode.CONFLICT
        message = (
            exc.detail if isinstance(exc.detail, str) else "Resource conflict"
        )

    else:
        code = ErrorCode.INTERNAL_ERROR
        message = str(exc.detail) if exc.detail else "HTTP error"

    logger.warning(
        "HTTP Exception",
        extra=log_extra(
            request_id,
            path=request.url.path,
            method=request.method,
            status_code=exc.status_code,
            detail=exc.detail,
        ),
    )

    return JSONResponse(
        status_code=exc.status_code,
        content=build_error(
            code=code,
            message=message,
            request_id=request_id,
        ),
    )


async def global_exception_handler(
    request: Request,
    exc: Exception,
) -> JSONResponse:
    request_id = getattr(
        request.state,
        "request_id",
        None,
    )

    logger.exception(
        "Unhandled Exception",
        extra=log_extra(
            request_id,
            path=request.url.path,
            method=request.method,
        ),
    )

    if config.DEBUG:
        message = str(exc)
    else:
        message = "Unexpected error"

    return JSONResponse(
        status_code=500,
        content=build_error(
            code=ErrorCode.INTERNAL_ERROR,
            message=message,
            request_id=request_id,
        ),
    )


def register_exception_handlers(
    app: FastAPI,
) -> None:
    app.add_exception_handler(
        RequestValidationError,
        cast(
            ExceptionHandler,
            request_validation_exception_handler,
        ),
    )

    app.add_exception_handler(
        APIException,
        cast(
            ExceptionHandler,
            api_exception_handler,
        ),
    )

    app.add_exception_handler(
        StarletteHTTPException,
        cast(
            ExceptionHandler,
            http_exception_handler,
        ),
    )

    app.add_exception_handler(
        Exception,
        global_exception_handler,
    )
