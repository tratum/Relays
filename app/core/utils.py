import hashlib
import json
from enum import Enum


class NotificationState(str, Enum):
    CREATED = "created"
    QUEUED = "queued"
    PROCESSING = "processing"
    SENT = "sent"
    FAIL = "failed"


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
