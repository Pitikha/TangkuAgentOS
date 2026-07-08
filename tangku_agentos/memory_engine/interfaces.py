#!/usr/bin/env python3
"""
Abstract interfaces for the TangkuAgentOS Memory Engine.

This module defines the abstract base classes (interfaces) that all memory
components must implement. These interfaces ensure consistency and allow
for dependency injection and easy swapping of implementations.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, TypeVar, Generic, Union, AsyncIterator
from datetime import datetime

from .models import (
    Memory,
    MemoryMetadata,
    MemoryType,
    MemoryQuery,
    MemorySearchResult,
    MemoryFilter,
    MemoryVersion,
    MemorySnapshot,
    MemoryBackup,
    MemoryStats,
    MemoryConfig,
)

# Type variables for generic interfaces
T = TypeVar("T")


# =============================================================================
# Memory Store Interface
# =============================================================================


class IMemoryStore(ABC):
    """
    Abstract interface for memory storage implementations.
    
    This interface defines the contract that all memory store implementations
    must follow. It provides methods for CRUD operations, search, and management
    of memories.
    
    Implementations should handle:
    - Storage of memory data
    - Retrieval by ID or query
    - Search operations
    - Memory lifecycle management
    - Error handling
    """
    
    @abstractmethod
    async def initialize(self, config: Optional[Dict[str, Any]] = None) -> None:
        """
        Initialize the memory store.
        
        Args:
            config: Configuration for the store
        """
        pass
    
    @abstractmethod
    async def shutdown(self) -> None:
        """Shutdown the memory store and clean up resources."""
        pass
    
    @abstractmethod
    async def add_memory(
        self,
        memory: Memory,
        overwrite: bool = False,
    ) -> str:
        """
        Add a new memory to the store.
        
        Args:
            memory: The memory to add
            overwrite: Whether to overwrite if the memory already exists
            
        Returns:
            The ID of the added memory
            
        Raises:
            MemoryExistsError: If the memory already exists and overwrite is False
        """
        pass
    
    @abstractmethod
    async def get_memory(self, memory_id: str) -> Optional[Memory]:
        """
        Retrieve a memory by its ID.
        
        Args:
            memory_id: The ID of the memory to retrieve
            
        Returns:
            The memory if found, None otherwise
            
        Raises:
            MemoryNotFoundError: If the memory does not exist
        """
        pass
    
    @abstractmethod
    async def get_memories(
        self,
        memory_ids: List[str],
    ) -> Dict[str, Optional[Memory]]:
        """
        Retrieve multiple memories by their IDs.
        
        Args:
            memory_ids: List of memory IDs to retrieve
            
        Returns:
            Dictionary mapping memory IDs to their corresponding memories
            (or None if not found)
        """
        pass
    
    @abstractmethod
    async def update_memory(
        self,
        memory_id: str,
        content: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        embedding: Optional[List[float]] = None,
    ) -> Memory:
        """
        Update an existing memory.
        
        Args:
            memory_id: The ID of the memory to update
            content: New content for the memory
            metadata: New metadata for the memory
            embedding: New embedding for the memory
            
        Returns:
            The updated memory
            
        Raises:
            MemoryNotFoundError: If the memory does not exist
        """
        pass
    
    @abstractmethod
    async def delete_memory(self, memory_id: str) -> bool:
        """
        Delete a memory from the store.
        
        Args:
            memory_id: The ID of the memory to delete
            
        Returns:
            True if the memory was deleted, False otherwise
            
        Raises:
            MemoryNotFoundError: If the memory does not exist
        """
        pass
    
    @abstractmethod
    async def delete_memories(self, memory_ids: List[str]) -> int:
        """
        Delete multiple memories from the store.
        
        Args:
            memory_ids: List of memory IDs to delete
            
        Returns:
            Number of memories deleted
        """
        pass
    
    @abstractmethod
    async def search_memories(
        self,
        query: Union[str, MemoryQuery],
    ) -> List[MemorySearchResult]:
        """
        Search for memories matching a query.
        
        Args:
            query: The search query (text or MemoryQuery object)
            
        Returns:
            List of search results with matching memories and scores
        """
        pass
    
    @abstractmethod
    async def list_memories(
        self,
        memory_type: Optional[MemoryType] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
        filters: Optional[MemoryFilter] = None,
    ) -> List[Memory]:
        """
        List memories with optional filtering.
        
        Args:
            memory_type: Filter by memory type
            limit: Maximum number of memories to return
            offset: Offset for pagination
            filters: Additional filters to apply
            
        Returns:
            List of matching memories
        """
        pass
    
    @abstractmethod
    async def count_memories(
        self,
        memory_type: Optional[MemoryType] = None,
        filters: Optional[MemoryFilter] = None,
    ) -> int:
        """
        Count memories matching the given criteria.
        
        Args:
            memory_type: Filter by memory type
            filters: Additional filters to apply
            
        Returns:
            Number of matching memories
        """
        pass
    
    @abstractmethod
    async def exists(self, memory_id: str) -> bool:
        """
        Check if a memory exists in the store.
        
        Args:
            memory_id: The ID of the memory to check
            
        Returns:
            True if the memory exists, False otherwise
        """
        pass
    
    @abstractmethod
    async def get_stats(self) -> MemoryStats:
        """
        Get statistics about the memory store.
        
        Returns:
            Statistics about the store
        """
        pass


# =============================================================================
# Memory Backend Interface
# =============================================================================


class IMemoryBackend(ABC):
    """
    Abstract interface for storage backends.
    
    This interface defines the contract for all storage backend implementations.
    Backends are responsible for the actual persistence of memory data.
    
    Implementations should handle:
    - Connection management
    - Data persistence
    - Query execution
    - Transaction support
    - Error handling
    """
    
    @abstractmethod
    async def connect(self, **kwargs: Any) -> None:
        """
        Establish a connection to the backend.
        
        Args:
            **kwargs: Connection parameters
        """
        pass
    
    @abstractmethod
    async def disconnect(self) -> None:
        """Close the connection to the backend."""
        pass
    
    @abstractmethod
    async def is_connected(self) -> bool:
        """
        Check if the backend is connected.
        
        Returns:
            True if connected, False otherwise
        """
        pass
    
    @abstractmethod
    async def create(self, data: Dict[str, Any]) -> str:
        """
        Create a new record in the backend.
        
        Args:
            data: The data to store
            
        Returns:
            The ID of the created record
        """
        pass
    
    @abstractmethod
    async def read(self, record_id: str) -> Optional[Dict[str, Any]]:
        """
        Read a record from the backend.
        
        Args:
            record_id: The ID of the record to read
            
        Returns:
            The record data if found, None otherwise
        """
        pass
    
    @abstractmethod
    async def update(self, record_id: str, data: Dict[str, Any]) -> bool:
        """
        Update a record in the backend.
        
        Args:
            record_id: The ID of the record to update
            data: The updated data
            
        Returns:
            True if the update was successful, False otherwise
        """
        pass
    
    @abstractmethod
    async def delete(self, record_id: str) -> bool:
        """
        Delete a record from the backend.
        
        Args:
            record_id: The ID of the record to delete
            
        Returns:
            True if the deletion was successful, False otherwise
        """
        pass
    
    @abstractmethod
    async def query(
        self,
        query: Dict[str, Any],
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Execute a query against the backend.
        
        Args:
            query: The query to execute
            limit: Maximum number of results to return
            offset: Offset for pagination
            
        Returns:
            List of matching records
        """
        pass
    
    @abstractmethod
    async def count(self, query: Optional[Dict[str, Any]] = None) -> int:
        """
        Count records matching a query.
        
        Args:
            query: Optional query to filter records
            
        Returns:
            Number of matching records
        """
        pass
    
    @abstractmethod
    async def begin_transaction(self) -> Any:
        """
        Begin a new transaction.
        
        Returns:
            A transaction object
        """
        pass
    
    @abstractmethod
    async def commit_transaction(self, transaction: Any) -> None:
        """
        Commit a transaction.
        
        Args:
            transaction: The transaction to commit
        """
        pass
    
    @abstractmethod
    async def rollback_transaction(self, transaction: Any) -> None:
        """
        Rollback a transaction.
        
        Args:
            transaction: The transaction to rollback
        """
        pass
    
    @abstractmethod
    async def backup(self, path: str) -> None:
        """
        Create a backup of the backend data.
        
        Args:
            path: Path to save the backup
        """
        pass
    
    @abstractmethod
    async def restore(self, path: str) -> None:
        """
        Restore data from a backup.
        
        Args:
            path: Path to the backup file
        """
        pass


