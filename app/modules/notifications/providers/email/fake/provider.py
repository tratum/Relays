from typing import Any

import httpx

from ....channels.email.schemas import EmailPayload
from ....constants import (
    DeliveryStatus,
    EmailNotificationProviders,
)
from ..base import EmailProvider
from ..result import ProviderResult


class FakeProvider(EmailProvider):
    def __init__(self) -> None:
        self._notification: dict[str, Any] | None = None

    def configure(
        self,
        notification: dict[str, Any],
    ) -> None:
        self._notification = notification

    async def send(
        self,
        payload: EmailPayload,
    ) -> ProviderResult:
        if self._notification is None:
            raise RuntimeError("FakeProvider was not configured.")

        metadata = self._notification.get("metadata") or {}

        testing = metadata.get("testing") or {}

        sequence = testing.get("sequence", [])

        attempt = self._notification["attempt_count"]

        if attempt >= len(sequence):
            outcome = "success"
        else:
            outcome = sequence[attempt]

        match outcome:
            case DeliveryStatus.SUCCESS:
                return ProviderResult(
                    status=DeliveryStatus.SUCCESS,
                    provider=EmailNotificationProviders.FAKE,
                    provider_message_id=f"fake-{attempt}",
                    raw_provider_response={
                        "fake": True,
                        "attempt": attempt,
                        "outcome": outcome,
                    },
                )

            case DeliveryStatus.TEMPORARY_FAILURE:
                return ProviderResult(
                    status=DeliveryStatus.TEMPORARY_FAILURE,
                    provider=EmailNotificationProviders.FAKE,
                    error_message="Simulated temporary failure.",
                )

            case DeliveryStatus.PERMANENT_FAILURE:
                return ProviderResult(
                    status=DeliveryStatus.PERMANENT_FAILURE,
                    provider=EmailNotificationProviders.FAKE,
                    error_message="Simulated permanent failure.",
                )

            case "timeout":
                raise httpx.TimeoutException("Simulated timeout.")

            case "network_error":
                raise httpx.ConnectError("Simulated network failure.")

            case _:
                raise RuntimeError(f"Unknown fake provider outcome: {outcome}")
