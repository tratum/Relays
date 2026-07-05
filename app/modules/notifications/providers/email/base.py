from typing import Protocol

from ...channels.email.schemas import EmailPayload
from .result import ProviderResult


class EmailProvider(Protocol):
    async def send(
        self,
        payload: EmailPayload,
    ) -> ProviderResult:
        """Send an email using the provider."""
        ...
