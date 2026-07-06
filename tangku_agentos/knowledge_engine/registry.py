from __future__ import annotations

from typing import Dict

from .exceptions import KnowledgeRegistryError
from .interfaces import KnowledgeRegistryInterface
from .models import KnowledgeConfiguration


class KnowledgeRegistry(KnowledgeRegistryInterface):
    """Registry for knowledge namespaces."""

    def __init__(self) -> None:
        self._configurations: Dict[str, KnowledgeConfiguration] = {}

    def register(self, namespace: str, configuration: KnowledgeConfiguration) -> None:
        self._configurations[namespace] = configuration

    def resolve(self, namespace: str) -> KnowledgeConfiguration:
        configuration = self._configurations.get(namespace)
        if configuration is None:
            raise KnowledgeRegistryError(f'Knowledge namespace not found: {namespace}')
        return configuration

    def list_namespaces(self) -> list[str]:
        return list(self._configurations.keys())
