import logging

import httpx

from app.core.constants import SYSTEM_REQUEST_ID
from app.core.logging import log_extra

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

logger = logging.getLogger(__name__)


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
        try:
            if payload.cc:
                return ProviderResult(
                    status=DeliveryStatus.PERMANENT_FAILURE,
                    provider=EmailNotificationProviders.MAILRELAY,
                    provider_error_code="UNSUPPORTED_CC",
                    error_message=(
                        "MailRelay REST API does not support CC recipients."
                    ),
                )

            if payload.bcc:
                return ProviderResult(
                    status=DeliveryStatus.PERMANENT_FAILURE,
                    provider=EmailNotificationProviders.MAILRELAY,
                    provider_error_code="UNSUPPORTED_BCC",
                    error_message=(
                        "MailRelay REST API does not support BCC recipients."
                    ),
                )

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
        ) as exc:
            logger.warning(
                "MailRelay request timed out.",
                extra=log_extra(
                    request_id=SYSTEM_REQUEST_ID,
                    error_message=exc,
                ),
            )

            return ProviderResult(
                status=DeliveryStatus.TEMPORARY_FAILURE,
                provider=EmailNotificationProviders.MAILRELAY,
                provider_error_code="TIMEOUT",
                error_message="Connection to MailRelay timed out.",
            )

        except (
            httpx.ConnectError,
            httpx.NetworkError,
        ) as exc:
            logger.warning(
                "MailRelay network error.",
                extra=log_extra(
                    request_id=SYSTEM_REQUEST_ID,
                    error_message=exc,
                ),
            )

            return ProviderResult(
                status=DeliveryStatus.TEMPORARY_FAILURE,
                provider=EmailNotificationProviders.MAILRELAY,
                provider_error_code="NETWORK_ERROR",
                error_message="Unable to connect to MailRelay.",
            )

        except httpx.RemoteProtocolError as exc:
            logger.warning(
                "MailRelay protocol error.",
                extra=log_extra(
                    request_id=SYSTEM_REQUEST_ID,
                    error_message=exc,
                ),
            )

            return ProviderResult(
                status=DeliveryStatus.TEMPORARY_FAILURE,
                provider=EmailNotificationProviders.MAILRELAY,
                provider_error_code="PROTOCOL_ERROR",
                error_message="MailRelay returned an invalid protocol response.",
            )

        # --------------------------------------------------
        # Unexpected Provider Failure
        # --------------------------------------------------

        except Exception as exc:
            logger.exception(
                "Unexpected MailRelay provider failure.",
                extra=log_extra(
                    request_id=SYSTEM_REQUEST_ID,
                    error_message=exc,
                ),
            )

            return ProviderResult(
                status=DeliveryStatus.TEMPORARY_FAILURE,
                provider=EmailNotificationProviders.MAILRELAY,
                provider_error_code="INTERNAL_PROVIDER_ERROR",
                error_message="Unexpected MailRelay provider failure.",
            )
