from fastapi import APIRouter, status

from app.core.errors import ErrorResponse

from ...schemas.request import APIKeysRequestBody
from ...schemas.response import (
    APIKeyListResponseBody,
    APIKeysResponseBody,
)

router = APIRouter(tags=["API Keys API"])


# -------------
# Health Check
# -------------


@router.get(
    "/api-keys/health",
    summary="API Keys API Health Check",
)
async def health_check():
    return {"status": "ok"}


# ----------------
# Create API Key
# ----------------


@router.post(
    path="/api-keys",
    summary="Create API Key",
    description="Create a new API key for a workspace.",
    status_code=status.HTTP_201_CREATED,
    responses={
        400: {"model": ErrorResponse},
        401: {"model": ErrorResponse},
        403: {"model": ErrorResponse},
        404: {"model": ErrorResponse},
        409: {"model": ErrorResponse},
        500: {"model": ErrorResponse},
    },
    response_model=APIKeysResponseBody,
)
async def create_api_key_route(
    req: APIKeysRequestBody,
):
    raise NotImplementedError


# ----------------
# List API Keys
# ----------------


@router.get(
    path="/api-keys",
    summary="List API Keys",
    description="List all API keys belonging to a workspace.",
    responses={
        400: {"model": ErrorResponse},
        401: {"model": ErrorResponse},
        403: {"model": ErrorResponse},
        404: {"model": ErrorResponse},
        500: {"model": ErrorResponse},
    },
    response_model=list[APIKeyListResponseBody],
)
async def list_api_keys_route():
    raise NotImplementedError


# ----------------
# Get API Key
# ----------------


@router.get(
    path="/api-keys/{api_key_id}",
    summary="Get API Key",
    description="Get API key metadata.",
    responses={
        400: {"model": ErrorResponse},
        401: {"model": ErrorResponse},
        403: {"model": ErrorResponse},
        404: {"model": ErrorResponse},
        500: {"model": ErrorResponse},
    },
    response_model=APIKeyListResponseBody,
)
async def get_api_key_route(
    api_key_id: str,
):
    raise NotImplementedError


# ----------------
# Revoke API Key
# ----------------


@router.post(
    path="/api-keys/{api_key_id}/revoke",
    summary="Revoke API Key",
    description="Permanently revoke an API key.",
    responses={
        400: {"model": ErrorResponse},
        401: {"model": ErrorResponse},
        403: {"model": ErrorResponse},
        404: {"model": ErrorResponse},
        409: {"model": ErrorResponse},
        500: {"model": ErrorResponse},
    },
    response_model=APIKeyListResponseBody,
)
async def revoke_api_key_route(
    api_key_id: str,
):
    raise NotImplementedError
