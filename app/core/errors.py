from pydantic import UUID4, BaseModel, Field


class ErrorBody(BaseModel):
    code: str = Field(
        ...,
        description="Error Code",
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


def build_error(
    *,
    code: str,
    message: str,
    request_id: str | None,
) -> dict:
    return {
        "error": {
            "code": code,
            "message": message,
            "request_id": request_id,
        }
    }
