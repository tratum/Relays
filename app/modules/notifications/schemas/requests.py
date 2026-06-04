from typing import Annotated, Literal

from pydantic import Field

from ..channels.email.schemas import EmailPayload
from ..channels.sms.schemas import SMSPayload
from ..channels.webhook.schemas import WebhookPayload
from .common import BaseNotificationRequest


class EmailNotificationRequest(BaseNotificationRequest):
    channel: Literal["email"] = Field(
        ...,
        description="Email notification channel",
    )
    payload: EmailPayload


class SMSNotificationRequest(BaseNotificationRequest):
    channel: Literal["sms"] = Field(
        ...,
        description="SMS notification channel",
    )
    payload: SMSPayload


class WebhookNotificationRequest(BaseNotificationRequest):
    channel: Literal["webhook"] = Field(
        ...,
        description="Webhook notification channel",
    )
    payload: WebhookPayload


NotificationRequestBody = Annotated[
    EmailNotificationRequest
    | SMSNotificationRequest
    | WebhookNotificationRequest,
    Field(discriminator="channel"),
]
