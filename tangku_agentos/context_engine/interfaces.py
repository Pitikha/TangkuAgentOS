#!/usr/bin/env python3
"""
Abstract interfaces for the TangkuAgentOS Context Engine.

This module defines the abstract base classes (interfaces) that all context
components must implement. These interfaces ensure consistency and allow
for dependency injection and easy swapping of implementations.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, TypeVar, Generic, Union, AsyncIterator
from datetime import datetime

from .models import (
    Context,
    ContextType,
    ContextMetadata,
    ContextSource,
    ContextChunk,
    ContextAssemblyResult,
    ContextOptimizationResult,
    ContextCompressionResult,
    ContextBudgetResult,
    ContextCacheResult,
    ContextSessionResult,
    ContextConfig,
    AssemblyConfig,
    OptimizationConfig,
    CompressionConfig,
    BudgetConfig,
    CacheConfig,
    SessionConfig,
)

# Type variables for generic interfaces
T = TypeVar("T")


# =============================================================================
# Context Manager Interface
# =============================================================================


class IContextManager(ABC):
    """
    Abstract interface for context manager implementations.
    
    This interface defines the contract that all context manager implementations
    must follow. It provides methods for managing contexts, sessions, and
    the overall context lifecycle.
    
    Implementations should handle:
    - Context creation, retrieval, update, and deletion
    - Session management
    - Configuration management
    - Event handling
    - Resource cleanup
    """
    
    @abstractmethod
    async def initialize(self, config: Optional[Dict[str, Any]] = None) -> None:
        """
        Initialize the context manager.
        
        Args:
            config: Configuration for the manager
        """
        pass
    
    @abstractmethod
    async def shutdown(self) -> None:
        """Shutdown the context manager and clean up resources."""
        pass
    
    @abstractmethod
    async def create_context(
        self,
        context_type: ContextType = ContextType.CONVERSATION,
        metadata: Optional[Dict[str, Any]] = None,
        config: Optional[ContextConfig] = None,
    ) -> str:
        """
        Create a new context.
        
        Args:
            context_type: Type of the context to create
            metadata: Optional metadata for the context
            config: Optional configuration for the context
            
        Returns:
            The ID of the created context
        """
        pass
    
    @abstractmethod
    async def get_context(self, context_id: str) -> Optional[Context]:
        """
        Retrieve a context by its ID.
        
        Args:
            context_id: The ID of the context to retrieve
            
        Returns:
            The context if found, None otherwise
        """
        pass
    
    @abstractmethod
    async def get_contexts(self, context_ids: List[str]) -> Dict[str, Optional[Context]]:
        """
        Retrieve multiple contexts by their IDs.
        
        Args:
            context_ids: List of context IDs to retrieve
            
        Returns:
            Dictionary mapping context IDs to their corresponding contexts
        """
        pass
    
    @abstractmethod
    async def update_context(
        self,
        context_id: str,
        metadata: Optional[Dict[str, Any]] = None,
        config: Optional[ContextConfig] = None,
    ) -> Context:
        """
        Update an existing context.
        
        Args:
            context_id: The ID of the context to update
            metadata: Optional new metadata for the context
            config: Optional new configuration for the context
            
        Returns:
            The updated context
        """
        pass
    
    @abstractmethod
    async def delete_context(self, context_id: str) -> bool:
        """
        Delete a context.
        
        Args:
            context_id: The ID of the context to delete
            
        Returns:
            True if the context was deleted, False otherwise
        """
        pass
    
    @abstractmethod
    async def delete_contexts(self, context_ids: List[str]) -> int:
        """
        Delete multiple contexts.
        
        Args:
            context_ids: List of context IDs to delete
            
        Returns:
            Number of contexts deleted
        """
        pass
    
    @abstractmethod
    async def list_contexts(
        self,
        context_type: Optional[ContextType] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> List[Context]:
        """
        List contexts with optional filtering.
        
        Args:
            context_type: Optional filter by context type
            limit: Maximum number of contexts to return
            offset: Offset for pagination
            
        Returns:
            List of matching contexts
        """
        pass
    
    @abstractmethod
    async def count_contexts(self, context_type: Optional[ContextType] = None) -> int:
        """
        Count contexts matching the given criteria.
        
        Args:
            context_type: Optional filter by context type
            
        Returns:
            Number of matching contexts
        """
        pass
    
    @abstractmethod
    async def assemble_context(
        self,
        sources: List[Dict[str, Any]],
        config: Optional[AssemblyConfig] = None,
    ) -> ContextAssemblyResult:
        """
        Assemble context from multiple sources.
        
        Args:
            sources: List of source specifications
            config: Optional assembly configuration
            
        Returns:
            Result of the assembly operation
        """
        pass
    
    @abstractmethod
    async def optimize_context(
        self,
        context: Context,
        config: Optional[OptimizationConfig] = None,
    ) -> ContextOptimizationResult:
        """
        Optimize a context.
        
        Args:
            context: The context to optimize
            config: Optional optimization configuration
            
        Returns:
            Result of the optimization operation
        """
        pass
    
    @abstractmethod
    async def compress_context(
        self,
        context: Context,
        config: Optional[CompressionConfig] = None,
    ) -> ContextCompressionResult:
        """
        Compress a context.
        
        Args:
            context: The context to compress
            config: Optional compression configuration
            
        Returns:
            Result of the compression operation
        """
        pass
    
    @abstractmethod
    async def budget_context(
        self,
        context: Context,
        config: Optional[BudgetConfig] = None,
    ) -> ContextBudgetResult:
        """
        Apply token budget to a context.
        
        Args:
            context: The context to budget
            config: Optional budget configuration
            
        Returns:
            Result of the budgeting operation
        """
        pass
    
    @abstractmethod
    async def get_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the context manager.
        
        Returns:
            Dictionary with manager statistics
        """
        pass


