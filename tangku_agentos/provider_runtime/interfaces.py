from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from ..model_runtime.models import ModelConfiguration


class ProviderRegistryInterface(ABC):
    """Interface for provider registry operations."""

    @abstractmethod
    def register_provider(self, provider_id: str, configuration: ModelConfiguration) -> None:
        ...

    @abstractmethod
    def resolve_provider(self, provider_id: str) -> ModelConfiguration:
        ...

    @abstractmethod
    def list_providers(self) -> list[str]:
        ...


class ProviderManager(ABC):
    """Interface for provider runtime management."""

    @abstractmethod
    def add_provider(self, provider_id: str, configuration: ModelConfiguration) -> None:
        ...

    @abstractmethod
    def get_provider(self, provider_id: str) -> ModelConfiguration:
        ...

    @abstractmethod
    def remove_provider(self, provider_id: str) -> None:
        ...


class ProviderAdapter(ABC):
    """Interface for provider adapter abstraction."""

    @abstractmethod
    def send(self, request: dict[str, Any]) -> dict[str, Any]:
        ...


class ProviderFactory(ABC):
    """Interface for provider instance creation."""

    @abstractmethod
    def create(self, provider_id: str, configuration: ModelConfiguration) -> ProviderAdapter:
        ...


class ProviderConfiguration(ABC):
    """Interface for provider configuration."""

    @abstractmethod
    def get_configuration(self) -> dict[str, Any]:
        ...


class ProviderHealth(ABC):
    """Interface for provider health checks."""

    @abstractmethod
    def check(self, provider_id: str) -> dict[str, Any]:
        ...


class ProviderSession(ABC):
    """Interface for provider session management."""

    @abstractmethod
    def start(self, provider_id: str) -> str:
        ...

    @abstractmethod
    def end(self, session_id: str) -> None:
        ...
