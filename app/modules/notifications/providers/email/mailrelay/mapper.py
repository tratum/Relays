from app.core.config import config

from ....channels.email.schemas import EmailPayload
from ....providers.email.mailrelay.schemas import (
    MailRelayRecipient,
    MailRelaySender,
    MailRelaySendRequest,
)


def build_mailrelay_request(payload: EmailPayload) -> MailRelaySendRequest:
    """
    Maps a Relays EmailPayload into a MailRelay API request.

    Raises:
        NotImplementedError:
            If the payload contains features not supported by the
            MailRelay REST API.
    """

    return MailRelaySendRequest(
        from_=MailRelaySender(
            email=config.MAILRELAY_SENDER_EMAIL,
            name=config.MAILRELAY_SENDER_NAME,
        ),
        to=[
            MailRelayRecipient(
                email=payload.to,
            )
        ],
        subject=payload.subject,
        html_part=payload.html_body,
        text_part_auto=True,
    )
