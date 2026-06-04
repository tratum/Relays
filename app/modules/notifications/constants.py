from enum import Enum


class NotificationState(str, Enum):
    CREATED = "created"
    QUEUED = "queued"
    PROCESSING = "processing"
    SENT = "sent"
    FAIL = "failed"
