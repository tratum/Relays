import hashlib
import secrets

from .constants import (
    API_KEY_PREFIX,
    API_KEY_PREFIX_LENGTH,
    API_KEY_SECRET_LENGTH,
)


def generate_api_key() -> str:
    """
    Generate a new API key.
    """
    secret_part = secrets.token_urlsafe(API_KEY_SECRET_LENGTH)

    return f"{API_KEY_PREFIX}_{secret_part}"


def extract_prefix(api_key: str) -> str:
    """
    Extract the lookup prefix from an API key.
    """
    if len(api_key) < API_KEY_PREFIX_LENGTH:
        raise ValueError("Invalid API key format.")
    return api_key[:API_KEY_PREFIX_LENGTH]


def hash_api_key(api_key: str) -> str:
    """
    Compute the SHA512 hash of an API key.
    """
    return hashlib.sha512(api_key.encode("utf-8")).hexdigest()


def verify_api_key_hash(
    stored_hash: str,
    computed_hash: str,
) -> bool:
    """
    Constant-time hash comparison.
    """
    return secrets.compare_digest(
        stored_hash,
        computed_hash,
    )
