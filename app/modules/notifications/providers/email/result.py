from pydantic import BaseModel

from ...constants import DeliveryStatus, EmailNotificationProviders


class ProviderResult(BaseModel):
    status: DeliveryStatus
    provider: EmailNotificationProviders
    provider_message_id: str | None = None
    provider_error_code: str | None = None
    error_message: str | None = None
    raw_provider_response: dict | None = None
