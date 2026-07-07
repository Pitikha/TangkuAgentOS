from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Protocol

from .models import (
    KnowledgeChunk,
    KnowledgeCollection,
    KnowledgeConfiguration,
    KnowledgeDocument,
    KnowledgeGraphEdge,
    KnowledgeGraphNode,
    KnowledgeItem,
    KnowledgeMetadata,
    KnowledgeNamespace,
    KnowledgeRelationship,
    KnowledgeSnapshot,
    KnowledgeSource,
)


class KnowledgeRegistryInterface(ABC):
    """Interface for knowledge registry operations."""

    @abstractmethod
    def register(self, namespace: str, configuration: KnowledgeConfiguration) -> None:
        ...

    @abstractmethod
    def resolve(self, namespace: str) -> KnowledgeConfiguration:
        ...

    @abstractmethod
    def list_namespaces(self) -> list[str]:
        ...


class KnowledgeManagerInterface(ABC):
    """Interface for managing knowledge assets."""

    @abstractmethod
    def register_document(self, document: KnowledgeDocument) -> None:
        ...

    @abstractmethod
    def get_document(self, document_id: str) -> KnowledgeDocument:
        ...

    @abstractmethod
    def list_documents(self) -> list[KnowledgeDocument]:
        ...


class KnowledgeProvider(ABC):
    """Interface for knowledge providers."""

    @abstractmethod
    def ingest(self, source: KnowledgeSource) -> KnowledgeDocument:
        ...


class KnowledgeSourceManagerInterface(ABC):
    """Interface for managing knowledge sources."""

    @abstractmethod
    def register_source(self, source: KnowledgeSource) -> None:
        ...

    @abstractmethod
    def get_source(self, source_id: str) -> KnowledgeSource:
        ...

    @abstractmethod
    def list_sources(self) -> list[KnowledgeSource]:
        ...


class GraphManagerInterface(ABC):
    """Interface for knowledge graph management."""

    @abstractmethod
    def register_node(self, node: KnowledgeGraphNode) -> None:
        ...

    @abstractmethod
    def register_edge(self, edge: KnowledgeGraphEdge) -> None:
        ...


class KnowledgeRetrievalManagerInterface(ABC):
    """Interface for retrieval workflows."""

    @abstractmethod
    def retrieve(self, query: str) -> KnowledgeCollection:
        ...


class KnowledgeSearchManagerInterface(ABC):
    """Interface for search operations."""

    @abstractmethod
    def search(self, query: str) -> KnowledgeCollection:
        ...


class CitationManagerInterface(ABC):
    """Interface for assignment of citations."""

    @abstractmethod
    def cite(self, item: KnowledgeItem, source: KnowledgeSource) -> None:
        ...


class KnowledgeCacheInterface(ABC):
    """Interface for knowledge caching."""

    @abstractmethod
    def get(self, key: str) -> KnowledgeDocument | None:
        ...

    @abstractmethod
    def put(self, document: KnowledgeDocument) -> None:
        ...


class KnowledgeStatisticsManagerInterface(ABC):
    """Interface for collecting statistics."""

    @abstractmethod
    def statistics(self) -> dict[str, int]:
        ...


class KnowledgeConfigurationManagerInterface(ABC):
    """Interface for configuration management."""

    @abstractmethod
    def get_configuration(self, namespace: str) -> KnowledgeConfiguration:
        ...

    @abstractmethod
    def set_configuration(self, namespace: str, configuration: KnowledgeConfiguration) -> None:
        ...


class KnowledgeResolverInterface(Protocol):
    """Protocol for resolving knowledge references."""

    def resolve(self, identifier: str) -> KnowledgeDocument:
        ...


class KnowledgeEventManagerInterface(ABC):
    """Interface for publishing knowledge events."""

    @abstractmethod
    def publish(self, event_name: str, payload: dict[str, str]) -> None:
        ...
