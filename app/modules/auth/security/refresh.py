import hashlib
import secrets

from ..constants import REFRESH_TOKEN_LENGTH_BYTES

"""
Uses a Cryptographically Random Opaque String
as a Refresh Token
"""


def generate_refresh_token():
    return secrets.token_urlsafe(REFRESH_TOKEN_LENGTH_BYTES)


def hash_refresh_token(refresh_token: str):
    return hashlib.sha512(refresh_token.encode("utf-8")).hexdigest()


def verify_refresh_token(computed_hash: str, stored_hash: str):
    return secrets.compare_digest(
        computed_hash,
        stored_hash,
    )
