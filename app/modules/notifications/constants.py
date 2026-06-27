from enum import Enum


class NotificationState(str, Enum):
    CREATED = "created"
    QUEUED = "queued"
    PROCESSING = "processing"
    SENT = "sent"
    FAIL = "failed"


class EmailNotificationProvider(str, Enum):
    MAILRELAY = "mailrelay"
    FAKE = "fake"


class DeliveryStatus(str, Enum):
    SUCCESS = "success"
    TEMPORARY_FAILURE = "temporary_failure"
    PERMANENT_FAILURE = "permanent_failure"
