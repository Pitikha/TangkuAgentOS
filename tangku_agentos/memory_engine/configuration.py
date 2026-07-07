from __future__ import annotations

from .interfaces import MemoryConfigurationManager
from .models import MemoryConfiguration


class MemoryConfigurationManagerImpl(MemoryConfigurationManager):
    """Skeleton memory configuration manager."""

    def __init__(self) -> None:
        self._configurations: dict[str, MemoryConfiguration] = {}

    def get_configuration(self, namespace: str) -> MemoryConfiguration:
        return self._configurations.get(namespace, MemoryConfiguration())

    def set_configuration(self, namespace: str, configuration: MemoryConfiguration) -> None:
        self._configurations[namespace] = configuration