# =============================================================================
# Context Assembler Interface
# =============================================================================


class IContextAssembler(ABC):
    """
    Abstract interface for context assembler implementations.
    
    This interface defines the contract for all context assembler implementations.
    Assemblers are responsible for gathering context from multiple sources
    and combining them into a unified context.
    
    Implementations should handle:
    - Multi-source context assembly
    - Context prioritization
    - Context merging
    - Context deduplication
    - Context validation
    - Metadata enrichment
    - Source attribution
    """
    
    @abstractmethod
    async def initialize(self, config: Optional[Dict[str, Any]] = None) -> None:
        """
        Initialize the context assembler.
        
        Args:
            config: Configuration for the assembler
        """
        pass
    
    @abstractmethod
    async def shutdown(self) -> None:
        """Shutdown the context assembler and clean up resources."""
        pass
    
    @abstractmethod
    async def assemble(
        self,
        sources: List[Dict[str, Any]],
        config: Optional[AssemblyConfig] = None,
    ) -> ContextAssemblyResult:
        """
        Assemble context from multiple sources.
        
        Args:
            sources: List of source specifications
            config: Optional assembly configuration
            
        Returns:
            Result of the assembly operation
        """
        pass
    
    @abstractmethod
    async def add_source(
        self,
        source_name: str,
        source: Any,
        priority: Optional[int] = None,
    ) -> None:
        """
        Add a context source to the assembler.
        
        Args:
            source_name: Name of the source
            source: The source implementation
            priority: Optional priority for the source
        """
        pass
    
    @abstractmethod
    async def remove_source(self, source_name: str) -> None:
        """
        Remove a context source from the assembler.
        
        Args:
            source_name: Name of the source to remove
        """
        pass
    
    @abstractmethod
    async def get_source(self, source_name: str) -> Any:
        """
        Get a context source by name.
        
        Args:
            source_name: Name of the source to retrieve
            
        Returns:
            The source implementation
        """
        pass
    
    @abstractmethod
    async def list_sources(self) -> List[str]:
        """
        List all registered context sources.
        
        Returns:
            List of source names
        """
        pass
    
    @abstractmethod
    async def prioritize(
        self,
        context: Context,
        config: Optional[Dict[str, Any]] = None,
    ) -> Context:
        """
        Prioritize chunks in a context.
        
        Args:
            context: The context to prioritize
            config: Optional configuration for prioritization
            
        Returns:
            The prioritized context
        """
        pass
    
    @abstractmethod
    async def merge(
        self,
        contexts: List[Context],
        config: Optional[Dict[str, Any]] = None,
    ) -> Context:
        """
        Merge multiple contexts into one.
        
        Args:
            contexts: List of contexts to merge
            config: Optional configuration for merging
            
        Returns:
            The merged context
        """
        pass
    
    @abstractmethod
    async def deduplicate(
        self,
        context: Context,
        config: Optional[Dict[str, Any]] = None,
    ) -> Context:
        """
        Remove duplicate chunks from a context.
        
        Args:
            context: The context to deduplicate
            config: Optional configuration for deduplication
            
        Returns:
            The deduplicated context
        """
        pass


