import httpx

from app.core.config import config

from ....providers.email.mailrelay.exceptions import MailRelayAPIError
from ....providers.email.mailrelay.schemas import (
    MailRelayErrorResponse,
    MailRelaySendRequest,
    MailRelaySendResponse,
)


class MailRelayClient:
    def __init__(self) -> None:
        timeout = httpx.Timeout(
            connect=5,
            read=config.MAILRELAY_REQUEST_TIMEOUT,
            write=config.MAILRELAY_REQUEST_TIMEOUT,
            pool=config.MAILRELAY_REQUEST_TIMEOUT,
        )

        self._client = httpx.AsyncClient(
            base_url=config.MAILRELAY_BASE_URL,
            timeout=timeout,
            headers={
                "Content-Type": "application/json",
                "X-AUTH-TOKEN": config.MAILRELAY_API_TOKEN,
            },
        )

    async def send(
        self, request: MailRelaySendRequest
    ) -> MailRelaySendResponse:
        response = await self._client.post(
            "/api/v1/send_emails",
            json=request.model_dump(
                mode="json",
                by_alias=True,
                exclude_none=True,
            ),
        )

        if response.is_error:
            await self._raise_mailrelay_error(response)

        body = response.json()

        if not isinstance(body, list):
            raise RuntimeError("Unexpected MailRelay Response Format")

        if len(body) != 1:
            raise RuntimeError(
                f"Expected One Recipient Response, recieved {len(body)}."
            )
        return MailRelaySendResponse.model_validate(body[0])

    async def close(self):
        await self._client.aclose()

    @staticmethod
    async def _raise_mailrelay_error(
        response: httpx.Response,
    ) -> None:
        try:
            error = MailRelayErrorResponse.model_validate(
                response.json(),
            )

            message = error.error

        except Exception:
            message = response.text or "Unknown MailRelay error."

        raise MailRelayAPIError(
            status_code=response.status_code,
            message=message,
        )
