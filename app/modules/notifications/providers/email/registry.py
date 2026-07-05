from app.modules.notifications.constants import EmailNotificationProviders
from app.modules.notifications.providers.email.base import EmailProvider
from app.modules.notifications.providers.email.mailrelay.client import (
    MailRelayClient,
)
from app.modules.notifications.providers.email.mailrelay.provider import (
    MailRelayProvider,
)


class EmailProviderRegsitry:
    def __init__(self) -> None:
        self._providers: dict[
            EmailNotificationProviders,
            EmailProvider,
        ] = {}

    def get(
        self,
        provider: EmailNotificationProviders,
    ) -> EmailProvider:
        existing_provider = self._providers.get(provider)

        if existing_provider is not None:
            return existing_provider

        if provider == EmailNotificationProviders.MAILRELAY:
            provider_instance = MailRelayProvider(
                client=MailRelayClient(),
            )

        else:
            raise ValueError(f"Unsupported Email Provider: {provider}")

        self._providers[provider] = provider_instance

        return provider_instance


email_provider_registry = EmailProviderRegsitry()
