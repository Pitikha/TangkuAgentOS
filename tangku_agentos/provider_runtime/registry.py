from __future__ import annotations

from typing import Dict

from .interfaces import ProviderRegistryInterface
from ..model_runtime.models import ModelConfiguration


class ProviderRegistry(ProviderRegistryInterface):
    """Registry for provider configurations."""

    def __init__(self) -> None:
        self._providers: Dict[str, ModelConfiguration] = {}

    def register_provider(self, provider_id: str, configuration: ModelConfiguration) -> None:
        self._providers[provider_id] = configuration

    def resolve_provider(self, provider_id: str) -> ModelConfiguration:
        return self._providers[provider_id]

    def list_providers(self) -> list[str]:
        return list(self._providers.keys())
