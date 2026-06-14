from app.core.error_codes import ErrorCode
from pydantic import UUID4, BaseModel, Field


class ErrorBody(BaseModel):
    code: ErrorCode = Field(
        ...,
        description="Error code",
        examples=["invalid_request"],
    )

    message: str = Field(
        ...,
        description="Human-readable error message",
    )

    request_id: UUID4 | None = Field(
        None,
        description="Request identifier",
    )


class ErrorResponse(BaseModel):
    error: ErrorBody


class APIException(Exception):
    def __init__(
        self,
        *,
        status_code: int,
        code: ErrorCode,
        message: str,
    ) -> None:
        self.status_code = status_code
        self.code = code
        self.message = message

        super().__init__(message)


def build_error(
    *,
    code: ErrorCode,
    message: str,
    request_id: UUID4 | None,
) -> dict:
    return ErrorResponse(
        error=ErrorBody(
            code=code,
            message=message,
            request_id=request_id,
        ),
    ).model_dump(mode="json")
