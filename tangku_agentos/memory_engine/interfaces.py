from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Protocol

from .models import (
    MemoryAction,
    MemoryCollection,
    MemoryConfiguration,
    MemoryEntry,
    MemoryMetadata,
    MemoryRecord,
    MemoryReference,
    MemorySnapshot,
    MemoryState,
    MemoryType,
)


class MemoryRegistryInterface(ABC):
    """Interface for memory registry operations."""

    @abstractmethod
    def register(self, namespace: str, configuration: MemoryConfiguration) -> None:
        ...

    @abstractmethod
    def resolve(self, namespace: str) -> MemoryConfiguration:
        ...

    @abstractmethod
    def list_namespaces(self) -> list[str]:
        ...


class MemoryManagerInterface(ABC):
    """Interface for memory lifecycle management."""

    @abstractmethod
    def create_record(self, record: MemoryRecord) -> None:
        ...

    @abstractmethod
    def read_record(self, record_id: str) -> MemoryRecord:
        ...

    @abstractmethod
    def update_record(self, record: MemoryRecord) -> None:
        ...

    @abstractmethod
    def delete_record(self, record_id: str) -> None:
        ...

    @abstractmethod
    def archive_record(self, record_id: str) -> None:
        ...

    @abstractmethod
    def restore_record(self, record_id: str) -> None:
        ...

    @abstractmethod
    def snapshot_record(self, record_id: str) -> MemorySnapshot:
        ...


class MemoryProvider(ABC):
    """Interface for memory providers."""

    @abstractmethod
    def load(self, namespace: str) -> MemoryCollection:
        ...

    @abstractmethod
    def persist(self, collection: MemoryCollection) -> None:
        ...


class MemoryBackend(ABC):
    """Abstract memory backend definition."""

    @abstractmethod
    def connect(self) -> None:
        ...

    @abstractmethod
    def disconnect(self) -> None:
        ...


class MemoryStore(ABC):
    """Abstract store for memory records."""

    @abstractmethod
    def save(self, record: MemoryRecord) -> None:
        ...

    @abstractmethod
    def retrieve(self, record_id: str) -> MemoryRecord:
        ...


class MemoryCache(ABC):
    """Abstract cache for memory records."""

    @abstractmethod
    def get(self, record_id: str) -> MemoryRecord | None:
        ...

    @abstractmethod
    def put(self, record: MemoryRecord) -> None:
        ...


class MemoryRepository(ABC):
    """Abstract memory repository."""

    @abstractmethod
    def retrieve_collection(self, namespace: str) -> MemoryCollection:
        ...

    @abstractmethod
    def persist_collection(self, collection: MemoryCollection) -> None:
        ...


class MemoryResolver(ABC):
    """Interface for resolving memory references."""

    @abstractmethod
    def resolve(self, reference_id: str) -> MemoryReference:
        ...


class MemoryCoordinator(ABC):
    """Interface for memory coordination across providers."""

    @abstractmethod
    def coordinate(self, collection: MemoryCollection) -> None:
        ...


class MemoryRouter(ABC):
    """Interface for routing memory requests."""

    @abstractmethod
    def route(self, entry: MemoryEntry) -> str:
        ...


class MemorySerializer(ABC):
    """Interface for memory serialization."""

    @abstractmethod
    def serialize(self, record: MemoryRecord) -> str:
        ...

    @abstractmethod
    def deserialize(self, payload: str) -> MemoryRecord:
        ...


class MemoryCompressor(ABC):
    """Interface for memory compression."""

    @abstractmethod
    def compress(self, record: MemoryRecord) -> MemoryRecord:
        ...


class MemoryOptimizer(ABC):
    """Interface for memory optimization."""

    @abstractmethod
    def optimize(self, collection: MemoryCollection) -> MemoryCollection:
        ...


class MemoryVersionManager(ABC):
    """Interface for memory version management."""

    @abstractmethod
    def create_version(self, record: MemoryRecord) -> MemorySnapshot:
        ...


class MemoryMetadataManager(ABC):
    """Interface for memory metadata management."""

    @abstractmethod
    def update_metadata(self, record_id: str, metadata: MemoryMetadata) -> None:
        ...


class MemoryStatisticsManager(ABC):
    """Interface for memory statistics collection."""

    @abstractmethod
    def statistics(self) -> MemoryStatistics:
        ...


class MemoryConfigurationManager(ABC):
    """Interface for memory configuration management."""

    @abstractmethod
    def get_configuration(self, namespace: str) -> MemoryConfiguration:
        ...

    @abstractmethod
    def set_configuration(self, namespace: str, configuration: MemoryConfiguration) -> None:
        ...
