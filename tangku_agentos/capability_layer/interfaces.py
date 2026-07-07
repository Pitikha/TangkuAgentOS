from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Protocol

from .models import CapabilityContext, CapabilityMetadata, CapabilityRequest, CapabilityResponse, CapabilityResult


class CapabilityManagerInterface(ABC):
    """Manager interface for capability lifecycle and orchestration."""

    @abstractmethod
    def register_capability(self, metadata: CapabilityMetadata) -> None:
        ...

    @abstractmethod
    def unregister_capability(self, capability_name: str) -> None:
        ...

    @abstractmethod
    def get_capability(self, capability_name: str) -> CapabilityMetadata:
        ...

    @abstractmethod
    def list_capabilities(self) -> list[CapabilityMetadata]:
        ...


class CapabilityRegistryInterface(ABC):
    """Registry interface for capabilities."""

    @abstractmethod
    def register(self, metadata: CapabilityMetadata) -> None:
        ...

    @abstractmethod
    def unregister(self, capability_name: str) -> None:
        ...

    @abstractmethod
    def get(self, capability_name: str) -> CapabilityMetadata:
        ...

    @abstractmethod
    def list(self) -> list[CapabilityMetadata]:
        ...


class CapabilityResolver(ABC):
    """Interface for resolving capabilities to implementations."""

    @abstractmethod
    def resolve(self, request: CapabilityRequest) -> CapabilityMetadata:
        ...


class CapabilityDispatcher(ABC):
    """Interface for dispatching capability requests."""

    @abstractmethod
    def dispatch(self, request: CapabilityRequest, context: CapabilityContext) -> CapabilityResponse:
        ...


class CapabilityEventManager(ABC):
    """Interface for capability event management."""

    @abstractmethod
    def publish(self, event_name: str, payload: Dict[str, Any]) -> None:
        ...


class CapabilityRequestHandler(Protocol):
    """Protocol for handlers that process capability requests."""

    def handle(self, request: CapabilityRequest, context: CapabilityContext) -> CapabilityResponse:
        ...


class CapabilityResponseProvider(Protocol):
    """Protocol for constructing capability responses."""

    def provide(self, result: CapabilityResult) -> CapabilityResponse:
        ...
