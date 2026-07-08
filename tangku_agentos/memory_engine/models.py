#!/usr/bin/env python3
"""
Data models and types for the TangkuAgentOS Memory Engine.

This module defines all the data structures, enums, and configurations
used throughout the memory system.
"""

from __future__ import annotations

import hashlib
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from typing import Any, Dict, List, Optional, Union, Tuple


# =============================================================================
# Enums
# =============================================================================


class MemoryType(Enum):
    """
    Enumeration of supported memory types.
    
    Each memory type serves a different purpose in the AI system:
    - SHORT_TERM: Temporary memory for immediate context (e.g., current conversation)
    - LONG_TERM: Persistent memory for important information
    - WORKING: Active memory being processed
    - EPISODIC: Memory of specific events or experiences
    - SEMANTIC: Conceptual knowledge and meanings
    - PROCEDURAL: Knowledge of how to perform tasks
    - CONVERSATION: Memory of dialogue history
    - PROJECT: Memory specific to a project
    - USER: User-specific memory
    - AGENT: Memory specific to an AI agent
    - SHARED: Memory shared across multiple agents/users
    - VECTOR: Memory stored as vector embeddings
    """
    SHORT_TERM = auto()
    LONG_TERM = auto()
    WORKING = auto()
    EPISODIC = auto()
    SEMANTIC = auto()
    PROCEDURAL = auto()
    CONVERSATION = auto()
    PROJECT = auto()
    USER = auto()
    AGENT = auto()
    SHARED = auto()
    VECTOR = auto()


class MemoryBackendType(Enum):
    """
    Enumeration of supported storage backend types.
    """
    SQLITE = auto()
    POSTGRESQL = auto()
    REDIS = auto()
    CHROMADB = auto()
    FAISS = auto()
    LANCEDB = auto()
    QDRANT = auto()
    PINECONE = auto()
    WEAVIATE = auto()
    MILVUS = auto()
    CUSTOM = auto()


class MemoryEventType(Enum):
    """
    Enumeration of memory event types.
    """
    CREATED = auto()
    UPDATED = auto()
    DELETED = auto()
    RETRIEVED = auto()
    SEARCHED = auto()
    COMPRESSED = auto()
    OPTIMIZED = auto()
    BACKED_UP = auto()
    RESTORED = auto()
    SYNCHRONIZED = auto()
    ERROR = auto()


class MemoryCompressionMethod(Enum):
    """
    Enumeration of memory compression methods.
    """
    NONE = auto()
    TRUNCATION = auto()
    SUMMARIZATION = auto()
    EXTRACTION = auto()
    CLUSTERING = auto()
    QUANTIZATION = auto()


class MemoryRankingMethod(Enum):
    """
    Enumeration of memory ranking methods for search results.
    """
    COSINE = auto()
    DOT_PRODUCT = auto()
    EUCLIDEAN = auto()
    MANHATTAN = auto()
    HYBRID = auto()


class MemoryEncryptionMethod(Enum):
    """
    Enumeration of memory encryption methods.
    """
    NONE = auto()
    AES_256 = auto()
    CHACHA20 = auto()


# =============================================================================
# Configurations
# =============================================================================


@dataclass
class EmbeddingConfig:
    """
    Configuration for embedding generation.
    
    Attributes:
        model: Name of the embedding model to use
        dimension: Dimension of the embedding vectors
        provider: Provider of the embedding model (e.g., "openai", "local")
        api_key: API key for the embedding provider (if required)
        base_url: Base URL for the embedding API
        timeout: Timeout for embedding requests in seconds
        max_retries: Maximum number of retries for failed requests
        batch_size: Number of items to embed in a single batch
    """
    model: str = "text-embedding-ada-002"
    dimension: int = 1536
    provider: str = "openai"
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    timeout: float = 30.0
    max_retries: int = 3
    batch_size: int = 100


@dataclass
class SearchConfig:
    """
    Configuration for memory search operations.
    
    Attributes:
        method: Ranking method to use for similarity search
        top_k: Number of results to return
        threshold: Similarity threshold for results
        include_metadata: Whether to include metadata in results
        include_scores: Whether to include similarity scores in results
        filters: Optional filters to apply to the search
    """
    method: MemoryRankingMethod = MemoryRankingMethod.COSINE
    top_k: int = 10
    threshold: float = 0.0
    include_metadata: bool = True
    include_scores: bool = True
    filters: Optional[Dict[str, Any]] = None


