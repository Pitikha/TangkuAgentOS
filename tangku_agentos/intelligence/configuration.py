from __future__ import annotations

from .interfaces import IntelligenceConfiguration


class IntelligenceConfiguration(IntelligenceConfiguration):
    """Concrete intelligence configuration store."""

    def __init__(self) -> None:
        self._settings: dict[str, object] = {}

    def get(self, key: str) -> object:
        return self._settings.get(key)

    def set(self, key: str, value: object) -> None:
        self._settings[key] = value
