from enum import Enum

API_KEY_PREFIX = "rly_"
API_KEY_PREFIX_LENGTH = 12
API_KEY_SECRET_LENGTH = 48

API_KEY_STATUS_ACTIVE = "active"
API_KEY_STATUS_REVOKED = "revoked"


class APIKeyStatus(str, Enum):
    ACTIVE = "active"
    REVOKED = "revoked"