@dataclass
class CompressionConfig:
    """
    Configuration for memory compression.
    
    Attributes:
        method: Compression method to use
        max_length: Maximum length for compressed memory
        summary_ratio: Ratio of original length for summaries
        extraction_fields: Fields to extract for compression
        cluster_threshold: Similarity threshold for clustering
        quantization_bits: Number of bits for quantization (if applicable)
    """
    method: MemoryCompressionMethod = MemoryCompressionMethod.NONE
    max_length: int = 1000
    summary_ratio: float = 0.25
    extraction_fields: List[str] = field(default_factory=list)
    cluster_threshold: float = 0.95
    quantization_bits: int = 8


@dataclass
class CacheConfig:
    """
    Configuration for memory caching.
    
    Attributes:
        enabled: Whether caching is enabled
        max_size: Maximum number of items in the cache
        ttl: Time-to-live for cache entries in seconds
        eviction_policy: Policy for evicting items from cache
        levels: Number of cache levels (L1, L2, etc.)
    """
    enabled: bool = True
    max_size: int = 1000
    ttl: float = 3600.0  # 1 hour
    eviction_policy: str = "LRU"
    levels: int = 2


@dataclass
class MemoryConfig:
    """
    Main configuration for the Memory Engine.
    
    Attributes:
        name: Name of the memory configuration
        memory_types: List of enabled memory types
        default_type: Default memory type for new memories
        embedding: Embedding configuration
        search: Search configuration
        compression: Compression configuration
        cache: Cache configuration
        backend: Default storage backend type
        vector_db: Default vector database backend type
        encryption: Encryption configuration
        max_memory_size: Maximum size for individual memories
        max_total_memory: Maximum total memory storage
        ttl: Default time-to-live for memories in seconds (None = no expiration)
        versioning: Whether to enable memory versioning
        snapshots: Whether to enable memory snapshots
        backup_interval: Interval for automatic backups in seconds
        sync_interval: Interval for synchronization in seconds
    """
    name: str = "default"
    memory_types: List[MemoryType] = field(
        default_factory=lambda: [
            MemoryType.SHORT_TERM,
            MemoryType.LONG_TERM,
            MemoryType.WORKING,
            MemoryType.SEMANTIC,
        ]
    )
    default_type: MemoryType = MemoryType.WORKING
    embedding: EmbeddingConfig = field(default_factory=EmbeddingConfig)
    search: SearchConfig = field(default_factory=SearchConfig)
    compression: CompressionConfig = field(default_factory=CompressionConfig)
    cache: CacheConfig = field(default_factory=CacheConfig)
    backend: MemoryBackendType = MemoryBackendType.SQLITE
    vector_db: MemoryBackendType = MemoryBackendType.FAISS
    encryption: MemoryEncryptionMethod = MemoryEncryptionMethod.NONE
    max_memory_size: int = 1000000  # 1MB
    max_total_memory: int = 10000000000  # 10GB
    ttl: Optional[float] = None
    versioning: bool = True
    snapshots: bool = True
    backup_interval: float = 86400.0  # 24 hours
    sync_interval: float = 300.0  # 5 minutes


# =============================================================================
# Core Data Models
# =============================================================================


