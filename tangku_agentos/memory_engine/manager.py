#!/usr/bin/env python3
"""
Memory Manager for the TangkuAgentOS Memory Engine.

This module implements the main memory management system, providing a unified
interface for all memory operations across different memory types and storage
backends.
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple, Union, AsyncIterator
from uuid import uuid4

from .interfaces import IMemoryStore, IMemoryVectorDB, IMemoryBackend
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
    EmbeddingConfig,
    SearchConfig,
    CompressionConfig,
    CacheConfig,
)
from .exceptions import (
    MemoryError,
    MemoryNotFoundError,
    MemoryExistsError,
    MemoryValidationError,
    MemoryBackendError,
    MemoryConflictError,
)

logger = logging.getLogger(__name__)


# =============================================================================
# Base Memory Manager
# =============================================================================


class BaseMemoryManager(ABC):
    """
    Base class for memory manager implementations.
    
    This class provides common functionality for managing memories.
    Subclasses should implement specific memory management features.
    """
    
    def __init__(self, config: Optional[MemoryConfig] = None):
        """
        Initialize the memory manager.
        
        Args:
            config: Configuration for the memory manager
        """
        self.config = config or MemoryConfig()
        self._stores: Dict[str, IMemoryStore] = {}
        self._vector_dbs: Dict[str, IMemoryVectorDB] = {}
        self._initialized = False
        self._lock = asyncio.Lock()
        self._event_callbacks: List[Callable] = []
    
    async def initialize(self, config: Optional[Dict[str, Any]] = None) -> None:
        """
        Initialize the memory manager.
        
        Args:
            config: Additional configuration
        """
        async with self._lock:
            if self._initialized:
                return
            
            # Update config
            if config:
                for key, value in config.items():
                    setattr(self.config, key, value)
            
            # Initialize default store
            await self._initialize_default_store()
            
            # Initialize default vector DB
            await self._initialize_default_vector_db()
            
            self._initialized = True
            logger.info("Initialized MemoryManager")
    
    async def shutdown(self) -> None:
        """Shutdown the memory manager and clean up resources."""
        async with self._lock:
            if not self._initialized:
                return
            
            # Shutdown all stores
            for store_name, store in self._stores.items():
                try:
                    await store.shutdown()
                except Exception as e:
                    logger.error(f"Error shutting down store {store_name}: {e}")
            
            # Shutdown all vector DBs
            for db_name, vector_db in self._vector_dbs.items():
                try:
                    await vector_db.shutdown()
                except Exception as e:
                    logger.error(f"Error shutting down vector DB {db_name}: {e}")
            
            self._stores.clear()
            self._vector_dbs.clear()
            self._initialized = False
            logger.info("Shut down MemoryManager")
    
    async def _initialize_default_store(self) -> None:
        """Initialize the default memory store."""
        from .store import MemoryStore
        from .backend import SQLiteBackend, BackendConfig
        
        # Create SQLite backend
        backend_config = BackendConfig(
            backend_type="sqlite",
            connection_string=":memory:",
        )
        backend = SQLiteBackend(**backend_config.__dict__)
        
        # Create memory store
        store = MemoryStore(backend, self.config)
        await store.initialize()
        
        # Register as default store
        self._stores["default"] = store
    
    async def _initialize_default_vector_db(self) -> None:
        """Initialize the default vector database."""
        from .vector_db import FAISSBackend, VectorDBConfig
        
        # Create FAISS backend
        vector_config = VectorDBConfig(
            dimension=self.config.embedding.dimension,
            metric=self.config.search.method.name.lower(),
        )
        vector_db = FAISSBackend(vector_config)
        await vector_db.initialize()
        
        # Register as default vector DB
        self._vector_dbs["default"] = vector_db
    
    @property
    def default_store(self) -> IMemoryStore:
        """Get the default memory store."""
        return self._stores.get("default")
    
    @property
    def default_vector_db(self) -> IMemoryVectorDB:
        """Get the default vector database."""
        return self._vector_dbs.get("default")
    
    # Abstract methods to be implemented by subclasses
    @abstractmethod
    async def add_memory(
        self,
        content: str,
        memory_type: MemoryType = MemoryType.WORKING,
        metadata: Optional[Dict[str, Any]] = None,
        store: Optional[str] = None,
    ) -> str:
        """Add a new memory."""
        pass
    
    @abstractmethod
    async def get_memory(self, memory_id: str, store: Optional[str] = None) -> Optional[Memory]:
        """Retrieve a memory by ID."""
        pass
    
    @abstractmethod
    async def update_memory(
        self,
        memory_id: str,
        content: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        store: Optional[str] = None,
    ) -> Memory:
        """Update an existing memory."""
        pass
    
    @abstractmethod
    async def delete_memory(self, memory_id: str, store: Optional[str] = None) -> bool:
        """Delete a memory."""
        pass
    
    @abstractmethod
    async def search_memories(
        self,
        query: Union[str, MemoryQuery],
        store: Optional[str] = None,
    ) -> List[MemorySearchResult]:
        """Search for memories."""
        pass


# =============================================================================
# Memory Manager
# =============================================================================


class MemoryManager(BaseMemoryManager):
    """
    Main memory manager implementation for the Memory Engine.
    
    This class provides a comprehensive memory management system with support for:
    - Multiple memory types (short-term, long-term, working, etc.)
    - Multiple storage backends (SQLite, PostgreSQL, Redis, etc.)
    - Multiple vector databases (FAISS, ChromaDB, Qdrant, etc.)
    - Memory versioning
    - Memory expiration (TTL)
    - Memory snapshots and backups
    - Memory search and filtering
    - Event notifications
    
    Example:
        ```python
        from tangku_agentos.memory_engine import MemoryManager, MemoryType
        
        # Create and initialize the memory manager
        memory_manager = MemoryManager()
        await memory_manager.initialize()
        
        # Add a memory
        memory_id = await memory_manager.add_memory(
            content="Hello, world!",
            memory_type=MemoryType.WORKING,
            metadata={"source": "user", "tags": ["greeting"]},
        )
        
        # Retrieve the memory
        memory = await memory_manager.get_memory(memory_id)
        print(memory.content)
        
        # Search for memories
        results = await memory_manager.search_memories("Hello")
        for result in results:
            print(f"{result.memory.content} (score: {result.score})")
        
        # Shutdown the memory manager
        await memory_manager.shutdown()
        ```
    """
    
    def __init__(self, config: Optional[MemoryConfig] = None):
        """
        Initialize the memory manager.
        
        Args:
            config: Configuration for the memory manager
        """
        super().__init__(config)
        self._snapshots: Dict[str, MemorySnapshot] = {}
        self._backups: Dict[str, MemoryBackup] = {}
        self._version_manager = None
        self._embedding_provider = None
    
    async def initialize(self, config: Optional[Dict[str, Any]] = None) -> None:
        """Initialize the memory manager."""
        await super().initialize(config)
        
        # Initialize version manager
        from .version_manager import MemoryVersionManager
        self._version_manager = MemoryVersionManager(self)
        
        # Initialize embedding provider
        from .intelligence import MemoryIntelligence
        self._embedding_provider = MemoryIntelligence(self.config)
    
    async def shutdown(self) -> None:
        """Shutdown the memory manager."""
        await super().shutdown()
    
    # =========================================================================
    # Store Management
    # =========================================================================
    
    async def register_store(
        self,
        name: str,
        store: IMemoryStore,
    ) -> None:
        """
        Register a memory store with the manager.
        
        Args:
            name: Name of the store
            store: The memory store to register
        """
        async with self._lock:
            if name in self._stores:
                raise MemoryError(
                    message=f"Store '{name}' already registered",
                    code="STORE_EXISTS",
                )
            
            await store.initialize()
            self._stores[name] = store
            logger.info(f"Registered memory store: {name}")
    
    async def unregister_store(self, name: str) -> None:
        """
        Unregister a memory store from the manager.
        
        Args:
            name: Name of the store to unregister
        """
        async with self._lock:
            if name not in self._stores:
                raise MemoryError(
                    message=f"Store '{name}' not found",
                    code="STORE_NOT_FOUND",
                )
            
            await self._stores[name].shutdown()
            del self._stores[name]
            logger.info(f"Unregistered memory store: {name}")
    
    def get_store(self, name: str = "default") -> IMemoryStore:
        """
        Get a registered memory store.
        
        Args:
            name: Name of the store to retrieve
            
        Returns:
            The memory store
            
        Raises:
            MemoryError: If the store is not found
        """
        store = self._stores.get(name)
        if not store:
            raise MemoryError(
                message=f"Store '{name}' not found",
                code="STORE_NOT_FOUND",
            )
        return store
    
    def list_stores(self) -> List[str]:
        """List all registered memory stores."""
        return list(self._stores.keys())
    
    # =========================================================================
    # Vector DB Management
    # =========================================================================
    
    async def register_vector_db(
        self,
        name: str,
        vector_db: IMemoryVectorDB,
    ) -> None:
        """
        Register a vector database with the manager.
        
        Args:
            name: Name of the vector database
            vector_db: The vector database to register
        """
        async with self._lock:
            if name in self._vector_dbs:
                raise MemoryError(
                    message=f"Vector DB '{name}' already registered",
                    code="VECTOR_DB_EXISTS",
                )
            
            await vector_db.initialize()
            self._vector_dbs[name] = vector_db
            logger.info(f"Registered vector DB: {name}")
    
    async def unregister_vector_db(self, name: str) -> None:
        """
        Unregister a vector database from the manager.
        
        Args:
            name: Name of the vector database to unregister
        """
        async with self._lock:
            if name not in self._vector_dbs:
                raise MemoryError(
                    message=f"Vector DB '{name}' not found",
                    code="VECTOR_DB_NOT_FOUND",
                )
            
            await self._vector_dbs[name].shutdown()
            del self._vector_dbs[name]
            logger.info(f"Unregistered vector DB: {name}")
    
    def get_vector_db(self, name: str = "default") -> IMemoryVectorDB:
        """
        Get a registered vector database.
        
        Args:
            name: Name of the vector database to retrieve
            
        Returns:
            The vector database
            
        Raises:
            MemoryError: If the vector database is not found
        """
        vector_db = self._vector_dbs.get(name)
        if not vector_db:
            raise MemoryError(
                message=f"Vector DB '{name}' not found",
                code="VECTOR_DB_NOT_FOUND",
            )
        return vector_db
    
    def list_vector_dbs(self) -> List[str]:
        """List all registered vector databases."""
        return list(self._vector_dbs.keys())
    
    # =========================================================================
    # Memory Operations
    # =========================================================================
    
    async def add_memory(
        self,
        content: str,
        memory_type: MemoryType = MemoryType.WORKING,
        metadata: Optional[Dict[str, Any]] = None,
        store: Optional[str] = None,
        embedding: Optional[List[float]] = None,
        generate_embedding: bool = True,
    ) -> str:
        """
        Add a new memory to the memory manager.
        
        Args:
            content: The content of the memory
            memory_type: The type of the memory
            metadata: Optional metadata for the memory
            store: Name of the store to use (default: "default")
            embedding: Optional pre-computed embedding
            generate_embedding: Whether to generate an embedding if not provided
            
        Returns:
            The ID of the added memory
        """
        if not self._initialized:
            await self.initialize()
        
        # Get the store
        memory_store = self.get_store(store or "default")
        
        # Create metadata
        metadata = metadata or {}
        memory_metadata = MemoryMetadata(
            memory_id=str(uuid4()),
            memory_type=memory_type,
            source=metadata.get("source", "unknown"),
            author=metadata.get("author", "system"),
            tags=metadata.get("tags", []),
            importance=metadata.get("importance", 0.5),
            confidence=metadata.get("confidence", 0.5),
            custom=metadata.get("custom", {}),
        )
        
        # Generate embedding if needed
        if embedding is None and generate_embedding:
            embedding = await self._generate_embedding(content)
        
        # Create memory
        memory = Memory(
            content=content,
            metadata=memory_metadata,
            embedding=embedding,
            raw=metadata.get("raw"),
        )
        
        # Add to store
        memory_id = await memory_store.add_memory(memory)
        
        # Add to vector DB if embedding is available
        if embedding is not None:
            try:
                vector_db = self.get_vector_db("default")
                await vector_db.add_vector(
                    vector_id=memory_id,
                    vector=embedding,
                    metadata={
                        "memory_type": memory_type.name,
                        "source": memory_metadata.source,
                        "author": memory_metadata.author,
                        "tags": memory_metadata.tags,
                    },
                )
            except Exception as e:
                logger.warning(f"Failed to add memory to vector DB: {e}")
        
        # Trigger event
        await self._trigger_event("memory_created", {"memory_id": memory_id})
        
        logger.debug(f"Added memory {memory_id} of type {memory_type.name}")
        return memory_id
    
    async def get_memory(
        self,
        memory_id: str,
        store: Optional[str] = None,
        include_versions: bool = False,
    ) -> Optional[Memory]:
        """
        Retrieve a memory by its ID.
        
        Args:
            memory_id: The ID of the memory to retrieve
            store: Name of the store to use (default: "default")
            include_versions: Whether to include version history
            
        Returns:
            The memory if found, None otherwise
        """
        if not self._initialized:
            await self.initialize()
        
        # Get the store
        memory_store = self.get_store(store or "default")
        
        # Get the memory
        memory = await memory_store.get_memory(memory_id)
        
        if memory is None:
            return None
        
        # Include version history if requested
        if include_versions:
            versions = await self._version_manager.get_versions(memory_id)
            memory.metadata.custom["versions"] = [
                v.to_dict() for v in versions
            ]
        
        # Trigger event
        await self._trigger_event("memory_retrieved", {"memory_id": memory_id})
        
        return memory
    
    async def get_memories(
        self,
        memory_ids: List[str],
        store: Optional[str] = None,
    ) -> Dict[str, Optional[Memory]]:
        """
        Retrieve multiple memories by their IDs.
        
        Args:
            memory_ids: List of memory IDs to retrieve
            store: Name of the store to use (default: "default")
            
        Returns:
            Dictionary mapping memory IDs to their corresponding memories
        """
        if not self._initialized:
            await self.initialize()
        
        memory_store = self.get_store(store or "default")
        return await memory_store.get_memories(memory_ids)
    
    async def update_memory(
        self,
        memory_id: str,
        content: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        store: Optional[str] = None,
        embedding: Optional[List[float]] = None,
        generate_embedding: bool = True,
    ) -> Memory:
        """
        Update an existing memory.
        
        Args:
            memory_id: The ID of the memory to update
            content: New content for the memory
            metadata: New metadata for the memory
            store: Name of the store to use (default: "default")
            embedding: Optional new embedding
            generate_embedding: Whether to generate a new embedding if content changes
            
        Returns:
            The updated memory
            
        Raises:
            MemoryNotFoundError: If the memory does not exist
        """
        if not self._initialized:
            await self.initialize()
        
        memory_store = self.get_store(store or "default")
        
        # Get the existing memory
        existing_memory = await memory_store.get_memory(memory_id)
        if not existing_memory:
            raise MemoryNotFoundError(memory_id)
        
        # Update content
        if content is not None:
            existing_memory.content = content
        
        # Update metadata
        if metadata is not None:
            for key, value in metadata.items():
                if hasattr(existing_memory.metadata, key):
                    setattr(existing_memory.metadata, key, value)
                else:
                    existing_memory.metadata.custom[key] = value
        
        # Update embedding
        if embedding is not None:
            existing_memory.embedding = embedding
        elif generate_embedding and content is not None:
            # Generate new embedding if content changed
            existing_memory.embedding = await self._generate_embedding(content)
        
        # Update in store
        updated_memory = await memory_store.update_memory(
            memory_id,
            content=existing_memory.content,
            metadata=existing_memory.metadata.to_dict(),
            embedding=existing_memory.embedding,
        )
        
        # Update in vector DB if embedding changed
        if existing_memory.embedding is not None:
            try:
                vector_db = self.get_vector_db("default")
                await vector_db.update_vector(
                    vector_id=memory_id,
                    vector=existing_memory.embedding,
                    metadata={
                        "memory_type": existing_memory.metadata.memory_type.name,
                        "source": existing_memory.metadata.source,
                        "author": existing_memory.metadata.author,
                        "tags": existing_memory.metadata.tags,
                    },
                )
            except Exception as e:
                logger.warning(f"Failed to update memory in vector DB: {e}")
        
        # Trigger event
        await self._trigger_event("memory_updated", {"memory_id": memory_id})
        
        logger.debug(f"Updated memory {memory_id}")
        return updated_memory
    
    async def delete_memory(
        self,
        memory_id: str,
        store: Optional[str] = None,
        permanent: bool = False,
    ) -> bool:
        """
        Delete a memory from the memory manager.
        
        Args:
            memory_id: The ID of the memory to delete
            store: Name of the store to use (default: "default")
            permanent: Whether to permanently delete (bypassing soft delete)
            
        Returns:
            True if the memory was deleted, False otherwise
        """
        if not self._initialized:
            await self.initialize()
        
        memory_store = self.get_store(store or "default")
        
        # Delete from vector DB
        try:
            vector_db = self.get_vector_db("default")
            await vector_db.delete_vector(memory_id)
        except Exception as e:
            logger.warning(f"Failed to delete memory from vector DB: {e}")
        
        # Delete from store
        result = await memory_store.delete_memory(memory_id)
        
        if result:
            # Trigger event
            await self._trigger_event("memory_deleted", {"memory_id": memory_id})
            logger.debug(f"Deleted memory {memory_id}")
        
        return result
    
    async def delete_memories(
        self,
        memory_ids: List[str],
        store: Optional[str] = None,
    ) -> int:
        """
        Delete multiple memories.
        
        Args:
            memory_ids: List of memory IDs to delete
            store: Name of the store to use (default: "default")
            
        Returns:
            Number of memories deleted
        """
        if not self._initialized:
            await self.initialize()
        
        memory_store = self.get_store(store or "default")
        
        # Delete from vector DB
        try:
            vector_db = self.get_vector_db("default")
            await vector_db.delete_vectors(memory_ids)
        except Exception as e:
            logger.warning(f"Failed to delete memories from vector DB: {e}")
        
        # Delete from store
        count = await memory_store.delete_memories(memory_ids)
        
        # Trigger events
        for memory_id in memory_ids:
            await self._trigger_event("memory_deleted", {"memory_id": memory_id})
        
        logger.debug(f"Deleted {count} memories")
        return count
    
    # =========================================================================
    # Search Operations
    # =========================================================================
    
    async def search_memories(
        self,
        query: Union[str, MemoryQuery],
        store: Optional[str] = None,
        use_vector_search: bool = True,
        use_text_search: bool = True,
        hybrid_search: bool = False,
    ) -> List[MemorySearchResult]:
        """
        Search for memories matching a query.
        
        Args:
            query: The search query (text or MemoryQuery object)
            store: Name of the store to use (default: "default")
            use_vector_search: Whether to use vector search
            use_text_search: Whether to use text search
            hybrid_search: Whether to combine vector and text search
            
        Returns:
            List of search results with matching memories and scores
        """
        if not self._initialized:
            await self.initialize()
        
        memory_store = self.get_store(store or "default")
        
        # Convert string query to MemoryQuery
        if isinstance(query, str):
            query = MemoryQuery(query=query)
        
        # Get results from different search methods
        results = []
        
        # Vector search
        if use_vector_search and query.query:
            try:
                # Generate embedding for the query
                query_embedding = await self._generate_embedding(query.query)
                
                # Search in vector DB
                vector_db = self.get_vector_db("default")
                vector_results = await vector_db.search(
                    query_vector=query_embedding,
                    top_k=query.limit or 10,
                    threshold=query.search_config.threshold if query.search_config else None,
                )
                
                # Convert to MemorySearchResult
                for vector_id, score, metadata in vector_results:
                    memory = await memory_store.get_memory(vector_id)
                    if memory:
                        results.append(MemorySearchResult(
                            memory=memory,
                            score=score,
                            rank=0,  # Will be updated after sorting
                            metadata={"source": "vector"},
                        ))
            except Exception as e:
                logger.warning(f"Vector search failed: {e}")
        
        # Text search
        if use_text_search:
            try:
                text_results = await memory_store.search_memories(query)
                for result in text_results:
                    # Check if this memory is already in results from vector search
                    already_in_results = any(
                        r.memory.memory_id == result.memory.memory_id
                        for r in results
                    )
                    if not already_in_results:
                        results.append(result)
                        results[-1].metadata["source"] = "text"
            except Exception as e:
                logger.warning(f"Text search failed: {e}")
        
        # Hybrid search: combine scores
        if hybrid_search and use_vector_search and use_text_search:
            # Group results by memory ID
            result_map = {}
            for result in results:
                if result.memory.memory_id not in result_map:
                    result_map[result.memory.memory_id] = []
                result_map[result.memory.memory_id].append(result)
            
            # Combine scores for each memory
            combined_results = []
            for memory_id, memory_results in result_map.items():
                # Simple average of scores
                avg_score = sum(r.score for r in memory_results) / len(memory_results)
                
                # Use the first result's memory (they're all the same memory)
                combined_results.append(MemorySearchResult(
                    memory=memory_results[0].memory,
                    score=avg_score,
                    rank=0,
                    metadata={
                        "source": "hybrid",
                        "sources": [r.metadata.get("source") for r in memory_results],
                    },
                ))
            
            results = combined_results
        
        # Sort by score (descending)
        results.sort(key=lambda x: x.score, reverse=True)
        
        # Apply limit and offset
        if query.limit is not None:
            results = results[:query.limit]
        if query.offset is not None:
            results = results[query.offset:]
        
        # Update ranks
        for i, result in enumerate(results):
            result.rank = i + 1
        
        # Trigger event
        await self._trigger_event("memory_searched", {
            "query": query.query if isinstance(query, MemoryQuery) else query,
            "results": len(results),
        })
        
        return results
    
    async def semantic_search(
        self,
        query: Union[str, List[float]],
        top_k: int = 10,
        threshold: Optional[float] = None,
        filters: Optional[Dict[str, Any]] = None,
        vector_db: Optional[str] = None,
    ) -> List[MemorySearchResult]:
        """
        Perform semantic search using vector embeddings.
        
        Args:
            query: The query (text or pre-computed embedding)
            top_k: Number of results to return
            threshold: Optional similarity threshold
            filters: Optional filters to apply
            vector_db: Name of the vector database to use (default: "default")
            
        Returns:
            List of search results with matching memories and scores
        """
        if not self._initialized:
            await self.initialize()
        
        # Get the vector DB
        vector_db_instance = self.get_vector_db(vector_db or "default")
        
        # Generate embedding if query is text
        if isinstance(query, str):
            query_embedding = await self._generate_embedding(query)
        else:
            query_embedding = query
        
        # Search in vector DB
        vector_results = await vector_db_instance.search(
            query_vector=query_embedding,
            top_k=top_k,
            threshold=threshold,
            filters=filters,
        )
        
        # Convert to MemorySearchResult
        results = []
        for vector_id, score, metadata in vector_results:
            # Get the full memory from the store
            memory = await self.get_memory(vector_id)
            if memory:
                results.append(MemorySearchResult(
                    memory=memory,
                    score=score,
                    rank=0,  # Will be updated after sorting
                    metadata={"source": "vector", **metadata},
                ))
        
        # Sort by score (descending)
        results.sort(key=lambda x: x.score, reverse=True)
        
        # Update ranks
        for i, result in enumerate(results):
            result.rank = i + 1
        
        return results
    
    # =========================================================================
    # Memory Type Operations
    # =========================================================================
    
    async def get_memories_by_type(
        self,
        memory_type: MemoryType,
        store: Optional[str] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> List[Memory]:
        """
        Get all memories of a specific type.
        
        Args:
            memory_type: The type of memories to retrieve
            store: Name of the store to use (default: "default")
            limit: Maximum number of memories to return
            offset: Offset for pagination
            
        Returns:
            List of memories of the specified type
        """
        if not self._initialized:
            await self.initialize()
        
        memory_store = self.get_store(store or "default")
        return await memory_store.list_memories(
            memory_type=memory_type,
            limit=limit,
            offset=offset,
        )
    
    async def get_memories_by_tag(
        self,
        tag: str,
        store: Optional[str] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> List[Memory]:
        """
        Get all memories with a specific tag.
        
        Args:
            tag: The tag to filter by
            store: Name of the store to use (default: "default")
            limit: Maximum number of memories to return
            offset: Offset for pagination
            
        Returns:
            List of memories with the specified tag
        """
        if not self._initialized:
            await self.initialize()
        
        memory_store = self.get_store(store or "default")
        filters = MemoryFilter(tags=[tag])
        return await memory_store.list_memories(
            filters=filters,
            limit=limit,
            offset=offset,
        )
    
    async def get_memories_by_source(
        self,
        source: str,
        store: Optional[str] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> List[Memory]:
        """
        Get all memories from a specific source.
        
        Args:
            source: The source to filter by
            store: Name of the store to use (default: "default")
            limit: Maximum number of memories to return
            offset: Offset for pagination
            
        Returns:
            List of memories from the specified source
        """
        if not self._initialized:
            await self.initialize()
        
        memory_store = self.get_store(store or "default")
        filters = MemoryFilter(source=source)
        return await memory_store.list_memories(
            filters=filters,
            limit=limit,
            offset=offset,
        )
    
    async def get_memories_by_author(
        self,
        author: str,
        store: Optional[str] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> List[Memory]:
        """
        Get all memories by a specific author.
        
        Args:
            author: The author to filter by
            store: Name of the store to use (default: "default")
            limit: Maximum number of memories to return
            offset: Offset for pagination
            
        Returns:
            List of memories by the specified author
        """
        if not self._initialized:
            await self.initialize()
        
        memory_store = self.get_store(store or "default")
        filters = MemoryFilter(author=author)
        return await memory_store.list_memories(
            filters=filters,
            limit=limit,
            offset=offset,
        )
    
    # =========================================================================
    # Versioning
    # =========================================================================
    
    async def get_versions(
        self,
        memory_id: str,
        limit: Optional[int] = None,
    ) -> List[MemoryVersion]:
        """
        Get all versions of a memory.
        
        Args:
            memory_id: The ID of the memory
            limit: Maximum number of versions to return
            
        Returns:
            List of memory versions
        """
        if not self._initialized:
            await self.initialize()
        
        return await self._version_manager.get_versions(memory_id, limit)
    
    async def get_version(
        self,
        memory_id: str,
        version: int,
    ) -> Optional[MemoryVersion]:
        """
        Get a specific version of a memory.
        
        Args:
            memory_id: The ID of the memory
            version: The version number
            
        Returns:
            The specified version of the memory, or None if not found
        """
        if not self._initialized:
            await self.initialize()
        
        return await self._version_manager.get_version(memory_id, version)
    
    async def revert_to_version(
        self,
        memory_id: str,
        version: int,
    ) -> Memory:
        """
        Revert a memory to a specific version.
        
        Args:
            memory_id: The ID of the memory
            version: The version number to revert to
            
        Returns:
            The reverted memory
            
        Raises:
            MemoryNotFoundError: If the memory or version is not found
        """
        if not self._initialized:
            await self.initialize()
        
        return await self._version_manager.revert_to_version(memory_id, version)
    
    # =========================================================================
    # Snapshots and Backups
    # =========================================================================
    
    async def create_snapshot(
        self,
        name: str = "",
        memory_ids: Optional[List[str]] = None,
        store: Optional[str] = None,
    ) -> MemorySnapshot:
        """
        Create a snapshot of memories.
        
        Args:
            name: Human-readable name for the snapshot
            memory_ids: Optional list of memory IDs to include (all if None)
            store: Name of the store to snapshot (default: "default")
            
        Returns:
            The created snapshot
        """
        if not self._initialized:
            await self.initialize()
        
        memory_store = self.get_store(store or "default")
        
        # Get all memory IDs if not specified
        if memory_ids is None:
            all_memories = await memory_store.list_memories()
            memory_ids = [m.memory_id for m in all_memories]
        
        # Create snapshot
        snapshot = MemorySnapshot(
            name=name,
            memory_ids=memory_ids,
            metadata={
                "created_at": datetime.utcnow().isoformat(),
                "store": store or "default",
            },
        )
        
        # Store snapshot
        self._snapshots[snapshot.snapshot_id] = snapshot
        
        # Trigger event
        await self._trigger_event("snapshot_created", {
            "snapshot_id": snapshot.snapshot_id,
            "name": name,
            "memory_count": len(memory_ids),
        })
        
        logger.info(f"Created snapshot {snapshot.snapshot_id} with {len(memory_ids)} memories")
        return snapshot
    
    async def get_snapshot(self, snapshot_id: str) -> Optional[MemorySnapshot]:
        """
        Get a snapshot by its ID.
        
        Args:
            snapshot_id: The ID of the snapshot
            
        Returns:
            The snapshot if found, None otherwise
        """
        return self._snapshots.get(snapshot_id)
    
    async def list_snapshots(self) -> List[MemorySnapshot]:
        """List all snapshots."""
        return list(self._snapshots.values())
    
    async def delete_snapshot(self, snapshot_id: str) -> bool:
        """
        Delete a snapshot.
        
        Args:
            snapshot_id: The ID of the snapshot to delete
            
        Returns:
            True if the snapshot was deleted, False otherwise
        """
        if snapshot_id in self._snapshots:
            del self._snapshots[snapshot_id]
            logger.info(f"Deleted snapshot {snapshot_id}")
            return True
        return False
    
    async def restore_snapshot(
        self,
        snapshot_id: str,
        store: Optional[str] = None,
    ) -> int:
        """
        Restore memories from a snapshot.
        
        Args:
            snapshot_id: The ID of the snapshot to restore
            store: Name of the store to restore to (default: "default")
            
        Returns:
            Number of memories restored
        """
        if not self._initialized:
            await self.initialize()
        
        snapshot = self._snapshots.get(snapshot_id)
        if not snapshot:
            raise MemoryError(
                message=f"Snapshot '{snapshot_id}' not found",
                code="SNAPSHOT_NOT_FOUND",
            )
        
        memory_store = self.get_store(store or "default")
        
        # Get all memories from the snapshot
        memories = await memory_store.get_memories(snapshot.memory_ids)
        
        # Restore each memory
        count = 0
        for memory_id, memory in memories.items():
            if memory:
                # Check if memory already exists
                existing = await memory_store.get_memory(memory_id)
                if not existing:
                    await memory_store.add_memory(memory)
                    count += 1
        
        # Trigger event
        await self._trigger_event("snapshot_restored", {
            "snapshot_id": snapshot_id,
            "memory_count": count,
        })
        
        logger.info(f"Restored {count} memories from snapshot {snapshot_id}")
        return count
    
    async def create_backup(
        self,
        name: str = "",
        path: Optional[Union[str, Path]] = None,
        store: Optional[str] = None,
    ) -> MemoryBackup:
        """
        Create a backup of memories.
        
        Args:
            name: Human-readable name for the backup
            path: Path to save the backup (default: ./backups/)
            store: Name of the store to backup (default: "default")
            
        Returns:
            The created backup
        """
        if not self._initialized:
            await self.initialize()
        
        memory_store = self.get_store(store or "default")
        
        # Determine backup path
        if path is None:
            backup_dir = Path("./backups/")
            backup_dir.mkdir(parents=True, exist_ok=True)
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            path = backup_dir / f"memory_backup_{timestamp}.json"
        else:
            path = Path(path)
            path.parent.mkdir(parents=True, exist_ok=True)
        
        # Get all memories
        all_memories = await memory_store.list_memories()
        
        # Save to file
        backup_data = {
            "name": name,
            "created_at": datetime.utcnow().isoformat(),
            "store": store or "default",
            "memory_count": len(all_memories),
            "memories": [m.to_dict() for m in all_memories],
        }
        
        with open(path, "w") as f:
            json.dump(backup_data, f, indent=2)
        
        # Create backup object
        backup = MemoryBackup(
            name=name,
            path=str(path),
            size=path.stat().st_size,
            memory_count=len(all_memories),
            metadata={
                "created_at": datetime.utcnow().isoformat(),
                "store": store or "default",
            },
        )
        
        # Store backup
        self._backups[backup.backup_id] = backup
        
        # Trigger event
        await self._trigger_event("backup_created", {
            "backup_id": backup.backup_id,
            "name": name,
            "path": str(path),
            "memory_count": len(all_memories),
        })
        
        logger.info(f"Created backup {backup.backup_id} with {len(all_memories)} memories")
        return backup
    
    async def get_backup(self, backup_id: str) -> Optional[MemoryBackup]:
        """
        Get a backup by its ID.
        
        Args:
            backup_id: The ID of the backup
            
        Returns:
            The backup if found, None otherwise
        """
        return self._backups.get(backup_id)
    
    async def list_backups(self) -> List[MemoryBackup]:
        """List all backups."""
        return list(self._backups.values())
    
    async def delete_backup(self, backup_id: str) -> bool:
        """
        Delete a backup.
        
        Args:
            backup_id: The ID of the backup to delete
            
        Returns:
            True if the backup was deleted, False otherwise
        """
        backup = self._backups.get(backup_id)
        if backup:
            # Delete the backup file
            backup_path = Path(backup.path)
            if backup_path.exists():
                backup_path.unlink()
            
            del self._backups[backup_id]
            logger.info(f"Deleted backup {backup_id}")
            return True
        return False
    
    async def restore_backup(
        self,
        backup_id: str,
        store: Optional[str] = None,
    ) -> int:
        """
        Restore memories from a backup.
        
        Args:
            backup_id: The ID of the backup to restore
            store: Name of the store to restore to (default: "default")
            
        Returns:
            Number of memories restored
        """
        if not self._initialized:
            await self.initialize()
        
        backup = self._backups.get(backup_id)
        if not backup:
            raise MemoryError(
                message=f"Backup '{backup_id}' not found",
                code="BACKUP_NOT_FOUND",
            )
        
        memory_store = self.get_store(store or "default")
        
        # Load backup file
        backup_path = Path(backup.path)
        if not backup_path.exists():
            raise MemoryError(
                message=f"Backup file not found: {backup.path}",
                code="BACKUP_FILE_NOT_FOUND",
            )
        
        with open(backup_path, "r") as f:
            backup_data = json.load(f)
        
        # Restore each memory
        count = 0
        for memory_dict in backup_data.get("memories", []):
            memory = Memory.from_dict(memory_dict)
            
            # Check if memory already exists
            existing = await memory_store.get_memory(memory.memory_id)
            if not existing:
                await memory_store.add_memory(memory)
                count += 1
        
        # Trigger event
        await self._trigger_event("backup_restored", {
            "backup_id": backup_id,
            "memory_count": count,
        })
        
        logger.info(f"Restored {count} memories from backup {backup_id}")
        return count
    
    # =========================================================================
    # Statistics and Monitoring
    # =========================================================================
    
    async def get_stats(self) -> MemoryStats:
        """
        Get statistics about the memory manager.
        
        Returns:
            Statistics about the memory manager
        """
        if not self._initialized:
            await self.initialize()
        
        # Get stats from all stores
        all_stats = MemoryStats()
        for store_name, store in self._stores.items():
            try:
                store_stats = await store.get_stats()
                all_stats.total_memories += store_stats.total_memories
                all_stats.by_type.update(store_stats.by_type)
                all_stats.total_size += store_stats.total_size
                all_stats.by_backend[store_name] = store_stats.by_backend
                all_stats.cache_hits += store_stats.cache_hits
                all_stats.cache_misses += store_stats.cache_misses
            except Exception as e:
                logger.warning(f"Failed to get stats from store {store_name}: {e}")
        
        # Get stats from all vector DBs
        for db_name, vector_db in self._vector_dbs.items():
            try:
                db_stats = await vector_db.get_stats()
                all_stats.by_backend[f"vector_{db_name}"] = db_stats
            except Exception as e:
                logger.warning(f"Failed to get stats from vector DB {db_name}: {e}")
        
        # Add manager-specific stats
        all_stats.by_backend["manager"] = {
            "store_count": len(self._stores),
            "vector_db_count": len(self._vector_dbs),
            "snapshot_count": len(self._snapshots),
            "backup_count": len(self._backups),
        }
        
        return all_stats
    
    async def cleanup(self) -> Dict[str, int]:
        """
        Clean up expired memories and temporary files.
        
        Returns:
            Dictionary with cleanup statistics
        """
        if not self._initialized:
            await self.initialize()
        
        stats = {
            "expired_memories": 0,
            "temp_files": 0,
        }
        
        # Clean up expired memories from all stores
        for store_name, store in self._stores.items():
            try:
                if hasattr(store, "cleanup_expired"):
                    count = await store.cleanup_expired()
                    stats["expired_memories"] += count
            except Exception as e:
                logger.warning(f"Failed to cleanup store {store_name}: {e}")
        
        # Clean up temporary files
        # (Implementation depends on specific temporary file management)
        
        # Trigger event
        await self._trigger_event("cleanup_performed", stats)
        
        logger.info(f"Cleanup performed: {stats}")
        return stats
    
    # =========================================================================
    # Event Handling
    # =========================================================================
    
    async def on(self, event_type: str, callback: Callable) -> None:
        """
        Register a callback for a specific event type.
        
        Args:
            event_type: The type of event to listen for
            callback: The callback function to call when the event occurs
        """
        self._event_callbacks.append((event_type, callback))
    
    async def off(self, event_type: str, callback: Callable) -> None:
        """
        Unregister a callback for a specific event type.
        
        Args:
            event_type: The type of event to unlisten for
            callback: The callback function to remove
        """
        self._event_callbacks = [
            (et, cb) for et, cb in self._event_callbacks
            if not (et == event_type and cb == callback)
        ]
    
    async def _trigger_event(self, event_type: str, data: Dict[str, Any]) -> None:
        """
        Trigger an event and call all registered callbacks.
        
        Args:
            event_type: The type of event
            data: Data associated with the event
        """
        for et, callback in self._event_callbacks:
            if et == event_type:
                try:
                    if asyncio.iscoroutinefunction(callback):
                        await callback(data)
                    else:
                        callback(data)
                except Exception as e:
                    logger.error(f"Error in event callback for {event_type}: {e}")
    
    # =========================================================================
    # Utility Methods
    # =========================================================================
    
    async def _generate_embedding(self, text: str) -> List[float]:
        """
        Generate an embedding for the given text.
        
        Args:
            text: The text to embed
            
        Returns:
            The embedding vector
        """
        if self._embedding_provider:
            return await self._embedding_provider.generate_embedding(text)
        else:
            # Fallback: return a dummy embedding
            logger.warning("No embedding provider configured, returning dummy embedding")
            return [0.0] * self.config.embedding.dimension
    
    def generate_memory_id(self, content: str, memory_type: MemoryType) -> str:
        """
        Generate a deterministic memory ID based on content and type.
        
        Args:
            content: The content of the memory
            memory_type: The type of the memory
            
        Returns:
            A deterministic memory ID
        """
        content_hash = hashlib.sha256(content.encode()).hexdigest()[:16]
        return f"{memory_type.name.lower()}_{content_hash}"
    
    async def import_memories(
        self,
        memories: List[Dict[str, Any]],
        store: Optional[str] = None,
    ) -> List[str]:
        """
        Import multiple memories from dictionaries.
        
        Args:
            memories: List of memory dictionaries to import
            store: Name of the store to import to (default: "default")
            
        Returns:
            List of imported memory IDs
        """
        memory_ids = []
        for memory_dict in memories:
            memory = Memory.from_dict(memory_dict)
            memory_id = await self.add_memory(
                content=memory.content,
                memory_type=memory.memory_type,
                metadata=memory.metadata.to_dict(),
                store=store,
                embedding=memory.embedding,
                generate_embedding=False,  # Embedding already provided
            )
            memory_ids.append(memory_id)
        
        return memory_ids
    
    async def export_memories(
        self,
        memory_ids: List[str],
        store: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Export multiple memories to dictionaries.
        
        Args:
            memory_ids: List of memory IDs to export
            store: Name of the store to export from (default: "default")
            
        Returns:
            List of memory dictionaries
        """
        memories = await self.get_memories(memory_ids, store)
        return [m.to_dict() for m in memories.values() if m is not None]
