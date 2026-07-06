from __future__ import annotations

from .interfaces import ProviderHealth


class ProviderHealth(ProviderHealth):
    """Provider health manager."""

    def __init__(self) -> None:
        self._health: dict[str, dict[str, object]] = {}

    def check(self, provider_id: str) -> dict[str, object]:
        return self._health.get(provider_id, {"provider_id": provider_id, "status": "unknown"})
