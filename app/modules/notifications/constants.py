from enum import Enum


class NotificationState(str, Enum):
    CREATED = "created"
    QUEUED = "queued"
    PROCESSING = "processing"
    SENT = "sent"
    FAIL = "failed"


class EmailNotificationProviders(str, Enum):
    MAILRELAY = "mailrelay"


class DeliveryStatus(str, Enum):
    SUCCESS = "success"
    TEMPORARY_FAILURE = "temporary_failure"
    PERMANENT_FAILURE = "permanent_failure"


MAILRELAY_RETRYABLE_STATUS_CODES = frozenset(
    {
        429,
        500,
        502,
        503,
        504,
    }
)
