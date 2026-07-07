from __future__ import annotations

from .interfaces import KnowledgeConfigurationManagerInterface
from .models import KnowledgeConfiguration


class KnowledgeConfigurationManager(KnowledgeConfigurationManagerInterface):
    """Knowledge configuration manager."""

    def __init__(self) -> None:
        self._configurations: dict[str, KnowledgeConfiguration] = {}

    def get_configuration(self, namespace: str) -> KnowledgeConfiguration:
        return self._configurations.get(namespace, KnowledgeConfiguration())

    def set_configuration(self, namespace: str, configuration: KnowledgeConfiguration) -> None:
        self._configurations[namespace] = configuration