@dataclass
class MemoryMetadata:
    """
    Metadata associated with a memory.
    
    Attributes:
        memory_id: Unique identifier for the memory
        memory_type: Type of the memory
        created_at: Timestamp when the memory was created
        updated_at: Timestamp when the memory was last updated
        expires_at: Timestamp when the memory expires (None = no expiration)
        tags: List of tags associated with the memory
        source: Source of the memory (e.g., "user", "agent", "api")
        author: Author of the memory
        importance: Importance score (0.0 to 1.0)
        confidence: Confidence score (0.0 to 1.0)
        version: Version number of the memory
        parent_id: ID of parent memory (for versioning)
        references: List of referenced memory IDs
        permissions: Access permissions for the memory
        custom: Custom metadata fields
    """
    memory_id: str
    memory_type: MemoryType
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    expires_at: Optional[datetime] = None
    tags: List[str] = field(default_factory=list)
    source: str = "unknown"
    author: str = "system"
    importance: float = 0.5
    confidence: float = 0.5
    version: int = 1
    parent_id: Optional[str] = None
    references: List[str] = field(default_factory=list)
    permissions: Dict[str, Any] = field(default_factory=dict)
    custom: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert metadata to a dictionary."""
        return {
            "memory_id": self.memory_id,
            "memory_type": self.memory_type.name,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "tags": self.tags,
            "source": self.source,
            "author": self.author,
            "importance": self.importance,
            "confidence": self.confidence,
            "version": self.version,
            "parent_id": self.parent_id,
            "references": self.references,
            "permissions": self.permissions,
            "custom": self.custom,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MemoryMetadata":
        """Create metadata from a dictionary."""
        return cls(
            memory_id=data.get("memory_id", str(uuid.uuid4())),
            memory_type=MemoryType[data.get("memory_type", "WORKING")],
            created_at=datetime.fromisoformat(data["created_at"]) if "created_at" in data else datetime.now(),
            updated_at=datetime.fromisoformat(data["updated_at"]) if "updated_at" in data else datetime.now(),
            expires_at=datetime.fromisoformat(data["expires_at"]) if data.get("expires_at") else None,
            tags=data.get("tags", []),
            source=data.get("source", "unknown"),
            author=data.get("author", "system"),
            importance=data.get("importance", 0.5),
            confidence=data.get("confidence", 0.5),
            version=data.get("version", 1),
            parent_id=data.get("parent_id"),
            references=data.get("references", []),
            permissions=data.get("permissions", {}),
            custom=data.get("custom", {}),
        )


@dataclass
class Memory:
    """
    Main memory data structure.
    
    Attributes:
        content: The actual content of the memory
        metadata: Metadata associated with the memory
        embedding: Vector embedding of the content (if available)
        raw: Raw data associated with the memory (e.g., original input)
    """
    content: str
    metadata: MemoryMetadata
    embedding: Optional[List[float]] = None
    raw: Optional[Dict[str, Any]] = None

    def __post_init__(self):
        """Initialize the memory with default metadata if not provided."""
        if not hasattr(self.metadata, 'memory_id'):
            self.metadata.memory_id = str(uuid.uuid4())
        if not hasattr(self.metadata, 'created_at'):
            self.metadata.created_at = datetime.now()
        if not hasattr(self.metadata, 'updated_at'):
            self.metadata.updated_at = datetime.now()

    @property
    def memory_id(self) -> str:
        """Get the memory ID."""
        return self.metadata.memory_id

    @property
    def memory_type(self) -> MemoryType:
        """Get the memory type."""
        return self.metadata.memory_type

    def to_dict(self) -> Dict[str, Any]:
        """Convert memory to a dictionary."""
        return {
            "content": self.content,
            "metadata": self.metadata.to_dict(),
            "embedding": self.embedding,
            "raw": self.raw,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Memory":
        """Create memory from a dictionary."""
        metadata = MemoryMetadata.from_dict(data.get("metadata", {}))
        return cls(
            content=data.get("content", ""),
            metadata=metadata,
            embedding=data.get("embedding"),
            raw=data.get("raw"),
        )

    def generate_id(self) -> str:
        """Generate a deterministic ID based on content."""
        content_hash = hashlib.sha256(self.content.encode()).hexdigest()[:16]
        return f"{self.metadata.memory_type.name.lower()}_{content_hash}"


@dataclass
class MemoryVersion:
    """
    Version information for a memory.
    
    Attributes:
        memory_id: ID of the memory
        version: Version number
        content: Content at this version
        metadata: Metadata at this version
        created_at: Timestamp when this version was created
        changes: Description of changes from previous version
    """
    memory_id: str
    version: int
    content: str
    metadata: MemoryMetadata
    created_at: datetime = field(default_factory=datetime.now)
    changes: str = ""


@dataclass
class MemorySnapshot:
    """
    Snapshot of the memory system at a point in time.
    
    Attributes:
        snapshot_id: Unique identifier for the snapshot
        name: Human-readable name for the snapshot
        created_at: Timestamp when the snapshot was created
        memory_ids: List of memory IDs included in the snapshot
        metadata: Additional metadata about the snapshot
    """
    snapshot_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    created_at: datetime = field(default_factory=datetime.now)
    memory_ids: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class MemoryBackup:
    """
    Backup of memory data.
    
    Attributes:
        backup_id: Unique identifier for the backup
        name: Human-readable name for the backup
        created_at: Timestamp when the backup was created
        path: Path to the backup file
        size: Size of the backup in bytes
        memory_count: Number of memories in the backup
        metadata: Additional metadata about the backup
    """
    backup_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    created_at: datetime = field(default_factory=datetime.now)
    path: str = ""
    size: int = 0
    memory_count: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class MemoryStats:
    """
    Statistics about memory usage.
    
    Attributes:
        total_memories: Total number of memories
        by_type: Count of memories by type
        total_size: Total size of all memories in bytes
        by_backend: Statistics by storage backend
        cache_hits: Number of cache hits
        cache_misses: Number of cache misses
        avg_retrieval_time: Average time for memory retrieval in seconds
        last_backup: Timestamp of last backup
        last_sync: Timestamp of last synchronization
    """
    total_memories: int = 0
    by_type: Dict[MemoryType, int] = field(default_factory=dict)
    total_size: int = 0
    by_backend: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    cache_hits: int = 0
    cache_misses: int = 0
    avg_retrieval_time: float = 0.0
    last_backup: Optional[datetime] = None
    last_sync: Optional[datetime] = None


# =============================================================================
# Query and Filter Models
# =============================================================================


@dataclass
class MemoryFilter:
    """
    Filter criteria for memory search.
    
    Attributes:
        memory_type: Filter by memory type
        tags: Filter by tags (AND logic)
        source: Filter by source
        author: Filter by author
        created_after: Filter by creation time (after)
        created_before: Filter by creation time (before)
        updated_after: Filter by update time (after)
        updated_before: Filter by update time (before)
        expires_after: Filter by expiration time (after)
        expires_before: Filter by expiration time (before)
        min_importance: Minimum importance score
        max_importance: Maximum importance score
        min_confidence: Minimum confidence score
        max_confidence: Maximum confidence score
        custom: Custom filter criteria
    """
    memory_type: Optional[MemoryType] = None
    tags: Optional[List[str]] = None
    source: Optional[str] = None
    author: Optional[str] = None
    created_after: Optional[datetime] = None
    created_before: Optional[datetime] = None
    updated_after: Optional[datetime] = None
    updated_before: Optional[datetime] = None
    expires_after: Optional[datetime] = None
    expires_before: Optional[datetime] = None
    min_importance: Optional[float] = None
    max_importance: Optional[float] = None
    min_confidence: Optional[float] = None
    max_confidence: Optional[float] = None
    custom: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert filter to a dictionary."""
        return {
            "memory_type": self.memory_type.name if self.memory_type else None,
            "tags": self.tags,
            "source": self.source,
            "author": self.author,
            "created_after": self.created_after.isoformat() if self.created_after else None,
            "created_before": self.created_before.isoformat() if self.created_before else None,
            "updated_after": self.updated_after.isoformat() if self.updated_after else None,
            "updated_before": self.updated_before.isoformat() if self.updated_before else None,
            "expires_after": self.expires_after.isoformat() if self.expires_after else None,
            "expires_before": self.expires_before.isoformat() if self.expires_before else None,
            "min_importance": self.min_importance,
            "max_importance": self.max_importance,
            "min_confidence": self.min_confidence,
            "max_confidence": self.max_confidence,
            "custom": self.custom,
        }


