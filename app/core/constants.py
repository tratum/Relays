from enum import StrEnum

SYSTEM_REQUEST_ID = "system"
API_VERSION = "/v1"


class NotificationChannel(StrEnum):
    EMAIL = "email"
    SMS = "sms"
    WEBHOOK = "webhook"