# =============================================================================
# Vector Database Interface
# =============================================================================


class IMemoryVectorDB(ABC):
    """
    Abstract interface for vector database implementations.
    
    This interface defines the contract for all vector database backends.
    Vector databases are specialized for storing and querying vector embeddings.
    
    Implementations should handle:
    - Vector storage and retrieval
    - Similarity search
    - Index management
    - Dimensionality handling
    """
    
    @abstractmethod
    async def initialize(
        self,
        dimension: int,
        metric: str = "cosine",
        **kwargs: Any,
    ) -> None:
        """
        Initialize the vector database.
        
        Args:
            dimension: Dimension of the vectors
            metric: Similarity metric to use (cosine, dot_product, euclidean, etc.)
            **kwargs: Additional initialization parameters
        """
        pass
    
    @abstractmethod
    async def shutdown(self) -> None:
        """Shutdown the vector database and clean up resources."""
        pass
    
    @abstractmethod
    async def add_vector(
        self,
        vector_id: str,
        vector: List[float],
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Add a vector to the database.
        
        Args:
            vector_id: Unique identifier for the vector
            vector: The vector to add
            metadata: Optional metadata to associate with the vector
        """
        pass
    
    @abstractmethod
    async def add_vectors(
        self,
        vectors: Dict[str, List[float]],
        metadata: Optional[Dict[str, Dict[str, Any]]] = None,
    ) -> None:
        """
        Add multiple vectors to the database.
        
        Args:
            vectors: Dictionary mapping vector IDs to vectors
            metadata: Optional dictionary mapping vector IDs to their metadata
        """
        pass
    
    @abstractmethod
    async def get_vector(self, vector_id: str) -> Optional[Tuple[List[float], Dict[str, Any]]]:
        """
        Retrieve a vector and its metadata by ID.
        
        Args:
            vector_id: The ID of the vector to retrieve
            
        Returns:
            Tuple of (vector, metadata) if found, None otherwise
        """
        pass
    
    @abstractmethod
    async def get_vectors(
        self,
        vector_ids: List[str],
    ) -> Dict[str, Optional[Tuple[List[float], Dict[str, Any]]]]:
        """
        Retrieve multiple vectors and their metadata by IDs.
        
        Args:
            vector_ids: List of vector IDs to retrieve
            
        Returns:
            Dictionary mapping vector IDs to (vector, metadata) tuples
        """
        pass
    
    @abstractmethod
    async def update_vector(
        self,
        vector_id: str,
        vector: List[float],
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Update a vector in the database.
        
        Args:
            vector_id: The ID of the vector to update
            vector: The new vector
            metadata: Optional new metadata
        """
        pass
    
    @abstractmethod
    async def delete_vector(self, vector_id: str) -> bool:
        """
        Delete a vector from the database.
        
        Args:
            vector_id: The ID of the vector to delete
            
        Returns:
            True if the vector was deleted, False otherwise
        """
        pass
    
    @abstractmethod
    async def delete_vectors(self, vector_ids: List[str]) -> int:
        """
        Delete multiple vectors from the database.
        
        Args:
            vector_ids: List of vector IDs to delete
            
        Returns:
            Number of vectors deleted
        """
        pass
    
    @abstractmethod
    async def search(
        self,
        query_vector: List[float],
        top_k: int = 10,
        threshold: Optional[float] = None,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[Tuple[str, float, Dict[str, Any]]]:
        """
        Search for similar vectors.
        
        Args:
            query_vector: The query vector
            top_k: Number of results to return
            threshold: Optional similarity threshold
            filters: Optional filters to apply to the search
            
        Returns:
            List of tuples (vector_id, score, metadata)
        """
        pass
    
    @abstractmethod
    async def batch_search(
        self,
        query_vectors: List[List[float]],
        top_k: int = 10,
        threshold: Optional[float] = None,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[List[Tuple[str, float, Dict[str, Any]]]]:
        """
        Perform batch search for multiple query vectors.
        
        Args:
            query_vectors: List of query vectors
            top_k: Number of results to return for each query
            threshold: Optional similarity threshold
            filters: Optional filters to apply to all searches
            
        Returns:
            List of search results for each query vector
        """
        pass
    
    @abstractmethod
    async def clear(self) -> None:
        """Clear all vectors from the database."""
        pass
    
    @abstractmethod
    async def get_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the vector database.
        
        Returns:
            Dictionary with database statistics
        """
        pass


# =============================================================================
# Memory Cache Interface
# =============================================================================


class IMemoryCache(ABC):
    """
    Abstract interface for memory caching implementations.
    
    This interface defines the contract for all cache implementations.
    Caches are used to improve performance by storing frequently accessed memories.
    
    Implementations should handle:
    - Cache storage and retrieval
    - Expiration and eviction
    - Cache invalidation
    - Multi-level caching
    """
    
    @abstractmethod
    async def initialize(
        self,
        max_size: int = 1000,
        ttl: float = 3600.0,
        **kwargs: Any,
    ) -> None:
        """
        Initialize the cache.
        
        Args:
            max_size: Maximum number of items in the cache
            ttl: Time-to-live for cache entries in seconds
            **kwargs: Additional initialization parameters
        """
        pass
    
    @abstractmethod
    async def shutdown(self) -> None:
        """Shutdown the cache and clean up resources."""
        pass
    
    @abstractmethod
    async def get(self, key: str) -> Optional[Any]:
        """
        Get a value from the cache.
        
        Args:
            key: The cache key
            
        Returns:
            The cached value if found, None otherwise
        """
        pass
    
    @abstractmethod
    async def get_many(self, keys: List[str]) -> Dict[str, Optional[Any]]:
        """
        Get multiple values from the cache.
        
        Args:
            keys: List of cache keys
            
        Returns:
            Dictionary mapping keys to their cached values (or None if not found)
        """
        pass
    
    @abstractmethod
    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[float] = None,
    ) -> None:
        """
        Set a value in the cache.
        
        Args:
            key: The cache key
            value: The value to cache
            ttl: Optional time-to-live in seconds (overrides default)
        """
        pass
    
    @abstractmethod
    async def set_many(
        self,
        items: Dict[str, Any],
        ttl: Optional[float] = None,
    ) -> None:
        """
        Set multiple values in the cache.
        
        Args:
            items: Dictionary mapping keys to values
            ttl: Optional time-to-live in seconds (overrides default)
        """
        pass
    
    @abstractmethod
    async def delete(self, key: str) -> bool:
        """
        Delete a value from the cache.
        
        Args:
            key: The cache key
            
        Returns:
            True if the key was deleted, False otherwise
        """
        pass
    
    @abstractmethod
    async def delete_many(self, keys: List[str]) -> int:
        """
        Delete multiple values from the cache.
        
        Args:
            keys: List of cache keys to delete
            
        Returns:
            Number of keys deleted
        """
        pass
    
    @abstractmethod
    async def clear(self) -> None:
        """Clear all items from the cache."""
        pass
    
    @abstractmethod
    async def exists(self, key: str) -> bool:
        """
        Check if a key exists in the cache.
        
        Args:
            key: The cache key
            
        Returns:
            True if the key exists, False otherwise
        """
        pass
    
    @abstractmethod
    async def get_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the cache.
        
        Returns:
            Dictionary with cache statistics
        """
        pass


# =============================================================================
# Memory Compressor Interface
# =============================================================================


class IMemoryCompressor(ABC):
    """
    Abstract interface for memory compression implementations.
    
    This interface defines the contract for all compression implementations.
    Compressors are used to reduce memory size while preserving important information.
    
    Implementations should handle:
    - Compression of memory content
    - Decompression of compressed memories
    - Quality preservation
    - Performance optimization
    """
    
    @abstractmethod
    async def initialize(self, config: Optional[Dict[str, Any]] = None) -> None:
        """
        Initialize the compressor.
        
        Args:
            config: Configuration for the compressor
        """
        pass
    
    @abstractmethod
    async def shutdown(self) -> None:
        """Shutdown the compressor and clean up resources."""
        pass
    
    @abstractmethod
    async def compress(
        self,
        content: str,
        metadata: Optional[MemoryMetadata] = None,
        target_length: Optional[int] = None,
    ) -> str:
        """
        Compress memory content.
        
        Args:
            content: The content to compress
            metadata: Optional metadata to consider during compression
            target_length: Optional target length for the compressed content
            
        Returns:
            The compressed content
        """
        pass
    
    @abstractmethod
    async def decompress(self, compressed_content: str) -> str:
        """
        Decompress memory content.
        
        Args:
            compressed_content: The compressed content
            
        Returns:
            The decompressed content
        """
        pass
    
    @abstractmethod
    async def batch_compress(
        self,
        contents: List[str],
        metadata_list: Optional[List[Optional[MemoryMetadata]]] = None,
        target_length: Optional[int] = None,
    ) -> List[str]:
        """
        Compress multiple memory contents.
        
        Args:
            contents: List of contents to compress
            metadata_list: Optional list of metadata for each content
            target_length: Optional target length for compressed contents
            
        Returns:
            List of compressed contents
        """
        pass
    
    @abstractmethod
    async def batch_decompress(self, compressed_contents: List[str]) -> List[str]:
        """
        Decompress multiple memory contents.
        
        Args:
            compressed_contents: List of compressed contents
            
        Returns:
            List of decompressed contents
        """
        pass


# =============================================================================
# Memory Optimizer Interface
# =============================================================================


class IMemoryOptimizer(ABC):
    """
    Abstract interface for memory optimization implementations.
    
    This interface defines the contract for all optimization implementations.
    Optimizers are used to improve memory system performance and efficiency.
    
    Implementations should handle:
    - Memory indexing optimization
    - Query optimization
    - Storage optimization
    - Background optimization tasks
    """
    
    @abstractmethod
    async def initialize(self, config: Optional[Dict[str, Any]] = None) -> None:
        """
        Initialize the optimizer.
        
        Args:
            config: Configuration for the optimizer
        """
        pass
    
    @abstractmethod
    async def shutdown(self) -> None:
        """Shutdown the optimizer and clean up resources."""
        pass
    
    @abstractmethod
    async def optimize_index(self) -> None:
        """Optimize the memory index for better performance."""
        pass
    
    @abstractmethod
    async def optimize_storage(self) -> None:
        """Optimize memory storage (e.g., compact, defragment)."""
        pass
    
    @abstractmethod
    async def optimize_queries(self, queries: List[MemoryQuery]) -> List[MemoryQuery]:
        """
        Optimize a list of queries for better performance.
        
        Args:
            queries: List of queries to optimize
            
        Returns:
            List of optimized queries
        """
        pass
    
    @abstractmethod
    async def analyze_performance(self) -> Dict[str, Any]:
        """
        Analyze the performance of the memory system.
        
        Returns:
            Dictionary with performance analysis
        """
        pass
    
    @abstractmethod
    async def get_recommendations(self) -> List[Dict[str, Any]]:
        """
        Get optimization recommendations.
        
        Returns:
            List of optimization recommendations
        """
        pass


# =============================================================================
# Memory Intelligence Interface
# =============================================================================


class IMemoryIntelligence(ABC):
    """
    Abstract interface for memory intelligence implementations.
    
    This interface defines the contract for all intelligence implementations.
    Intelligence components add smart features to the memory system.
    
    Implementations should handle:
    - Importance scoring
    - Relevance ranking
    - Memory consolidation
    - Knowledge extraction
    - Relationship detection
    - Forgetting strategies
    """
    
    @abstractmethod
    async def initialize(self, config: Optional[Dict[str, Any]] = None) -> None:
        """
        Initialize the intelligence component.
        
        Args:
            config: Configuration for the intelligence component
        """
        pass
    
    @abstractmethod
    async def shutdown(self) -> None:
        """Shutdown the intelligence component and clean up resources."""
        pass
    
    @abstractmethod
    async def score_importance(self, memory: Memory) -> float:
        """
        Score the importance of a memory.
        
        Args:
            memory: The memory to score
            
        Returns:
            Importance score (0.0 to 1.0)
        """
        pass
    
    @abstractmethod
    async def rank_relevance(
        self,
        query: MemoryQuery,
        memories: List[Memory],
    ) -> List[Tuple[Memory, float]]:
        """
        Rank memories by relevance to a query.
        
        Args:
            query: The search query
            memories: List of memories to rank
            
        Returns:
            List of (memory, relevance_score) tuples, sorted by relevance
        """
        pass
    
    @abstractmethod
    async def should_forget(self, memory: Memory) -> bool:
        """
        Determine if a memory should be forgotten.
        
        Args:
            memory: The memory to evaluate
            
        Returns:
            True if the memory should be forgotten, False otherwise
        """
        pass
    
    @abstractmethod
    async def consolidate_memories(self, memories: List[Memory]) -> List[Memory]:
        """
        Consolidate multiple memories into fewer, more comprehensive ones.
        
        Args:
            memories: List of memories to consolidate
            
        Returns:
            List of consolidated memories
        """
        pass
    
    @abstractmethod
    async def extract_knowledge(self, memory: Memory) -> Dict[str, Any]:
        """
        Extract structured knowledge from a memory.
        
        Args:
            memory: The memory to analyze
            
        Returns:
            Dictionary with extracted knowledge
        """
        pass
    
    @abstractmethod
    async def detect_relationships(
        self,
        memories: List[Memory],
    ) -> List[Dict[str, Any]]:
        """
        Detect relationships between memories.
        
        Args:
            memories: List of memories to analyze
            
        Returns:
            List of detected relationships
        """
        pass
    
    @abstractmethod
    async def build_memory_graph(
        self,
        memories: List[Memory],
    ) -> Dict[str, Any]:
        """
        Build a graph representation of memories and their relationships.
        
        Args:
            memories: List of memories to include in the graph
            
        Returns:
            Dictionary representing the memory graph
        """
        pass


# =============================================================================
# Memory Provider Interface
# =============================================================================


class IMemoryProvider(ABC):
    """
    Abstract interface for memory provider implementations.
    
    This interface defines the contract for all memory provider implementations.
    Providers are responsible for creating and managing specific types of memories.
    
    Implementations should handle:
    - Memory creation
    - Memory type-specific operations
    - Integration with the memory system
    """
    
    @abstractmethod
    async def initialize(self, config: Optional[Dict[str, Any]] = None) -> None:
        """
        Initialize the memory provider.
        
        Args:
            config: Configuration for the provider
        """
        pass
    
    @abstractmethod
    async def shutdown(self) -> None:
        """Shutdown the memory provider and clean up resources."""
        pass
    
    @abstractmethod
    def get_supported_types(self) -> List[MemoryType]:
        """
        Get the memory types supported by this provider.
        
        Returns:
            List of supported memory types
        """
        pass
    
    @abstractmethod
    async def create_memory(
        self,
        content: str,
        memory_type: MemoryType,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Memory:
        """
        Create a new memory of the specified type.
        
        Args:
            content: The content of the memory
            memory_type: The type of memory to create
            metadata: Optional metadata for the memory
            
        Returns:
            The created memory
        """
        pass
    
    @abstractmethod
    async def process_memory(self, memory: Memory) -> Memory:
        """
        Process a memory (e.g., enrich, transform, validate).
        
        Args:
            memory: The memory to process
            
        Returns:
            The processed memory
        """
        pass
    
    @abstractmethod
    async def validate_memory(self, memory: Memory) -> bool:
        """
        Validate a memory of the supported type.
        
        Args:
            memory: The memory to validate
            
        Returns:
            True if the memory is valid, False otherwise
        """
        pass


# =============================================================================
# Memory Context Interface
# =============================================================================


class IMemoryContext(ABC):
    """
    Abstract interface for memory context implementations.
    
    This interface defines the contract for all memory context implementations.
    Contexts manage the current working set of memories for a session or task.
    
    Implementations should handle:
    - Context creation and management
    - Memory addition and removal
    - Context prioritization
    - Token budgeting
    - Context serialization
    """
    
    @abstractmethod
    async def initialize(self, config: Optional[Dict[str, Any]] = None) -> None:
        """
        Initialize the memory context.
        
        Args:
            config: Configuration for the context
        """
        pass
    
    @abstractmethod
    async def shutdown(self) -> None:
        """Shutdown the memory context and clean up resources."""
        pass
    
    @abstractmethod
    async def create_context(
        self,
        context_id: str,
        initial_memories: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Create a new memory context.
        
        Args:
            context_id: Unique identifier for the context
            initial_memories: Optional list of memory IDs to include initially
            metadata: Optional metadata for the context
        """
        pass
    
    @abstractmethod
    async def delete_context(self, context_id: str) -> bool:
        """
        Delete a memory context.
        
        Args:
            context_id: The ID of the context to delete
            
        Returns:
            True if the context was deleted, False otherwise
        """
        pass
    
    @abstractmethod
    async def add_to_context(
        self,
        context_id: str,
        memory_id: str,
        priority: Optional[float] = None,
    ) -> None:
        """
        Add a memory to a context.
        
        Args:
            context_id: The ID of the context
            memory_id: The ID of the memory to add
            priority: Optional priority for the memory in the context
        """
        pass
    
    @abstractmethod
    async def remove_from_context(self, context_id: str, memory_id: str) -> bool:
        """
        Remove a memory from a context.
        
        Args:
            context_id: The ID of the context
            memory_id: The ID of the memory to remove
            
        Returns:
            True if the memory was removed, False otherwise
        """
        pass
    
    @abstractmethod
    async def get_context(self, context_id: str) -> Dict[str, Any]:
        """
        Get information about a context.
        
        Args:
            context_id: The ID of the context
            
        Returns:
            Dictionary with context information
        """
        pass
    
    @abstractmethod
    async def get_context_memories(
        self,
        context_id: str,
        limit: Optional[int] = None,
        priority_threshold: Optional[float] = None,
    ) -> List[Tuple[str, float]]:
        """
        Get memories in a context, sorted by priority.
        
        Args:
            context_id: The ID of the context
            limit: Maximum number of memories to return
            priority_threshold: Optional minimum priority threshold
            
        Returns:
            List of (memory_id, priority) tuples
        """
        pass
    
    @abstractmethod
    async def prioritize_context(
        self,
        context_id: str,
        token_budget: Optional[int] = None,
    ) -> List[str]:
        """
        Prioritize memories in a context based on token budget.
        
        Args:
            context_id: The ID of the context
            token_budget: Optional maximum number of tokens to use
            
        Returns:
            List of memory IDs in priority order
        """
        pass
    
    @abstractmethod
    async def compress_context(
        self,
        context_id: str,
        target_size: Optional[int] = None,
    ) -> None:
        """
        Compress a context to fit within constraints.
        
        Args:
            context_id: The ID of the context
            target_size: Optional target size in tokens
        """
        pass
    
    @abstractmethod
    async def serialize_context(self, context_id: str) -> str:
        """
        Serialize a context for storage or transmission.
        
        Args:
            context_id: The ID of the context
            
        Returns:
            Serialized context string
        """
        pass
    
    @abstractmethod
    async def deserialize_context(
        self,
        context_id: str,
        serialized: str,
    ) -> None:
        """
        Deserialize a context from a string.
        
        Args:
            context_id: The ID of the context
            serialized: The serialized context string
        """
        pass