@dataclass
class MemoryQuery:
    """
    Query for memory search.
    
    Attributes:
        query: The search query (text or embedding)
        query_embedding: Pre-computed embedding for the query
        filters: Filter criteria
        search_config: Search configuration
        limit: Maximum number of results to return
        offset: Offset for pagination
        include_content: Whether to include full content in results
        include_embeddings: Whether to include embeddings in results
    """
    query: str = ""
    query_embedding: Optional[List[float]] = None
    filters: Optional[MemoryFilter] = None
    search_config: Optional[SearchConfig] = None
    limit: int = 10
    offset: int = 0
    include_content: bool = True
    include_embeddings: bool = False


@dataclass
class MemorySearchResult:
    """
    Result of a memory search operation.
    
    Attributes:
        memory: The matching memory
        score: Similarity score (0.0 to 1.0)
        rank: Rank of the result
        metadata: Additional metadata about the match
    """
    memory: Memory
    score: float = 0.0
    rank: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)


# =============================================================================
# Base Configuration
# =============================================================================


@dataclass
class BaseMemoryConfig:
    """
    Base configuration class for memory components.
    
    Attributes:
        name: Name of the configuration
        enabled: Whether the component is enabled
        config: Additional configuration parameters
    """
    name: str = ""
    enabled: bool = True
    config: Dict[str, Any] = field(default_factory=dict)
