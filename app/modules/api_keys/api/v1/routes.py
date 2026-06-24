from typing import Annotated

from asyncpg import UniqueViolationError
from fastapi import APIRouter, Depends, Header, status
from pydantic import UUID4

from app.core.error_codes import ErrorCode
from app.core.errors import APIException, ErrorResponse
from app.infra.db.session import get_pool
from app.infra.guards.jwt import authenticate_jwt

from ....workspaces.db.workspaces_queries import get_workspace_by_id
from ...db.api_keys_queries import (
    create_api_key,
    get_api_key_by_id_and_workspace,
    list_workspace_api_keys,
    revoke_api_key,
)
from ...schemas.request import APIKeyRequestBody
from ...schemas.response import (
    APIKeyListResponseBody,
    APIKeyResponseBody,
)
from ...security.apikey import (
    extract_prefix,
    generate_api_key,
    hash_api_key,
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
    response_model=APIKeyResponseBody,
    dependencies=[Depends(authenticate_jwt)],
)
async def create_api_key_route(
    req: APIKeyRequestBody,
    # TEMPORARY:
    # Workspace context is supplied via request header.
    #
    # Once JWT authentication is implemented:
    #
    # 1. JWT Guard resolves request.state.user_id
    # 2. Workspace membership is validated
    # 3. Workspace context is resolved from the authenticated user
    # 4. The X-Workspace-Id header will be removed
    workspace_id: Annotated[
        UUID4,
        Header(
            alias="X-Workspace-Id",
        ),
    ],
):
    pool = get_pool()
    async with pool.acquire() as conn:
        if await get_workspace_by_id(conn, workspace_id) is None:
            raise APIException(
                status_code=status.HTTP_404_NOT_FOUND,
                code=ErrorCode.NOT_FOUND,
                message="Workspace Not Found",
            )

        key = generate_api_key()
        key_prefix = extract_prefix(key)
        key_hash = hash_api_key(key)

        try:
            async with conn.transaction():
                api_key_record = await create_api_key(
                    conn,
                    workspace_id=workspace_id,
                    name=req.name,
                    key_prefix=key_prefix,
                    key_hash=key_hash,
                    expires_at=req.expires_at,
                )

        except UniqueViolationError:
            raise APIException(
                status_code=status.HTTP_409_CONFLICT,
                code=ErrorCode.CONFLICT,
                message="API Key Name already exists",
            )

        return APIKeyResponseBody(
            id=api_key_record["id"],
            name=api_key_record["name"],
            key_prefix=api_key_record["key_prefix"],
            api_key=key,
            status=api_key_record["status"],
            expires_at=api_key_record["expires_at"],
            created_at=api_key_record["created_at"],
            last_used_at=None,
            revoked_at=None,
            updated_at=api_key_record["updated_at"],
        )


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
async def list_api_keys_route(
    workspace_id: Annotated[
        UUID4,
        Header(
            alias="X-Workspace-Id",
        ),
    ],
):
    pool = get_pool()

    async with pool.acquire() as conn:
        workspace = await get_workspace_by_id(
            conn,
            workspace_id,
        )

        if workspace is None:
            raise APIException(
                status_code=status.HTTP_404_NOT_FOUND,
                code=ErrorCode.NOT_FOUND,
                message="Workspace not found",
            )

        api_keys = await list_workspace_api_keys(
            conn,
            workspace_id,
        )

        return [
            APIKeyListResponseBody(
                id=api_key["id"],
                name=api_key["name"],
                key_prefix=api_key["key_prefix"],
                status=api_key["status"],
                expires_at=api_key["expires_at"],
                last_used_at=api_key["last_used_at"],
                revoked_at=api_key["revoked_at"],
                created_at=api_key["created_at"],
                updated_at=api_key["updated_at"],
            )
            for api_key in api_keys
        ]


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
    dependencies=[Depends(authenticate_jwt)],
)
async def get_api_key_route(
    api_key_id: UUID4,
    workspace_id: Annotated[
        UUID4,
        Header(
            alias="X-Workspace-Id",
        ),
    ],
):
    pool = get_pool()

    async with pool.acquire() as conn:
        workspace = await get_workspace_by_id(
            conn,
            workspace_id,
        )

        if workspace is None:
            raise APIException(
                status_code=status.HTTP_404_NOT_FOUND,
                code=ErrorCode.NOT_FOUND,
                message="Workspace not found",
            )

        api_key = await get_api_key_by_id_and_workspace(
            conn,
            api_key_id,
            workspace_id,
        )

        if api_key is None:
            raise APIException(
                status_code=status.HTTP_404_NOT_FOUND,
                code=ErrorCode.NOT_FOUND,
                message="API Key not found",
            )

        return APIKeyListResponseBody(
            id=api_key["id"],
            name=api_key["name"],
            key_prefix=api_key["key_prefix"],
            status=api_key["status"],
            expires_at=api_key["expires_at"],
            last_used_at=api_key["last_used_at"],
            revoked_at=api_key["revoked_at"],
            created_at=api_key["created_at"],
            updated_at=api_key["updated_at"],
        )


# ----------------
# Revoke API Key
# ----------------


@router.delete(
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
    response_model=APIKeyResponseBody,
    dependencies=[Depends(authenticate_jwt)],
)
async def revoke_api_key_route(
    api_key_id: UUID4,
    workspace_id: Annotated[
        UUID4,
        Header(
            alias="X-Workspace-Id",
        ),
    ],
):
    pool = get_pool()

    async with pool.acquire() as conn:
        workspace = await get_workspace_by_id(
            conn,
            workspace_id,
        )

        if workspace is None:
            raise APIException(
                status_code=status.HTTP_404_NOT_FOUND,
                code=ErrorCode.NOT_FOUND,
                message="API Key not found",
            )

        async with conn.transaction():
            revoked_api_key = await revoke_api_key(
                conn,
                api_key_id,
                workspace_id,
            )

        if revoked_api_key is None:
            raise APIException(
                status_code=status.HTTP_404_NOT_FOUND,
                code=ErrorCode.NOT_FOUND,
                message="API Key not found",
            )

        return APIKeyResponseBody(
            id=revoked_api_key["id"],
            name=revoked_api_key["name"],
            key_prefix=revoked_api_key["key_prefix"],
            status=revoked_api_key["status"],
            expires_at=revoked_api_key["expires_at"],
            last_used_at=revoked_api_key["last_used_at"],
            revoked_at=revoked_api_key["revoked_at"],
            created_at=revoked_api_key["created_at"],
            updated_at=revoked_api_key["updated_at"],
        )
