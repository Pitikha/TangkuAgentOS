from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Mapping, Protocol

from .models import ContextConfiguration, ContextObject, ContextMetadata


class ContextManagerInterface(ABC):
    """Interface for context management operations."""

    @abstractmethod
    def create_context(self, context: ContextObject) -> None:
        ...

    @abstractmethod
    def get_context(self, context_id: str) -> ContextObject:
        ...

    @abstractmethod
    def update_context(self, context: ContextObject) -> None:
        ...

    @abstractmethod
    def delete_context(self, context_id: str) -> None:
        ...


class ContextRegistryInterface(ABC):
    """Interface for context registry storage."""

    @abstractmethod
    def register(self, context: ContextObject) -> None:
        ...

    @abstractmethod
    def unregister(self, context_id: str) -> None:
        ...

    @abstractmethod
    def get(self, context_id: str) -> ContextObject:
        ...

    @abstractmethod
    def list(self) -> list[ContextObject]:
        ...


class ContextProviderInterface(Protocol):
    """Protocol for providing context objects."""

    def provide(self, context_id: str) -> ContextObject:
        ...


class ContextBuilderInterface(ABC):
    """Interface for building contexts."""

    @abstractmethod
    def build(self, metadata: ContextMetadata) -> ContextObject:
        ...


class ContextCacheInterface(ABC):
    """Interface for context caching."""

    @abstractmethod
    def store(self, context: ContextObject) -> None:
        ...

    @abstractmethod
    def retrieve(self, context_id: str) -> ContextObject | None:
        ...


class ContextCompressorInterface(ABC):
    """Interface for context compression."""

    @abstractmethod
    def compress(self, context: ContextObject) -> ContextObject:
        ...


class ContextOptimizerInterface(ABC):
    """Interface for context optimization."""

    @abstractmethod
    def optimize(self, context: ContextObject) -> ContextObject:
        ...


class ContextResolverInterface(ABC):
    """Interface for resolving context references."""

    @abstractmethod
    def resolve(self, reference_id: str) -> ContextObject:
        ...


class ContextSnapshotManagerInterface(ABC):
    """Interface for context snapshot management."""

    @abstractmethod
    def snapshot(self, context: ContextObject) -> None:
        ...

    @abstractmethod
    def get_snapshot(self, context_id: str) -> ContextObject:
        ...
