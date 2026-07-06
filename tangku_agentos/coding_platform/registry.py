from __future__ import annotations

from typing import Any, Dict

from .interfaces import CodingRegistryInterface


class CodingRegistry(CodingRegistryInterface):
    """Registry for coding platform components."""

    def __init__(self) -> None:
        self._registry: Dict[str, Any] = {}

    def register(self, key: str, value: Any) -> None:
        self._registry[key] = value

    def resolve(self, key: str) -> Any:
        return self._registry[key]

    def list_registered(self) -> list[str]:
        return list(self._registry.keys())
