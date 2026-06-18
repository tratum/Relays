from datetime import datetime, timezone

from fastapi import Request, status

from app.core.error_codes import ErrorCode
from app.core.errors import APIException
from app.infra.db.session import get_pool
from app.modules.api_keys.db.api_keys_queries import (
    get_api_key_by_prefix,
)
from app.modules.api_keys.security.apikey import (
    extract_prefix,
    hash_api_key,
    verify_api_key_hash,
)


async def authenticate_api_key(
    req: Request,
) -> None:
    authorization = req.headers.get("Authorization")

    if not authorization:
        raise APIException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            code=ErrorCode.UNAUTHORIZED,
            message="Missing Authorization header",
        )

    scheme, _, api_key = authorization.partition(" ")

    if scheme.lower() != "bearer" or not api_key:
        raise APIException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            code=ErrorCode.UNAUTHORIZED,
            message="Invalid Authorization header",
        )

    key_prefix = extract_prefix(api_key)

    pool = get_pool()

    async with pool.acquire() as conn:
        api_key_record = await get_api_key_by_prefix(
            conn,
            key_prefix,
        )

    if api_key_record is None:
        raise APIException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            code=ErrorCode.UNAUTHORIZED,
            message="Invalid API Key",
        )

    incoming_hash = hash_api_key(api_key)

    if not verify_api_key_hash(
        api_key_record["key_hash"],
        incoming_hash,
    ):
        raise APIException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            code=ErrorCode.UNAUTHORIZED,
            message="Invalid API Key",
        )

    if api_key_record["status"] != "active":
        raise APIException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            code=ErrorCode.UNAUTHORIZED,
            message="API Key has been revoked",
        )

    expires_at = api_key_record["expires_at"]

    if expires_at is not None and expires_at <= datetime.now(timezone.utc):
        raise APIException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            code=ErrorCode.UNAUTHORIZED,
            message="API Key has expired",
        )

    req.state.api_key_id = api_key_record["id"]
    req.state.workspace_id = api_key_record["workspace_id"]

    return None
