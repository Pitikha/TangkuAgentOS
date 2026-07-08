#!/usr/bin/env python3
"""
TangkuAgentOS Memory Engine.

This package provides a production-grade, enterprise-level memory system for AI agents,
supporting multiple memory types, storage backends, and intelligence features.

## Features
- Short-term, long-term, working, episodic, semantic, procedural, conversation, project, user, agent, and shared memory
- Multiple storage backends: SQLite, PostgreSQL, Redis, ChromaDB, FAISS, LanceDB, Qdrant, Pinecone, Weaviate, Milvus
- Memory compression, deduplication, versioning, snapshots, backup, restore, synchronization
- Context management with token budgeting, compression, prioritization, and scoring
- Intelligence features: importance scoring, relevance ranking, forgetting strategy, summarization, consolidation
- Performance optimizations: multi-level caching, batch retrieval, async operations, lazy loading
- Security: encryption, permissions, isolation, secure deletion, audit logging

## Usage
```python
from tangku_agentos.memory_engine import MemoryManager, MemoryStore, VectorDB

# Initialize the memory manager
memory_manager = MemoryManager()

# Create a memory store
memory_store = MemoryStore(backend="sqlite", db_path=":memory:")

# Register the store with the manager
memory_manager.register_store("default", memory_store)

# Add a memory
memory_id = await memory_manager.add_memory(
    content="Hello, world!",
    memory_type="working",
    metadata={"source": "user"},
)

# Retrieve a memory
memory = await memory_manager.get_memory(memory_id)
```
"""

# --- Core Components ---
from .manager import MemoryManager
from .store import MemoryStore, BaseMemoryStore
from .vector_db import VectorDB, BaseVectorDB
from .cache import MemoryCache, BaseMemoryCache
from .compressor import MemoryCompressor, BaseMemoryCompressor
from .optimizer import MemoryOptimizer, BaseMemoryOptimizer
from .intelligence import MemoryIntelligence, BaseMemoryIntelligence
from .coordinator import MemoryCoordinator
from .provider import MemoryProvider, BaseMemoryProvider
from .registry import MemoryRegistry

# --- Backends ---
from .backend import (
    BaseStorageBackend,
    SQLiteBackend,
    PostgreSQLBackend,
    RedisBackend,
)

# --- Vector DB Backends ---
from .vector_db import (
    FAISSBackend,
    ChromaDBBackend,
    QdrantBackend,
    PineconeBackend,
    WeaviateBackend,
    MilvusBackend,
    LanceDBBackend,
)

# --- Models and Types ---
from .models import (
    Memory,
    MemoryType,
    MemoryMetadata,
    MemorySearchResult,
    MemoryQuery,
    MemoryFilter,
    MemoryVersion,
    MemorySnapshot,
    MemoryBackup,
    MemoryStats,
    MemoryConfig,
    EmbeddingConfig,
    SearchConfig,
    CompressionConfig,
    CacheConfig,
)

# --- Context Management ---
from .context import MemoryContext, BaseMemoryContext

# --- Events ---
from .events import MemoryEvent, MemoryEventType, MemoryEventBus

# --- Configuration ---
from .configuration import MemoryConfigManager, BaseMemoryConfig

# --- Exceptions ---
from .exceptions import (
    MemoryError,
    MemoryNotFoundError,
    MemoryExistsError,
    MemoryBackendError,
    MemoryPermissionError,
    MemoryEncryptionError,
    MemoryValidationError,
    MemoryTimeoutError,
    MemoryConflictError,
)

# --- Interfaces ---
from .interfaces import (
    IMemoryStore,
    IMemoryBackend,
    IMemoryVectorDB,
    IMemoryCache,
    IMemoryCompressor,
    IMemoryOptimizer,
    IMemoryIntelligence,
    IMemoryProvider,
)

# --- Utilities ---
from .metadata import MemoryMetadataManager
from .resolver import MemoryResolver
from .router import MemoryRouter
from .serializer import MemorySerializer
from .statistics import MemoryStatistics
from .version_manager import MemoryVersionManager

# --- Public API ---
__all__ = [
    # Core Components
    "MemoryManager",
    "MemoryStore",
    "BaseMemoryStore",
    "VectorDB",
    "BaseVectorDB",
    "MemoryCache",
    "BaseMemoryCache",
    "MemoryCompressor",
    "BaseMemoryCompressor",
    "MemoryOptimizer",
    "BaseMemoryOptimizer",
    "MemoryIntelligence",
    "BaseMemoryIntelligence",
    "MemoryCoordinator",
    "MemoryProvider",
    "BaseMemoryProvider",
    "MemoryRegistry",
    # Backends
    "BaseStorageBackend",
    "SQLiteBackend",
    "PostgreSQLBackend",
    "RedisBackend",
    # Vector DB Backends
    "FAISSBackend",
    "ChromaDBBackend",
    "QdrantBackend",
    "PineconeBackend",
    "WeaviateBackend",
    "MilvusBackend",
    "LanceDBBackend",
    # Models and Types
    "Memory",
    "MemoryType",
    "MemoryMetadata",
    "MemorySearchResult",
    "MemoryQuery",
    "MemoryFilter",
    "MemoryVersion",
    "MemorySnapshot",
    "MemoryBackup",
    "MemoryStats",
    "MemoryConfig",
    "EmbeddingConfig",
    "SearchConfig",
    "CompressionConfig",
    "CacheConfig",
    # Context Management
    "MemoryContext",
    "BaseMemoryContext",
    # Events
    "MemoryEvent",
    "MemoryEventType",
    "MemoryEventBus",
    # Configuration
    "MemoryConfigManager",
    "BaseMemoryConfig",
    # Exceptions
    "MemoryError",
    "MemoryNotFoundError",
    "MemoryExistsError",
    "MemoryBackendError",
    "MemoryPermissionError",
    "MemoryEncryptionError",
    "MemoryValidationError",
    "MemoryTimeoutError",
    "MemoryConflictError",
    # Interfaces
    "IMemoryStore",
    "IMemoryBackend",
    "IMemoryVectorDB",
    "IMemoryCache",
    "IMemoryCompressor",
    "IMemoryOptimizer",
    "IMemoryIntelligence",
    "IMemoryProvider",
    # Utilities
    "MemoryMetadataManager",
    "MemoryResolver",
    "MemoryRouter",
    "MemorySerializer",
    "MemoryStatistics",
    "MemoryVersionManager",
]
