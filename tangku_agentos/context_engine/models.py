#!/usr/bin/env python3
"""
Data models and types for the TangkuAgentOS Context Engine.

This module defines all the data structures, enums, and configurations
used throughout the context system.
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


class ContextType(Enum):
    """
    Enumeration of context types.
    
    Each context type serves a different purpose in the AI system:
    - CONVERSATION: Context from conversation history
    - AGENT: Context specific to an AI agent
    - WORKFLOW: Context for workflow execution
    - WORKSPACE: Context for a workspace or project
    - MEMORY: Context from the memory system
    - KNOWLEDGE: Context from the knowledge base
    - DOCUMENT: Context from documents
    - TASK: Context for a specific task
    - TOOL: Context for tool usage
    - USER: Context specific to a user
    - SYSTEM: System-level context
    - CUSTOM: Custom context type
    """
    CONVERSATION = auto()
    AGENT = auto()
    WORKFLOW = auto()
    WORKSPACE = auto()
    MEMORY = auto()
    KNOWLEDGE = auto()
    DOCUMENT = auto()
    TASK = auto()
    TOOL = auto()
    USER = auto()
    SYSTEM = auto()
    CUSTOM = auto()


class ContextSource(Enum):
    """
    Enumeration of context sources.
    
    Each source represents where the context originates from:
    - MEMORY_ENGINE: Context from the Memory Engine
    - KNOWLEDGE_ENGINE: Context from the Knowledge Engine
    - PROJECT_INTELLIGENCE: Context from Project Intelligence
    - REPOSITORY_INTELLIGENCE: Context from Repository Intelligence
    - USER_PROFILE: Context from user profile
    - SESSION_HISTORY: Context from session history
    - WORKFLOW_RUNTIME: Context from Workflow Engine
    - AGENT_RUNTIME: Context from Agent Runtime
    - PLUGIN_RUNTIME: Context from Plugin Runtime
    - PROVIDER_RUNTIME: Context from Provider Runtime
    - EXTERNAL: Context from external providers
    - CUSTOM: Custom context source
    """
    MEMORY_ENGINE = auto()
    KNOWLEDGE_ENGINE = auto()
    PROJECT_INTELLIGENCE = auto()
    REPOSITORY_INTELLIGENCE = auto()
    USER_PROFILE = auto()
    SESSION_HISTORY = auto()
    WORKFLOW_RUNTIME = auto()
    AGENT_RUNTIME = auto()
    PLUGIN_RUNTIME = auto()
    PROVIDER_RUNTIME = auto()
    EXTERNAL = auto()
    CUSTOM = auto()


class ContextPriority(Enum):
    """
    Enumeration of context priority levels.
    
    Priority levels determine the importance of context segments
    during assembly and optimization.
    """
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4


class ContextAssemblyMode(Enum):
    """
    Enumeration of context assembly modes.
    
    Different modes for assembling context from multiple sources:
    - SEQUENTIAL: Assemble sources one after another
    - PARALLEL: Assemble sources in parallel
    - MERGE: Merge context from all sources
    - PRIORITY: Assemble based on priority
    - CUSTOM: Custom assembly mode
    """
    SEQUENTIAL = auto()
    PARALLEL = auto()
    MERGE = auto()
    PRIORITY = auto()
    CUSTOM = auto()


class ContextOptimizationMode(Enum):
    """
    Enumeration of context optimization modes.
    
    Different modes for optimizing context:
    - NONE: No optimization
    - BASIC: Basic token budgeting
    - ADVANCED: Advanced compression and summarization
    - AGGRESSIVE: Aggressive optimization for maximum compression
    - CUSTOM: Custom optimization mode
    """
    NONE = auto()
    BASIC = auto()
    ADVANCED = auto()
    AGGRESSIVE = auto()
    CUSTOM = auto()


class ContextCompressionMethod(Enum):
    """
    Enumeration of context compression methods.
    
    Different methods for compressing context:
    - NONE: No compression
    - TRUNCATION: Simple truncation to fit budget
    - SUMMARIZATION: Summarize context to reduce size
    - EXTRACTION: Extract key information
    - SEMANTIC: Semantic compression preserving meaning
    - HIERARCHICAL: Hierarchical summarization
    - CUSTOM: Custom compression method
    """
    NONE = auto()
    TRUNCATION = auto()
    SUMMARIZATION = auto()
    EXTRACTION = auto()
    SEMANTIC = auto()
    HIERARCHICAL = auto()
    CUSTOM = auto()


class ContextCacheLevel(Enum):
    """
    Enumeration of cache levels.
    
    Different levels of caching for context:
    - L1: Fast, small, local cache
    - L2: Larger, shared cache
    - L3: Persistent, distributed cache
    """
    L1 = 1
    L2 = 2
    L3 = 3


class ContextEventType(Enum):
    """
    Enumeration of context event types.
    """
    ASSEMBLED = auto()
    OPTIMIZED = auto()
    COMPRESSED = auto()
    BUDGETED = auto()
    CACHED = auto()
    SESSION_CREATED = auto()
    SESSION_UPDATED = auto()
    SESSION_DELETED = auto()
    SNAPSHOT_CREATED = auto()
    SNAPSHOT_RESTORED = auto()
    ERROR = auto()


# =============================================================================
# Configurations
# =============================================================================


@dataclass
class AssemblyConfig:
    """
    Configuration for context assembly.
    
    Attributes:
        mode: Assembly mode (sequential, parallel, merge, priority)
        max_sources: Maximum number of sources to assemble from
        timeout: Timeout for assembly in seconds
        parallel_workers: Number of parallel workers for parallel assembly
        merge_strategy: Strategy for merging context from multiple sources
        deduplication: Whether to deduplicate context segments
        priority_threshold: Minimum priority for including segments
        max_retries: Maximum number of retries for failed assembly
    """
    mode: ContextAssemblyMode = ContextAssemblyMode.PARALLEL
    max_sources: int = 10
    timeout: float = 30.0
    parallel_workers: int = 4
    merge_strategy: str = "concatenate"
    deduplication: bool = True
    priority_threshold: ContextPriority = ContextPriority.LOW
    max_retries: int = 3


@dataclass
class OptimizationConfig:
    """
    Configuration for context optimization.
    
    Attributes:
        mode: Optimization mode (none, basic, advanced, aggressive)
        max_iterations: Maximum number of optimization iterations
        timeout: Timeout for optimization in seconds
        early_stopping: Whether to stop early if no improvement
        preserve_order: Whether to preserve the original order of segments
        max_segment_size: Maximum size for individual segments
    """
    mode: ContextOptimizationMode = ContextOptimizationMode.BASIC
    max_iterations: int = 10
    timeout: float = 30.0
    early_stopping: bool = True
    preserve_order: bool = False
    max_segment_size: int = 1024


@dataclass
class CompressionConfig:
    """
    Configuration for context compression.
    
    Attributes:
        method: Compression method to use
        max_length: Maximum length for compressed context
        summary_ratio: Ratio of original length for summaries
        extraction_fields: Fields to extract for compression
        semantic_threshold: Similarity threshold for semantic compression
        hierarchical_levels: Number of levels for hierarchical summarization
    """
    method: ContextCompressionMethod = ContextCompressionMethod.SEMANTIC
    max_length: int = 2048
    summary_ratio: float = 0.25
    extraction_fields: List[str] = field(default_factory=list)
    semantic_threshold: float = 0.9
    hierarchical_levels: int = 3


@dataclass
class BudgetConfig:
    """
    Configuration for token budgeting.
    
    Attributes:
        max_tokens: Maximum number of tokens allowed
        reserved_tokens: Number of tokens to reserve for system messages
        min_tokens: Minimum number of tokens to keep
        strict: Whether to strictly enforce the budget
        overflow_strategy: Strategy for handling overflow (trim, compress, error)
        warning_threshold: Percentage of budget at which to warn
    """
    max_tokens: int = 4096
    reserved_tokens: int = 256
    min_tokens: int = 512
    strict: bool = True
    overflow_strategy: str = "compress"
    warning_threshold: float = 0.8


@dataclass
class CacheConfig:
    """
    Configuration for context caching.
    
    Attributes:
        enabled: Whether caching is enabled
        levels: Number of cache levels to use
        l1_size: Size of L1 cache (number of entries)
        l2_size: Size of L2 cache (number of entries)
        l3_enabled: Whether L3 (persistent) cache is enabled
        l3_path: Path for L3 cache storage
        ttl: Time-to-live for cache entries in seconds
        eviction_policy: Policy for evicting items from cache
        warm_cache: Whether to warm the cache on startup
    """
    enabled: bool = True
    levels: int = 2
    l1_size: int = 100
    l2_size: int = 1000
    l3_enabled: bool = False
    l3_path: str = "./cache/context"
    ttl: float = 3600.0
    eviction_policy: str = "LRU"
    warm_cache: bool = False


@dataclass
class SessionConfig:
    """
    Configuration for context sessions.
    
    Attributes:
        max_sessions: Maximum number of concurrent sessions
        session_timeout: Timeout for inactive sessions in seconds
        max_contexts_per_session: Maximum number of contexts per session
        auto_cleanup: Whether to automatically clean up old sessions
        cleanup_interval: Interval for session cleanup in seconds
        shared_workspaces: Whether to enable shared workspaces
    """
    max_sessions: int = 100
    session_timeout: float = 3600.0
    max_contexts_per_session: int = 10
    auto_cleanup: bool = True
    cleanup_interval: float = 300.0
    shared_workspaces: bool = True


@dataclass
class ContextConfig:
    """
    Main configuration for the Context Engine.
    
    Attributes:
        name: Name of the context configuration
        assembly: Assembly configuration
        optimization: Optimization configuration
        compression: Compression configuration
        budget: Budget configuration
        cache: Cache configuration
        session: Session configuration
        max_context_size: Maximum size for individual contexts
        max_total_contexts: Maximum total number of contexts
        default_context_type: Default context type for new contexts
        enable_snapshots: Whether to enable context snapshots
        snapshot_interval: Interval for automatic snapshots in seconds
        enable_backup: Whether to enable context backups
        backup_interval: Interval for automatic backups in seconds
    """
    name: str = "default"
    assembly: AssemblyConfig = field(default_factory=AssemblyConfig)
    optimization: OptimizationConfig = field(default_factory=OptimizationConfig)
    compression: CompressionConfig = field(default_factory=CompressionConfig)
    budget: BudgetConfig = field(default_factory=BudgetConfig)
    cache: CacheConfig = field(default_factory=CacheConfig)
    session: SessionConfig = field(default_factory=SessionConfig)
    max_context_size: int = 10000
    max_total_contexts: int = 100000
    default_context_type: ContextType = ContextType.CONVERSATION
    enable_snapshots: bool = True
    snapshot_interval: float = 300.0
    enable_backup: bool = False
    backup_interval: float = 86400.0


# =============================================================================
# Core Data Models
# =============================================================================


@dataclass
class ContextMetadata:
    """
    Metadata associated with a context or context segment.
    
    Attributes:
        context_id: Unique identifier for the context
        segment_id: Unique identifier for the segment (if applicable)
        source: Source of the context
        timestamp: Timestamp when the context was created or updated
        priority: Priority level of the context
        author: Author of the context
        tags: List of tags associated with the context
        attributes: Additional attributes
        custom: Custom metadata fields
    """
    context_id: str = ""
    segment_id: str = ""
    source: ContextSource = ContextSource.MEMORY_ENGINE
    timestamp: datetime = field(default_factory=datetime.now)
    priority: ContextPriority = ContextPriority.MEDIUM
    author: str = "system"
    tags: List[str] = field(default_factory=list)
    attributes: Dict[str, Any] = field(default_factory=dict)
    custom: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert metadata to a dictionary."""
        return {
            "context_id": self.context_id,
            "segment_id": self.segment_id,
            "source": self.source.name,
            "timestamp": self.timestamp.isoformat(),
            "priority": self.priority.name,
            "author": self.author,
            "tags": self.tags,
            "attributes": self.attributes,
            "custom": self.custom,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ContextMetadata":
        """Create metadata from a dictionary."""
        return cls(
            context_id=data.get("context_id", ""),
            segment_id=data.get("segment_id", ""),
            source=ContextSource[data.get("source", "MEMORY_ENGINE")],
            timestamp=datetime.fromisoformat(data["timestamp"]) if "timestamp" in data else datetime.now(),
            priority=ContextPriority[data.get("priority", "MEDIUM")],
            author=data.get("author", "system"),
            tags=data.get("tags", []),
            attributes=data.get("attributes", {}),
            custom=data.get("custom", {}),
        )


@dataclass
class ContextSourceInfo:
    """
    Information about a context source.
    
    Attributes:
        source: The source type
        source_id: Unique identifier for the source
        query: Query used to retrieve context from the source
        parameters: Parameters used for retrieval
        timestamp: Timestamp when the context was retrieved
        metadata: Additional metadata about the source
    """
    source: ContextSource
    source_id: str = ""
    query: str = ""
    parameters: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ContextChunk:
    """
    A chunk of context content.
    
    Attributes:
        chunk_id: Unique identifier for the chunk
        content: The actual content of the chunk
        metadata: Metadata associated with the chunk
        token_count: Number of tokens in the chunk
        source_info: Information about the source of the chunk
    """
    chunk_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    content: str = ""
    metadata: ContextMetadata = field(default_factory=ContextMetadata)
    token_count: int = 0
    source_info: Optional[ContextSourceInfo] = None

    def __post_init__(self):
        """Initialize the chunk with default values."""
        if not self.metadata.context_id:
            self.metadata.context_id = self.chunk_id
        if not self.metadata.segment_id:
            self.metadata.segment_id = self.chunk_id

    def to_dict(self) -> Dict[str, Any]:
        """Convert chunk to a dictionary."""
        return {
            "chunk_id": self.chunk_id,
            "content": self.content,
            "metadata": self.metadata.to_dict(),
            "token_count": self.token_count,
            "source_info": self.source_info.to_dict() if self.source_info else None,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ContextChunk":
        """Create chunk from a dictionary."""
        source_info = None
        if "source_info" in data and data["source_info"]:
            source_info = ContextSourceInfo(**data["source_info"])
        
        return cls(
            chunk_id=data.get("chunk_id", str(uuid.uuid4())),
            content=data.get("content", ""),
            metadata=ContextMetadata.from_dict(data.get("metadata", {})),
            token_count=data.get("token_count", 0),
            source_info=source_info,
        )


@dataclass
class Context:
    """
    Main context data structure.
    
    A context is a collection of chunks that together provide the information
    needed for an AI operation. Contexts can be assembled from multiple sources,
    optimized for token budget, and cached for performance.
    
    Attributes:
        context_id: Unique identifier for the context
        chunks: List of context chunks
        metadata: Metadata associated with the context
        statistics: Statistics about the context
        configuration: Configuration used for this context
    """
    context_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    chunks: List[ContextChunk] = field(default_factory=list)
    metadata: ContextMetadata = field(default_factory=ContextMetadata)
    statistics: Optional[Dict[str, Any]] = None
    configuration: Optional[ContextConfig] = None

    def __post_init__(self):
        """Initialize the context with default values."""
        if not self.metadata.context_id:
            self.metadata.context_id = self.context_id
        if self.statistics is None:
            self.statistics = self._calculate_statistics()
        if self.configuration is None:
            self.configuration = ContextConfig()

    @property
    def token_count(self) -> int:
        """Get the total token count for this context."""
        return sum(chunk.token_count for chunk in self.chunks)

    @property
    def chunk_count(self) -> int:
        """Get the number of chunks in this context."""
        return len(self.chunks)

    @property
    def content(self) -> str:
        """Get the concatenated content of all chunks."""
        return "\n\n".join(chunk.content for chunk in self.chunks)

    def _calculate_statistics(self) -> Dict[str, Any]:
        """Calculate statistics for this context."""
        source_counts = {}
        for chunk in self.chunks:
            source = chunk.metadata.source
            source_counts[source] = source_counts.get(source, 0) + 1
        
        return {
            "token_count": self.token_count,
            "chunk_count": self.chunk_count,
            "source_counts": {k.name: v for k, v in source_counts.items()},
            "average_chunk_size": self.token_count / self.chunk_count if self.chunk_count > 0 else 0,
        }

    def to_dict(self) -> Dict[str, Any]:
        """Convert context to a dictionary."""
        return {
            "context_id": self.context_id,
            "chunks": [chunk.to_dict() for chunk in self.chunks],
            "metadata": self.metadata.to_dict(),
            "statistics": self.statistics,
            "configuration": self.configuration.to_dict() if self.configuration else None,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Context":
        """Create context from a dictionary."""
        chunks = [ContextChunk.from_dict(chunk_data) for chunk_data in data.get("chunks", [])]
        
        context = cls(
            context_id=data.get("context_id", str(uuid.uuid4())),
            chunks=chunks,
            metadata=ContextMetadata.from_dict(data.get("metadata", {})),
            statistics=data.get("statistics"),
        )
        
        if "configuration" in data and data["configuration"]:
            context.configuration = ContextConfig(**data["configuration"])
        
        return context

    def to_string(self, separator: str = "\n\n") -> str:
        """
        Convert the context to a string.
        
        Args:
            separator: Separator to use between chunks
            
        Returns:
            The context as a string
        """
        return separator.join(chunk.content for chunk in self.chunks)

    def add_chunk(self, chunk: ContextChunk) -> None:
        """
        Add a chunk to this context.
        
        Args:
            chunk: The chunk to add
        """
        self.chunks.append(chunk)
        self.statistics = self._calculate_statistics()

    def remove_chunk(self, chunk_id: str) -> bool:
        """
        Remove a chunk from this context.
        
        Args:
            chunk_id: The ID of the chunk to remove
            
        Returns:
            True if the chunk was removed, False otherwise
        """
        for i, chunk in enumerate(self.chunks):
            if chunk.chunk_id == chunk_id:
                del self.chunks[i]
                self.statistics = self._calculate_statistics()
                return True
        return False

    def clear(self) -> None:
        """Clear all chunks from this context."""
        self.chunks.clear()
        self.statistics = self._calculate_statistics()

    def sort_by_priority(self, descending: bool = True) -> None:
        """
        Sort chunks by priority.
        
        Args:
            descending: Whether to sort in descending order (highest first)
        """
        self.chunks.sort(
            key=lambda x: x.metadata.priority.value,
            reverse=descending,
        )

    def filter_by_priority(self, min_priority: ContextPriority) -> "Context":
        """
        Filter chunks by minimum priority.
        
        Args:
            min_priority: Minimum priority to include
            
        Returns:
            A new context with only the filtered chunks
        """
        filtered_chunks = [
            chunk for chunk in self.chunks
            if chunk.metadata.priority.value >= min_priority.value
        ]
        return Context(
            context_id=self.context_id,
            chunks=filtered_chunks,
            metadata=self.metadata,
        )

    def get_chunks_by_source(self, source: ContextSource) -> List[ContextChunk]:
        """
        Get all chunks from a specific source.
        
        Args:
            source: The source to filter by
            
        Returns:
            List of chunks from the specified source
        """
        return [
            chunk for chunk in self.chunks
            if chunk.metadata.source == source
        ]


# =============================================================================
# Result Models
# =============================================================================


@dataclass
class ContextAssemblyResult:
    """
    Result of a context assembly operation.
    
    Attributes:
        context: The assembled context
        chunks_added: Number of chunks added
        chunks_removed: Number of chunks removed (due to deduplication)
        sources_used: List of sources used for assembly
        assembly_time: Time taken for assembly in seconds
        metadata: Additional metadata about the assembly
    """
    context: Context
    chunks_added: int = 0
    chunks_removed: int = 0
    sources_used: List[ContextSource] = field(default_factory=list)
    assembly_time: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ContextOptimizationResult:
    """
    Result of a context optimization operation.
    
    Attributes:
        context: The optimized context
        original_token_count: Token count before optimization
        optimized_token_count: Token count after optimization
        chunks_removed: Number of chunks removed
        chunks_compressed: Number of chunks compressed
        optimization_time: Time taken for optimization in seconds
        metadata: Additional metadata about the optimization
    """
    context: Context
    original_token_count: int = 0
    optimized_token_count: int = 0
    chunks_removed: int = 0
    chunks_compressed: int = 0
    optimization_time: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ContextCompressionResult:
    """
    Result of a context compression operation.
    
    Attributes:
        context: The compressed context
        original_token_count: Token count before compression
        compressed_token_count: Token count after compression
        compression_ratio: Ratio of compressed to original size
        chunks_compressed: Number of chunks compressed
        compression_time: Time taken for compression in seconds
        metadata: Additional metadata about the compression
    """
    context: Context
    original_token_count: int = 0
    compressed_token_count: int = 0
    compression_ratio: float = 1.0
    chunks_compressed: int = 0
    compression_time: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ContextBudgetResult:
    """
    Result of a context budgeting operation.
    
    Attributes:
        context: The budgeted context
        original_token_count: Token count before budgeting
        budgeted_token_count: Token count after budgeting
        chunks_removed: Number of chunks removed
        chunks_trimmed: Number of chunks trimmed
        within_budget: Whether the context is within the token budget
        overflow: Number of tokens over the budget (if any)
        budget_time: Time taken for budgeting in seconds
        metadata: Additional metadata about the budgeting
    """
    context: Context
    original_token_count: int = 0
    budgeted_token_count: int = 0
    chunks_removed: int = 0
    chunks_trimmed: int = 0
    within_budget: bool = True
    overflow: int = 0
    budget_time: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ContextCacheResult:
    """
    Result of a context caching operation.
    
    Attributes:
        context: The cached context
        cache_hit: Whether the context was found in cache
        cache_level: Level of cache where the context was found
        cache_time: Time taken for cache operation in seconds
        metadata: Additional metadata about the caching
    """
    context: Optional[Context] = None
    cache_hit: bool = False
    cache_level: Optional[ContextCacheLevel] = None
    cache_time: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ContextSessionResult:
    """
    Result of a context session operation.
    
    Attributes:
        session_id: ID of the session
        context_ids: List of context IDs in the session
        success: Whether the operation was successful
        message: Additional message about the operation
        metadata: Additional metadata about the session
    """
    session_id: str = ""
    context_ids: List[str] = field(default_factory=list)
    success: bool = True
    message: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)


# =============================================================================
# Base Configuration
# =============================================================================


@dataclass
class BaseContextConfig:
    """
    Base configuration class for context components.
    
    Attributes:
        name: Name of the configuration
        enabled: Whether the component is enabled
        config: Additional configuration parameters
    """
    name: str = ""
    enabled: bool = True
    config: Dict[str, Any] = field(default_factory=dict)
