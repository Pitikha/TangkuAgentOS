from __future__ import annotations

from typing import Dict, Any

from .interfaces import BackgroundWorkerManager


class ServiceRegistry:
    """Registry for background service handlers."""

    def __init__(self) -> None:
        self._services: Dict[str, Any] = {}

    def register(self, service_type: str, handler: Any) -> None:
        self._services[service_type] = handler

    def resolve(self, service_type: str) -> Any:
        return self._services[service_type]

    def list_registered(self) -> list[str]:
        return list(self._services.keys())
