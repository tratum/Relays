from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse


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
