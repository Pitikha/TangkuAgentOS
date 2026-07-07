from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from .models import (
    Model,
    ModelConfiguration,
    ModelRequest,
    ModelResponse,
    ModelResult,
    ModelSession,
)


class ModelRegistryInterface(ABC):
    """Interface for registering and resolving models."""

    @abstractmethod
    def register_model(self, model: Model) -> None:
        ...

    @abstractmethod
    def resolve_model(self, model_id: str) -> Model:
        ...

    @abstractmethod
    def list_models(self) -> list[Model]:
        ...


class ModelProviderRegistryInterface(ABC):
    """Interface for registering model providers."""

    @abstractmethod
    def register_provider(self, provider_id: str, configuration: ModelConfiguration) -> None:
        ...

    @abstractmethod
    def resolve_provider(self, provider_id: str) -> ModelConfiguration:
        ...

    @abstractmethod
    def list_providers(self) -> list[str]:
        ...


class ModelRuntimeManager(ABC):
    """Interface for managing model runtime lifecycle."""

    @abstractmethod
    def register_model(self, model: Model) -> None:
        ...

    @abstractmethod
    def select_model(self, capability: str) -> Model:
        ...

    @abstractmethod
    def execute(self, request: ModelRequest) -> ModelResponse:
        ...


class ModelResolver(ABC):
    """Interface for resolving a model for a request."""

    @abstractmethod
    def resolve(self, request: ModelRequest) -> Model:
        ...


class ModelRouter(ABC):
    """Interface for routing model requests."""

    @abstractmethod
    def route(self, request: ModelRequest) -> ModelResponse:
        ...


class ModelScheduler(ABC):
    """Interface for scheduling model execution."""

    @abstractmethod
    def schedule(self, request: ModelRequest, cron_expression: str) -> str:
        ...

    @abstractmethod
    def cancel(self, schedule_id: str) -> None:
        ...


class ModelSessionManager(ABC):
    """Interface for model session lifecycle management."""

    @abstractmethod
    def create_session(self, model_id: str) -> ModelSession:
        ...

    @abstractmethod
    def close_session(self, session_id: str) -> None:
        ...


class ModelLifecycleManager(ABC):
    """Interface for managing model lifecycle transitions."""

    @abstractmethod
    def deploy(self, model: Model) -> None:
        ...

    @abstractmethod
    def retire(self, model_id: str) -> None:
        ...


class ModelHealthManager(ABC):
    """Interface for model health monitoring."""

    @abstractmethod
    def check_model(self, model_id: str) -> dict[str, Any]:
        ...


class ModelStatisticsManager(ABC):
    """Interface for collecting model runtime statistics."""

    @abstractmethod
    def record_usage(self, model_id: str, usage: dict[str, Any]) -> None:
        ...

    @abstractmethod
    def get_statistics(self, model_id: str) -> dict[str, Any]:
        ...
