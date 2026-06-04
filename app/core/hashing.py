import hashlib
import json


def canonical_hash(payload: dict):
    # Normalizes Payload Before hashing
    normalized = json.dumps(
        payload,
        sort_keys=True,  # Ensure Keys are sorted alphabetically
        separators=(",", ":"),
    )
    return hashlib.sha256(
        normalized.encode()
    ).hexdigest()  # converts the string into bytes
