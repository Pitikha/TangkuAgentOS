"""Adapter for the TangkuAgentOS Provider Runtime."""

from __future__ import annotations

from typing import Any

from .interfaces import ProviderAdapter


class BaseProviderAdapter(ProviderAdapter):
    """Base provider adapter implementation."""

    def __init__(self, provider_id: str) -> None:
        self.provider_id = provider_id

    def initialize(self, settings: dict[str, Any]) -> None:
        """Initialize the provider adapter."""
        self.settings = settings

    def send(self, request: dict[str, Any]) -> dict[str, Any]:
        """Send a request to the provider."""
        raise NotImplementedError("Subclasses must implement send")

    async def send_async(self, request: dict[str, Any]) -> dict[str, Any]:
        """Send a request to the provider asynchronously."""
        return self.send(request)

    def supports(self, capability: str) -> bool:
        """Check if the provider supports a capability."""
        return False

    def health_check(self) -> dict[str, Any]:
        """Perform a health check."""
        return {"status": "healthy", "latency_ms": 0.0}


class ProviderAdapter(BaseProviderAdapter):
    """Default provider adapter."""

    def send(self, request: dict[str, Any]) -> dict[str, Any]:
        """Send a request to the provider."""
        return {"provider_id": self.provider_id, "request": request}
