import httpx

from ....channels.email.schemas import EmailPayload
from ....constants import (
    MAILRELAY_RETRYABLE_STATUS_CODES,
    DeliveryStatus,
    EmailNotificationProviders,
)
from ....providers.email.base import EmailProvider
from ....providers.email.mailrelay.client import MailRelayClient
from ....providers.email.mailrelay.exceptions import MailRelayAPIError
from ....providers.email.mailrelay.mapper import build_mailrelay_request
from ....providers.email.result import ProviderResult


class MailRelayProvider(EmailProvider):
    def __init__(
        self,
        client: MailRelayClient,
    ) -> None:
        self._client = client

    async def send(
        self,
        payload: EmailPayload,
    ) -> ProviderResult:
        if payload.cc:
            return ProviderResult(
                status=DeliveryStatus.PERMANENT_FAILURE,
                provider=EmailNotificationProviders.MAILRELAY,
                error_message="MailRelay REST API does not support CC recipients.",
            )

        if payload.bcc:
            return ProviderResult(
                status=DeliveryStatus.PERMANENT_FAILURE,
                provider=EmailNotificationProviders.MAILRELAY,
                error_message="MailRelay REST API does not support BCC recipients.",
            )

        try:
            request = build_mailrelay_request(payload)
            response = await self._client.send(request)

            return ProviderResult(
                status=DeliveryStatus.SUCCESS,
                provider=EmailNotificationProviders.MAILRELAY,
                provider_message_id=str(response.id),
                raw_provider_response=response.model_dump(mode="json"),
            )

        except MailRelayAPIError as exc:
            return ProviderResult(
                status=(
                    DeliveryStatus.TEMPORARY_FAILURE
                    if exc.status_code in MAILRELAY_RETRYABLE_STATUS_CODES
                    else DeliveryStatus.PERMANENT_FAILURE
                ),
                provider=EmailNotificationProviders.MAILRELAY,
                provider_error_code=str(exc.status_code),
                error_message=str(exc),
            )

        except (
            httpx.TimeoutException,
            httpx.ConnectTimeout,
            httpx.ReadTimeout,
            httpx.WriteTimeout,
            httpx.PoolTimeout,
            httpx.ConnectError,
            httpx.NetworkError,
            httpx.RemoteProtocolError,
        ) as exc:
            return ProviderResult(
                status=DeliveryStatus.TEMPORARY_FAILURE,
                provider=EmailNotificationProviders.MAILRELAY,
                error_message=str(exc),
            )
