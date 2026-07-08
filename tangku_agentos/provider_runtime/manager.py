from __future__ import annotations

from __future__ import annotations

from ..model_runtime.models import ModelConfiguration
from .factory import ProviderFactory
from .interfaces import ProviderManager
from .registry import ProviderRegistry


class ProviderManager(ProviderManager):
    """Provider runtime manager."""

    def __init__(self, registry: ProviderRegistry | None = None, factory: ProviderFactory | None = None) -> None:
        self._registry = registry or ProviderRegistry()
        self._providers: dict[str, ModelConfiguration] = {}
        self._factory = factory or ProviderFactory()
        self._adapters: dict[str, object] = {}

    def add_provider(self, provider_id: str, configuration: ModelConfiguration) -> None:
        self._providers[provider_id] = configuration
        self._registry.register_provider(provider_id, configuration)
        self._adapters[provider_id] = self._factory.create(provider_id, configuration)

    def get_provider(self, provider_id: str) -> ModelConfiguration:
        return self._providers.get(provider_id) or self._registry.resolve_provider(provider_id)

    def list_providers(self) -> list[str]:
        return sorted(self._providers.keys())

    def remove_provider(self, provider_id: str) -> None:
        self._providers.pop(provider_id, None)
        self._registry._providers.pop(provider_id, None)
        self._adapters.pop(provider_id, None)

    def get_adapter(self, provider_id: str) -> object | None:
        return self._adapters.get(provider_id)
