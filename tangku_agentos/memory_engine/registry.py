from __future__ import annotations

from typing import Dict

from .exceptions import MemoryRegistryError
from .interfaces import MemoryRegistryInterface
from .models import MemoryConfiguration


class MemoryRegistry(MemoryRegistryInterface):
    """Registry for memory namespaces and configurations."""

    def __init__(self) -> None:
        self._configurations: Dict[str, MemoryConfiguration] = {}

    def register(self, namespace: str, configuration: MemoryConfiguration) -> None:
        self._configurations[namespace] = configuration

    def resolve(self, namespace: str) -> MemoryConfiguration:
        configuration = self._configurations.get(namespace)
        if configuration is None:
            raise MemoryRegistryError(f'Memory namespace not found: {namespace}')
        return configuration

    def list_namespaces(self) -> list[str]:
        return list(self._configurations.keys())