# =============================================================================
# Context Builder Interface
# =============================================================================


class IContextBuilder(ABC):
    """
    Abstract interface for context builder implementations.
    
    This interface defines the contract for all context builder implementations.
    Builders are responsible for constructing context objects from raw data.
    
    Implementations should handle:
    - Context construction from various data sources
    - Metadata enrichment
    - Chunk creation and management
    - Source attribution
    """
    
    @abstractmethod
    async def initialize(self, config: Optional[Dict[str, Any]] = None) -> None:
        """
        Initialize the context builder.
        
        Args:
            config: Configuration for the builder
        """
        pass
    
    @abstractmethod
    async def shutdown(self) -> None:
        """Shutdown the context builder and clean up resources."""
        pass
    
    @abstractmethod
    async def build(
        self,
        data: Any,
        source: ContextSource,
        metadata: Optional[Dict[str, Any]] = None,
        config: Optional[Dict[str, Any]] = None,
    ) -> Context:
        """
        Build a context from raw data.
        
        Args:
            data: The raw data to build context from
            source: The source of the data
            metadata: Optional metadata for the context
            config: Optional configuration for building
            
        Returns:
            The built context
        """
        pass
    
    @abstractmethod
    async def build_chunk(
        self,
        content: str,
        source: ContextSource,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> ContextChunk:
        """
        Build a context chunk from content.
        
        Args:
            content: The content for the chunk
            source: The source of the content
            metadata: Optional metadata for the chunk
            
        Returns:
            The built context chunk
        """
        pass
    
    @abstractmethod
    async def enrich_metadata(
        self,
        context: Context,
        additional_metadata: Optional[Dict[str, Any]] = None,
    ) -> Context:
        """
        Enrich context metadata with additional information.
        
        Args:
            context: The context to enrich
            additional_metadata: Optional additional metadata to add
            
        Returns:
            The enriched context
        """
        pass
    
    @abstractmethod
    async def attribute_sources(
        self,
        context: Context,
        source_info: Dict[str, ContextSourceInfo],
    ) -> Context:
        """
        Add source attribution to context chunks.
        
        Args:
            context: The context to attribute
            source_info: Dictionary mapping chunk IDs to source info
            
        Returns:
            The context with source attribution
        """
        pass


# =============================================================================
# Context Optimizer Interface
# =============================================================================


class IContextOptimizer(ABC):
    """
    Abstract interface for context optimizer implementations.
    
    This interface defines the contract for all context optimizer implementations.
    Optimizers are responsible for improving context quality and efficiency.
    
    Implementations should handle:
    - Token budgeting
    - Context compression
    - Context ranking
    - Relevance scoring
    - Adaptive context windows
    - Dynamic optimization
    """
    
    @abstractmethod
    async def initialize(self, config: Optional[Dict[str, Any]] = None) -> None:
        """
        Initialize the context optimizer.
        
        Args:
            config: Configuration for the optimizer
        """
        pass
    
    @abstractmethod
    async def shutdown(self) -> None:
        """Shutdown the context optimizer and clean up resources."""
        pass
    
    @abstractmethod
    async def optimize(
        self,
        context: Context,
        config: Optional[OptimizationConfig] = None,
    ) -> ContextOptimizationResult:
        """
        Optimize a context.
        
        Args:
            context: The context to optimize
            config: Optional optimization configuration
            
        Returns:
            Result of the optimization operation
        """
        pass
    
    @abstractmethod
    async def budget(
        self,
        context: Context,
        config: Optional[BudgetConfig] = None,
    ) -> ContextBudgetResult:
        """
        Apply token budget to a context.
        
        Args:
            context: The context to budget
            config: Optional budget configuration
            
        Returns:
            Result of the budgeting operation
        """
        pass
    
    @abstractmethod
    async def compress(
        self,
        context: Context,
        config: Optional[CompressionConfig] = None,
    ) -> ContextCompressionResult:
        """
        Compress a context.
        
        Args:
            context: The context to compress
            config: Optional compression configuration
            
        Returns:
            Result of the compression operation
        """
        pass
    
    @abstractmethod
    async def rank(
        self,
        context: Context,
        query: Optional[str] = None,
    ) -> Context:
        """
        Rank chunks in a context by relevance.
        
        Args:
            context: The context to rank
            query: Optional query for relevance ranking
            
        Returns:
            The ranked context
        """
        pass
    
    @abstractmethod
    async def score_relevance(
        self,
        chunks: List[ContextChunk],
        query: str,
    ) -> List[Tuple[ContextChunk, float]]:
        """
        Score chunks by relevance to a query.
        
        Args:
            chunks: List of chunks to score
            query: The query for relevance scoring
            
        Returns:
            List of (chunk, relevance_score) tuples
        """
        pass


# =============================================================================
# Context Compressor Interface
# =============================================================================


class IContextCompressor(ABC):
    """
    Abstract interface for context compressor implementations.
    
    This interface defines the contract for all context compressor implementations.
    Compressors are responsible for reducing context size while preserving
    important information.
    
    Implementations should handle:
    - Context compression using various methods
    - Quality preservation
    - Performance optimization
    - Configurable compression levels
    """
    
    @abstractmethod
    async def initialize(self, config: Optional[Dict[str, Any]] = None) -> None:
        """
        Initialize the context compressor.
        
        Args:
            config: Configuration for the compressor
        """
        pass
    
    @abstractmethod
    async def shutdown(self) -> None:
        """Shutdown the context compressor and clean up resources."""
        pass
    
    @abstractmethod
    async def compress(
        self,
        context: Context,
        config: Optional[CompressionConfig] = None,
    ) -> ContextCompressionResult:
        """
        Compress a context.
        
        Args:
            context: The context to compress
            config: Optional compression configuration
            
        Returns:
            Result of the compression operation
        """
        pass
    
    @abstractmethod
    async def compress_chunk(
        self,
        chunk: ContextChunk,
        config: Optional[CompressionConfig] = None,
    ) -> ContextChunk:
        """
        Compress a single context chunk.
        
        Args:
            chunk: The chunk to compress
            config: Optional compression configuration
            
        Returns:
            The compressed chunk
        """
        pass
    
    @abstractmethod
    async def batch_compress(
        self,
        chunks: List[ContextChunk],
        config: Optional[CompressionConfig] = None,
    ) -> List[ContextChunk]:
        """
        Compress multiple context chunks.
        
        Args:
            chunks: List of chunks to compress
            config: Optional compression configuration
            
        Returns:
            List of compressed chunks
        """
        pass


# =============================================================================
# Context Budget Interface
# =============================================================================


class IContextBudget(ABC):
    """
    Abstract interface for context budget implementations.
    
    This interface defines the contract for all context budget implementations.
    Budgets are responsible for managing token usage and enforcing limits.
    
    Implementations should handle:
    - Token counting
    - Budget enforcement
    - Overflow handling
    - Budget reporting
    """
    
    @abstractmethod
    async def initialize(self, config: Optional[Dict[str, Any]] = None) -> None:
        """
        Initialize the context budget.
        
        Args:
            config: Configuration for the budget
        """
        pass
    
    @abstractmethod
    async def shutdown(self) -> None:
        """Shutdown the context budget and clean up resources."""
        pass
    
    @abstractmethod
    async def apply_budget(
        self,
        context: Context,
        config: Optional[BudgetConfig] = None,
    ) -> ContextBudgetResult:
        """
        Apply token budget to a context.
        
        Args:
            context: The context to budget
            config: Optional budget configuration
            
        Returns:
            Result of the budgeting operation
        """
        pass
    
    @abstractmethod
    async def count_tokens(self, text: str) -> int:
        """
        Count the number of tokens in a text.
        
        Args:
            text: The text to count tokens in
            
        Returns:
            Number of tokens in the text
        """
        pass
    
    @abstractmethod
    async def count_tokens_in_context(self, context: Context) -> int:
        """
        Count the total number of tokens in a context.
        
        Args:
            context: The context to count tokens in
            
        Returns:
            Total number of tokens in the context
        """
        pass
    
    @abstractmethod
    async def check_budget(
        self,
        context: Context,
        config: Optional[BudgetConfig] = None,
    ) -> bool:
        """
        Check if a context is within the token budget.
        
        Args:
            context: The context to check
            config: Optional budget configuration
            
        Returns:
            True if within budget, False otherwise
        """
        pass
    
    @abstractmethod
    async def get_budget_report(self, context: Context) -> Dict[str, Any]:
        """
        Get a detailed budget report for a context.
        
        Args:
            context: The context to report on
            
        Returns:
            Dictionary with budget report details
        """
        pass


# =============================================================================
# Context Cache Interface
# =============================================================================


class IContextCache(ABC):
    """
    Abstract interface for context cache implementations.
    
    This interface defines the contract for all context cache implementations.
    Caches are used to improve performance by storing frequently accessed contexts.
    
    Implementations should handle:
    - Cache storage and retrieval
    - Expiration and eviction
    - Cache invalidation
    - Multi-level caching
    - Cache statistics
    """
    
    @abstractmethod
    async def initialize(
        self,
        config: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Initialize the context cache.
        
        Args:
            config: Configuration for the cache
        """
        pass
    
    @abstractmethod
    async def shutdown(self) -> None:
        """Shutdown the context cache and clean up resources."""
        pass
    
    @abstractmethod
    async def store(
        self,
        context: Context,
        ttl: Optional[float] = None,
    ) -> None:
        """
        Store a context in the cache.
        
        Args:
            context: The context to store
            ttl: Optional time-to-live in seconds
        """
        pass
    
    @abstractmethod
    async def retrieve(self, context_id: str) -> Optional[Context]:
        """
        Retrieve a context from the cache.
        
        Args:
            context_id: The ID of the context to retrieve
            
        Returns:
            The context if found in cache, None otherwise
        """
        pass
    
    @abstractmethod
    async def retrieve_many(self, context_ids: List[str]) -> Dict[str, Optional[Context]]:
        """
        Retrieve multiple contexts from the cache.
        
        Args:
            context_ids: List of context IDs to retrieve
            
        Returns:
            Dictionary mapping context IDs to their cached contexts (or None if not found)
        """
        pass
    
    @abstractmethod
    async def invalidate(self, context_id: str) -> bool:
        """
        Invalidate a context in the cache.
        
        Args:
            context_id: The ID of the context to invalidate
            
        Returns:
            True if the context was invalidated, False otherwise
        """
        pass
    
    @abstractmethod
    async def invalidate_many(self, context_ids: List[str]) -> int:
        """
        Invalidate multiple contexts in the cache.
        
        Args:
            context_ids: List of context IDs to invalidate
            
        Returns:
            Number of contexts invalidated
        """
        pass
    
    @abstractmethod
    async def clear(self) -> None:
        """Clear all contexts from the cache."""
        pass
    
    @abstractmethod
    async def exists(self, context_id: str) -> bool:
        """
        Check if a context exists in the cache.
        
        Args:
            context_id: The ID of the context to check
            
        Returns:
            True if the context exists in cache, False otherwise
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
# Context Session Interface
# =============================================================================


class IContextSession(ABC):
    """
    Abstract interface for context session implementations.
    
    This interface defines the contract for all context session implementations.
    Sessions manage the current working set of contexts for a user or task.
    
    Implementations should handle:
    - Session creation and management
    - Context addition and removal
    - Session persistence
    - Session isolation
    - Workspace management
    """
    
    @abstractmethod
    async def initialize(self, config: Optional[Dict[str, Any]] = None) -> None:
        """
        Initialize the context session manager.
        
        Args:
            config: Configuration for the session manager
        """
        pass
    
    @abstractmethod
    async def shutdown(self) -> None:
        """Shutdown the context session manager and clean up resources."""
        pass
    
    @abstractmethod
    async def create_session(
        self,
        session_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Create a new session.
        
        Args:
            session_id: Optional ID for the session
            metadata: Optional metadata for the session
            
        Returns:
            The ID of the created session
        """
        pass
    
    @abstractmethod
    async def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Get information about a session.
        
        Args:
            session_id: The ID of the session to retrieve
            
        Returns:
            Dictionary with session information if found, None otherwise
        """
        pass
    
    @abstractmethod
    async def delete_session(self, session_id: str) -> bool:
        """
        Delete a session.
        
        Args:
            session_id: The ID of the session to delete
            
        Returns:
            True if the session was deleted, False otherwise
        """
        pass
    
    @abstractmethod
    async def add_to_session(
        self,
        session_id: str,
        context_id: str,
        priority: Optional[int] = None,
    ) -> None:
        """
        Add a context to a session.
        
        Args:
            session_id: The ID of the session
            context_id: The ID of the context to add
            priority: Optional priority for the context in the session
        """
        pass
    
    @abstractmethod
    async def remove_from_session(self, session_id: str, context_id: str) -> bool:
        """
        Remove a context from a session.
        
        Args:
            session_id: The ID of the session
            context_id: The ID of the context to remove
            
        Returns:
            True if the context was removed, False otherwise
        """
        pass
    
    @abstractmethod
    async def get_session_contexts(
        self,
        session_id: str,
        limit: Optional[int] = None,
        priority_threshold: Optional[int] = None,
    ) -> List[str]:
        """
        Get all context IDs in a session.
        
        Args:
            session_id: The ID of the session
            limit: Maximum number of contexts to return
            priority_threshold: Optional minimum priority threshold
            
        Returns:
            List of context IDs in the session
        """
        pass
    
    @abstractmethod
    async def list_sessions(
        self,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> List[str]:
        """
        List all sessions.
        
        Args:
            limit: Maximum number of sessions to return
            offset: Offset for pagination
            
        Returns:
            List of session IDs
        """
        pass
    
    @abstractmethod
    async def create_workspace(
        self,
        workspace_id: str,
        session_ids: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Create a new workspace.
        
        Args:
            workspace_id: ID for the workspace
            session_ids: Optional list of session IDs to include
            metadata: Optional metadata for the workspace
            
        Returns:
            The ID of the created workspace
        """
        pass
    
    @abstractmethod
    async def get_workspace(self, workspace_id: str) -> Optional[Dict[str, Any]]:
        """
        Get information about a workspace.
        
        Args:
            workspace_id: The ID of the workspace to retrieve
            
        Returns:
            Dictionary with workspace information if found, None otherwise
        """
        pass
    
    @abstractmethod
    async def delete_workspace(self, workspace_id: str) -> bool:
        """
        Delete a workspace.
        
        Args:
            workspace_id: The ID of the workspace to delete
            
        Returns:
            True if the workspace was deleted, False otherwise
        """
        pass


# =============================================================================
# Context Provider Interface
# =============================================================================


class IContextProvider(ABC):
    """
    Abstract interface for context provider implementations.
    
    This interface defines the contract for all context provider implementations.
    Providers are responsible for supplying context from various sources.
    
    Implementations should handle:
    - Context retrieval from specific sources
    - Query support
    - Filtering
    - Pagination
    - Source-specific operations
    """
    
    @abstractmethod
    async def initialize(self, config: Optional[Dict[str, Any]] = None) -> None:
        """
        Initialize the context provider.
        
        Args:
            config: Configuration for the provider
        """
        pass
    
    @abstractmethod
    async def shutdown(self) -> None:
        """Shutdown the context provider and clean up resources."""
        pass
    
    @abstractmethod
    async def provide(
        self,
        query: Optional[str] = None,
        filters: Optional[Dict[str, Any]] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> Context:
        """
        Provide context based on a query.
        
        Args:
            query: Optional query for context retrieval
            filters: Optional filters to apply
            limit: Maximum number of results to return
            offset: Offset for pagination
            
        Returns:
            The provided context
        """
        pass
    
    @abstractmethod
    async def get_source_type(self) -> str:
        """
        Get the type of source this provider handles.
        
        Returns:
            The source type (e.g., "memory", "knowledge", "document")
        """
        pass
    
    @abstractmethod
    async def get_source_id(self) -> str:
        """
        Get the unique identifier for this provider.
        
        Returns:
            The source ID
        """
        pass


# =============================================================================
# Context Registry Interface
# =============================================================================


class IContextRegistry(ABC):
    """
    Abstract interface for context registry implementations.
    
    This interface defines the contract for all context registry implementations.
    Registries are responsible for tracking and managing registered contexts.
    
    Implementations should handle:
    - Context registration and unregistration
    - Context lookup
    - Context listing
    - Metadata management
    """
    
    @abstractmethod
    async def initialize(self, config: Optional[Dict[str, Any]] = None) -> None:
        """
        Initialize the context registry.
        
        Args:
            config: Configuration for the registry
        """
        pass
    
    @abstractmethod
    async def shutdown(self) -> None:
        """Shutdown the context registry and clean up resources."""
        pass
    
    @abstractmethod
    async def register(
        self,
        context: Context,
        context_id: Optional[str] = None,
    ) -> str:
        """
        Register a context with the registry.
        
        Args:
            context: The context to register
            context_id: Optional ID for the context
            
        Returns:
            The ID of the registered context
        """
        pass
    
    @abstractmethod
    async def unregister(self, context_id: str) -> bool:
        """
        Unregister a context from the registry.
        
        Args:
            context_id: The ID of the context to unregister
            
        Returns:
            True if the context was unregistered, False otherwise
        """
        pass
    
    @abstractmethod
    async def get(self, context_id: str) -> Optional[Context]:
        """
        Get a registered context by its ID.
        
        Args:
            context_id: The ID of the context to retrieve
            
        Returns:
            The context if found, None otherwise
        """
        pass
    
    @abstractmethod
    async def list(
        self,
        context_type: Optional[ContextType] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> List[Context]:
        """
        List registered contexts with optional filtering.
        
        Args:
            context_type: Optional filter by context type
            limit: Maximum number of contexts to return
            offset: Offset for pagination
            
        Returns:
            List of matching contexts
        """
        pass
    
    @abstractmethod
    async def exists(self, context_id: str) -> bool:
        """
        Check if a context is registered.
        
        Args:
            context_id: The ID of the context to check
            
        Returns:
            True if the context is registered, False otherwise
        """
        pass
    
    @abstractmethod
    async def update_metadata(
        self,
        context_id: str,
        metadata: Dict[str, Any],
    ) -> bool:
        """
        Update metadata for a registered context.
        
        Args:
            context_id: The ID of the context to update
            metadata: The new metadata
            
        Returns:
            True if the metadata was updated, False otherwise
        """
        pass


# =============================================================================
# Context Resolver Interface
# =============================================================================


class IContextResolver(ABC):
    """
    Abstract interface for context resolver implementations.
    
    This interface defines the contract for all context resolver implementations.
    Resolvers are responsible for resolving context references and dependencies.
    
    Implementations should handle:
    - Reference resolution
    - Dependency resolution
    - Context loading
    - Circular reference detection
    """
    
    @abstractmethod
    async def initialize(self, config: Optional[Dict[str, Any]] = None) -> None:
        """
        Initialize the context resolver.
        
        Args:
            config: Configuration for the resolver
        """
        pass
    
    @abstractmethod
    async def shutdown(self) -> None:
        """Shutdown the context resolver and clean up resources."""
        pass
    
    @abstractmethod
    async def resolve(
        self,
        reference: str,
        context: Optional[Context] = None,
    ) -> Optional[Context]:
        """
        Resolve a context reference.
        
        Args:
            reference: The reference to resolve
            context: Optional context to resolve within
            
        Returns:
            The resolved context if found, None otherwise
        """
        pass
    
    @abstractmethod
    async def resolve_many(
        self,
        references: List[str],
        context: Optional[Context] = None,
    ) -> Dict[str, Optional[Context]]:
        """
        Resolve multiple context references.
        
        Args:
            references: List of references to resolve
            context: Optional context to resolve within
            
        Returns:
            Dictionary mapping references to their resolved contexts
        """
        pass
    
    @abstractmethod
    async def resolve_dependencies(
        self,
        context: Context,
    ) -> Context:
        """
        Resolve all dependencies for a context.
        
        Args:
            context: The context to resolve dependencies for
            
        Returns:
            The context with all dependencies resolved
        """
        pass
    
    @abstractmethod
    async def detect_circular_dependencies(
        self,
        context: Context,
    ) -> List[List[str]]:
        """
        Detect circular dependencies in a context.
        
        Args:
            context: The context to check
            
        Returns:
            List of circular dependency chains
        """
        pass
