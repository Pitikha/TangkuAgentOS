"""Memory Engine module for TangkuAgentOS.

This module provides the core functionality for managing memory, including
storage, retrieval, indexing, and vector databases for semantic search.
"""

from .backend import MemoryBackend
from .cache import MemoryCache
from .compressor import MemoryCompressor
from .configuration import MemoryConfiguration
from .context import MemoryContext
from .coordinator import MemoryCoordinator
from .events import MemoryEvent
from .exceptions import (
    MemoryError,
    MemoryBackendError,
    MemoryIndexError,
    MemoryQueryError,
    MemoryRetrievalError,
    MemoryStorageError,
    MemoryVersionError,
)
from .intelligence import MemoryIntelligence
from .interfaces import (
    MemoryInterface,
    MemoryProvider,
    MemoryReader,
    MemoryWriter,
    MemoryIndexer,
    MemorySearcher,
)
from .manager import MemoryManager
from .metadata import MemoryMetadata
from .models import (
    Memory,
    MemoryBlock,
    MemoryChunk,
    MemoryCollection,
    MemoryEntry,
    MemoryIndex,
    MemoryQuery,
    MemoryResult,
    MemorySpan,
)
from .optimizer import MemoryOptimizer
from .provider import MemoryProviderBase
from .registry import MemoryRegistry
from .repository import MemoryRepository
from .resolver import MemoryResolver
from .router import MemoryRouter
from .serializer import MemorySerializer
from .statistics import MemoryStatistics
from .store import MemoryStore
from .vector_db import VectorDB
from .version_manager import MemoryVersionManager

__all__ = [
    "MemoryBackend",
    "MemoryCache",
    "MemoryCompressor",
    "MemoryConfiguration",
    "MemoryContext",
    "MemoryCoordinator",
    "MemoryEvent",
    "MemoryError",
    "MemoryBackendError",
    "MemoryIndexError",
    "MemoryQueryError",
    "MemoryRetrievalError",
    "MemoryStorageError",
    "MemoryVersionError",
    "MemoryIntelligence",
    "MemoryInterface",
    "MemoryProvider",
    "MemoryReader",
    "MemoryWriter",
    "MemoryIndexer",
    "MemorySearcher",
    "MemoryManager",
    "MemoryMetadata",
    "Memory",
    "MemoryBlock",
    "MemoryChunk",
    "MemoryCollection",
    "MemoryEntry",
    "MemoryIndex",
    "MemoryQuery",
    "MemoryResult",
    "MemorySpan",
    "MemoryOptimizer",
    "MemoryProviderBase",
    "MemoryRegistry",
    "MemoryRepository",
    "MemoryResolver",
    "MemoryRouter",
    "MemorySerializer",
    "MemoryStatistics",
    "MemoryStore",
    "VectorDB",
    "MemoryVersionManager",
]