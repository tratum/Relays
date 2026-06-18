from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from uuid import UUID

import jwt
from fastapi import status
from jwt import (
    ExpiredSignatureError,
    InvalidIssuedAtError,
    InvalidIssuerError,
    InvalidTokenError,
    MissingRequiredClaimError,
)

from app.core.config import config
from app.core.error_codes import ErrorCode
from app.core.errors import APIException

from ..constants import (
    JWT_ACCESS_TOKEN_TTL_SECONDS,
    JWT_ACCESS_TOKEN_TYPE,
    JWT_ISSUER,
    JWT_VERSION,
    REGISTRATION_TOKEN_TTL_SECONDS,
    REGISTRATION_TOKEN_TYPE,
)


@dataclass(frozen=True)
class AccessTokenPayload:
    iss: str
    sub: UUID
    type: str
    ver: int
    iat: int
    exp: int


@dataclass(frozen=True)
class RegistrationTokenPayload:
    iss: str
    email: str
    type: str
    iat: int
    exp: int


def create_access_token(
    user_id: UUID,
) -> str:
    now = datetime.now(UTC)
    expires_at = now + timedelta(
        seconds=JWT_ACCESS_TOKEN_TTL_SECONDS,
    )

    payload = {
        "iss": JWT_ISSUER,
        "sub": str(user_id),
        "type": JWT_ACCESS_TOKEN_TYPE,
        "ver": JWT_VERSION,
        "iat": int(now.timestamp()),
        "exp": int(expires_at.timestamp()),
    }

    return jwt.encode(
        payload=payload,
        key=config.JWT_SECRET,
        algorithm=config.JWT_ALGORITHM,
    )


def create_registration_token(
    email: str,
) -> str:
    now = datetime.now(UTC)
    expires_at = now + timedelta(
        seconds=REGISTRATION_TOKEN_TTL_SECONDS,
    )

    payload = {
        "iss": JWT_ISSUER,
        "email": email,
        "type": REGISTRATION_TOKEN_TYPE,
        "iat": int(now.timestamp()),
        "exp": int(expires_at.timestamp()),
    }

    return jwt.encode(
        payload=payload,
        key=config.JWT_SECRET,
        algorithm=config.JWT_ALGORITHM,
    )


def decode_access_token(
    token: str,
) -> AccessTokenPayload:
    try:
        payload = jwt.decode(
            jwt=token,
            key=config.JWT_SECRET,
            algorithms=[config.JWT_ALGORITHM],
            issuer=JWT_ISSUER,
            options={
                "require": [
                    "iss",
                    "sub",
                    "type",
                    "ver",
                    "iat",
                    "exp",
                ]
            },
        )

    except ExpiredSignatureError:
        raise APIException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            code=ErrorCode.ACCESS_TOKEN_EXPIRED,
            message="Access token expired",
        )

    except MissingRequiredClaimError:
        raise APIException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            code=ErrorCode.INVALID_ACCESS_TOKEN,
            message="Missing required token claim",
        )

    except InvalidIssuedAtError:
        raise APIException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            code=ErrorCode.INVALID_ACCESS_TOKEN,
            message="Invalid token issued-at timestamp",
        )

    except InvalidIssuerError:
        raise APIException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            code=ErrorCode.INVALID_ACCESS_TOKEN,
            message="Invalid access token issuer",
        )

    except InvalidTokenError:
        raise APIException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            code=ErrorCode.INVALID_ACCESS_TOKEN,
            message="Invalid access token",
        )

    if payload.get("type") != JWT_ACCESS_TOKEN_TYPE:
        raise APIException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            code=ErrorCode.INVALID_ACCESS_TOKEN,
            message="Invalid access token type",
        )

    if payload.get("ver") != JWT_VERSION:
        raise APIException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            code=ErrorCode.INVALID_ACCESS_TOKEN,
            message="Unsupported access token version",
        )

    try:
        uid = UUID(payload["sub"])

    except (ValueError, TypeError):
        raise APIException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            code=ErrorCode.INVALID_ACCESS_TOKEN,
            message="Invalid token subject",
        )

    return AccessTokenPayload(
        iss=payload["iss"],
        sub=uid,
        type=payload["type"],
        ver=payload["ver"],
        iat=payload["iat"],
        exp=payload["exp"],
    )


def decode_registration_token(
    token: str,
) -> RegistrationTokenPayload:
    try:
        payload = jwt.decode(
            jwt=token,
            key=config.JWT_SECRET,
            algorithms=[config.JWT_ALGORITHM],
            issuer=JWT_ISSUER,
            options={
                "require": [
                    "iss",
                    "email",
                    "type",
                    "iat",
                    "exp",
                ]
            },
        )

    except ExpiredSignatureError:
        raise APIException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            code=ErrorCode.INVALID_REQUEST,
            message="Registration token expired",
        )

    except MissingRequiredClaimError:
        raise APIException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            code=ErrorCode.INVALID_REQUEST,
            message="Missing required token claim",
        )

    except InvalidIssuedAtError:
        raise APIException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            code=ErrorCode.INVALID_REQUEST,
            message="Invalid token issued-at timestamp",
        )

    except InvalidIssuerError:
        raise APIException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            code=ErrorCode.INVALID_REQUEST,
            message="Invalid registration token issuer",
        )

    except InvalidTokenError:
        raise APIException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            code=ErrorCode.INVALID_REQUEST,
            message="Invalid registration token",
        )

    if payload.get("type") != REGISTRATION_TOKEN_TYPE:
        raise APIException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            code=ErrorCode.INVALID_REQUEST,
            message="Invalid registration token type",
        )

    email = payload.get("email")

    if not isinstance(email, str) or not email:
        raise APIException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            code=ErrorCode.INVALID_REQUEST,
            message="Invalid registration token email",
        )

    return RegistrationTokenPayload(
        iss=payload["iss"],
        email=email,
        type=payload["type"],
        iat=payload["iat"],
        exp=payload["exp"],
    )
