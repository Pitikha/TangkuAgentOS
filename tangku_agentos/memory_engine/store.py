#!/usr/bin/env python3
"""
Memory Store for the TangkuAgentOS Memory Engine.

This module implements the main memory storage system, providing a unified
interface for storing, retrieving, and managing memories of all types.
"""

from __future__ import annotations

import asyncio
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple, Union
from uuid import uuid4

from .interfaces import IMemoryStore, IMemoryBackend
from .models import (
    Memory,
    MemoryMetadata,
    MemoryType,
    MemoryQuery,
    MemorySearchResult,
    MemoryFilter,
    MemoryStats,
    MemoryConfig,
)
from .exceptions import (
    MemoryError,
    MemoryNotFoundError,
    MemoryExistsError,
    MemoryValidationError,
    MemoryBackendError,
)

logger = logging.getLogger(__name__)


# =============================================================================
# Base Memory Store
# =============================================================================


class BaseMemoryStore(IMemoryStore):
    """
    Base class for memory store implementations.
    
    This class provides common functionality and implements the IMemoryStore
    interface. Subclasses should implement the backend-specific operations.
    """
    
    def __init__(self, backend: IMemoryBackend, config: Optional[MemoryConfig] = None):
        """
        Initialize the memory store.
        
        Args:
            backend: The storage backend to use
            config: Configuration for the memory store
        """
        self.backend = backend
        self.config = config or MemoryConfig()
        self._initialized = False
        self._lock = asyncio.Lock()
    
    async def initialize(self, config: Optional[Dict[str, Any]] = None) -> None:
        """Initialize the memory store."""
        async with self._lock:
            if self._initialized:
                return
            
            # Update config if provided
            if config:
                for key, value in config.items():
                    setattr(self.config, key, value)
            
            # Initialize the backend
            await self.backend.connect()
            
            self._initialized = True
            logger.info(f"Initialized {self.__class__.__name__} with {self.backend.backend_type} backend")
    
    async def shutdown(self) -> None:
        """Shutdown the memory store and clean up resources."""
        async with self._lock:
            if not self._initialized:
                return
            
            await self.backend.disconnect()
            self._initialized = False
            logger.info(f"Shut down {self.__class__.__name__}")
    
    async def add_memory(
        self,
        memory: Memory,
        overwrite: bool = False,
    ) -> str:
        """Add a new memory to the store."""
        if not self._initialized:
            await self.initialize()
        
        # Validate the memory
        self._validate_memory(memory)
        
        # Check if memory already exists
        if not overwrite and await self.exists(memory.memory_id):
            raise MemoryExistsError(memory.memory_id)
        
        # Convert memory to dictionary for storage
        data = self._memory_to_dict(memory)
        
        # Add to backend
        memory_id = await self.backend.create(data)
        
        logger.debug(f"Added memory {memory_id} of type {memory.memory_type.name}")
        return memory_id
    
    async def get_memory(self, memory_id: str) -> Optional[Memory]:
        """Retrieve a memory by its ID."""
        if not self._initialized:
            await self.initialize()
        
        data = await self.backend.read(memory_id)
        if not data:
            return None
        
        return self._dict_to_memory(data)
    
    async def get_memories(self, memory_ids: List[str]) -> Dict[str, Optional[Memory]]:
        """Retrieve multiple memories by their IDs."""
        if not self._initialized:
            await self.initialize()
        
        results = {}
        for memory_id in memory_ids:
            memory = await self.get_memory(memory_id)
            results[memory_id] = memory
        
        return results
    
    async def update_memory(
        self,
        memory_id: str,
        content: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        embedding: Optional[List[float]] = None,
    ) -> Memory:
        """Update an existing memory."""
        if not self._initialized:
            await self.initialize()
        
        # Get the existing memory
        existing_memory = await self.get_memory(memory_id)
        if not existing_memory:
            raise MemoryNotFoundError(memory_id)
        
        # Update the memory
        if content is not None:
            existing_memory.content = content
        if metadata is not None:
            for key, value in metadata.items():
                setattr(existing_memory.metadata, key, value)
        if embedding is not None:
            existing_memory.embedding = embedding
        
        # Validate the updated memory
        self._validate_memory(existing_memory)
        
        # Convert to dictionary for storage
        data = self._memory_to_dict(existing_memory)
        
        # Update in backend
        await self.backend.update(memory_id, data)
        
        logger.debug(f"Updated memory {memory_id}")
        return existing_memory
    
    async def delete_memory(self, memory_id: str) -> bool:
        """Delete a memory from the store."""
        if not self._initialized:
            await self.initialize()
        
        # Check if memory exists
        if not await self.exists(memory_id):
            return False
        
        # Delete from backend
        result = await self.backend.delete(memory_id)
        
        if result:
            logger.debug(f"Deleted memory {memory_id}")
        
        return result
    
    async def delete_memories(self, memory_ids: List[str]) -> int:
        """Delete multiple memories from the store."""
        if not self._initialized:
            await self.initialize()
        
        count = 0
        for memory_id in memory_ids:
            if await self.delete_memory(memory_id):
                count += 1
        
        logger.debug(f"Deleted {count} memories")
        return count
    
    async def search_memories(
        self,
        query: Union[str, MemoryQuery],
    ) -> List[MemorySearchResult]:
        """Search for memories matching a query."""
        if not self._initialized:
            await self.initialize()
        
        # Convert string query to MemoryQuery
        if isinstance(query, str):
            query = MemoryQuery(query=query)
        
        # Build backend query
        backend_query = self._build_backend_query(query)
        
        # Execute query
        results = await self.backend.query(
            backend_query,
            limit=query.limit,
            offset=query.offset,
        )
        
        # Convert results to MemorySearchResult
        search_results = []
        for i, data in enumerate(results):
            memory = self._dict_to_memory(data)
            score = self._calculate_score(memory, query)
            search_results.append(MemorySearchResult(
                memory=memory,
                score=score,
                rank=i + 1,
                metadata={"backend": self.backend.backend_type},
            ))
        
        # Sort by score (descending)
        search_results.sort(key=lambda x: x.score, reverse=True)
        
        return search_results
    
    async def list_memories(
        self,
        memory_type: Optional[MemoryType] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
        filters: Optional[MemoryFilter] = None,
    ) -> List[Memory]:
        """List memories with optional filtering."""
        if not self._initialized:
            await self.initialize()
        
        # Build backend query
        backend_query = {}
        if memory_type:
            backend_query["memory_type"] = memory_type.name
        
        if filters:
            if filters.memory_type:
                backend_query["memory_type"] = filters.memory_type.name
            if filters.tags:
                backend_query["tags"] = filters.tags[0]  # Simple implementation
            if filters.source:
                backend_query["source"] = filters.source
            if filters.author:
                backend_query["author"] = filters.author
            if filters.min_importance is not None:
                backend_query["min_importance"] = filters.min_importance
            if filters.max_importance is not None:
                backend_query["max_importance"] = filters.max_importance
        
        # Execute query
        results = await self.backend.query(
            backend_query,
            limit=limit,
            offset=offset,
        )
        
        # Convert results to Memory objects
        return [self._dict_to_memory(data) for data in results]
    
    async def count_memories(
        self,
        memory_type: Optional[MemoryType] = None,
        filters: Optional[MemoryFilter] = None,
    ) -> int:
        """Count memories matching the given criteria."""
        if not self._initialized:
            await self.initialize()
        
        # Build backend query
        backend_query = {}
        if memory_type:
            backend_query["memory_type"] = memory_type.name
        
        if filters:
            if filters.memory_type:
                backend_query["memory_type"] = filters.memory_type.name
            if filters.tags:
                backend_query["tags"] = filters.tags[0]  # Simple implementation
        
        return await self.backend.count(backend_query)
    
    async def exists(self, memory_id: str) -> bool:
        """Check if a memory exists in the store."""
        if not self._initialized:
            await self.initialize()
        
        data = await self.backend.read(memory_id)
        return data is not None
    
    async def get_stats(self) -> MemoryStats:
        """Get statistics about the memory store."""
        if not self._initialized:
            await self.initialize()
        
        # Count memories by type
        by_type = {}
        for memory_type in MemoryType:
            count = await self.count_memories(memory_type=memory_type)
            by_type[memory_type] = count
        
        # Get total count
        total_memories = sum(by_type.values())
        
        # Get backend-specific stats
        backend_stats = await self.backend.get_stats() if hasattr(self.backend, "get_stats") else {}
        
        return MemoryStats(
            total_memories=total_memories,
            by_type=by_type,
            by_backend={self.backend.backend_type: backend_stats},
        )
    
    def _validate_memory(self, memory: Memory) -> None:
        """Validate a memory before storage."""
        if not memory.content:
            raise MemoryValidationError(
                field="content",
                value=memory.content,
                expected="non-empty string",
            )
        
        if not isinstance(memory.metadata, MemoryMetadata):
            raise MemoryValidationError(
                field="metadata",
                value=type(memory.metadata),
                expected="MemoryMetadata",
            )
        
        if memory.embedding is not None:
            if not isinstance(memory.embedding, list):
                raise MemoryValidationError(
                    field="embedding",
                    value=type(memory.embedding),
                    expected="list of floats",
                )
            if len(memory.embedding) == 0:
                raise MemoryValidationError(
                    field="embedding",
                    value=memory.embedding,
                    expected="non-empty list",
                )
    
    def _memory_to_dict(self, memory: Memory) -> Dict[str, Any]:
        """Convert a Memory object to a dictionary for storage."""
        data = {
            "memory_id": memory.memory_id,
            "content": memory.content,
            "memory_type": memory.memory_type.name,
            "created_at": memory.metadata.created_at.isoformat(),
            "updated_at": memory.metadata.updated_at.isoformat(),
        }
        
        # Add optional fields
        if memory.metadata.expires_at:
            data["expires_at"] = memory.metadata.expires_at.isoformat()
        if memory.metadata.tags:
            data["tags"] = memory.metadata.tags
        if memory.metadata.source:
            data["source"] = memory.metadata.source
        if memory.metadata.author:
            data["author"] = memory.metadata.author
        if memory.metadata.importance != 0.5:
            data["importance"] = memory.metadata.importance
        if memory.metadata.confidence != 0.5:
            data["confidence"] = memory.metadata.confidence
        if memory.metadata.version != 1:
            data["version"] = memory.metadata.version
        if memory.metadata.parent_id:
            data["parent_id"] = memory.metadata.parent_id
        if memory.metadata.references:
            data["references"] = memory.metadata.references
        if memory.metadata.permissions:
            data["permissions"] = memory.metadata.permissions
        if memory.metadata.custom:
            data["custom"] = memory.metadata.custom
        if memory.embedding:
            data["embedding"] = memory.embedding
        if memory.raw:
            data["raw"] = memory.raw
        
        return data
    
    def _dict_to_memory(self, data: Dict[str, Any]) -> Memory:
        """Convert a dictionary from storage to a Memory object."""
        # Create metadata
        metadata = MemoryMetadata(
            memory_id=data["memory_id"],
            memory_type=MemoryType[data["memory_type"]],
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"]),
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
        
        # Create memory
        memory = Memory(
            content=data["content"],
            metadata=metadata,
            embedding=data.get("embedding"),
            raw=data.get("raw"),
        )
        
        return memory
    
    def _build_backend_query(self, query: MemoryQuery) -> Dict[str, Any]:
        """Build a backend query from a MemoryQuery."""
        backend_query = {}
        
        # Add text query (for full-text search if supported)
        if query.query:
            backend_query["query"] = query.query
        
        # Add filters
        if query.filters:
            if query.filters.memory_type:
                backend_query["memory_type"] = query.filters.memory_type.name
            if query.filters.tags:
                backend_query["tags"] = query.filters.tags[0]  # Simple implementation
            if query.filters.source:
                backend_query["source"] = query.filters.source
            if query.filters.author:
                backend_query["author"] = query.filters.author
            if query.filters.min_importance is not None:
                backend_query["min_importance"] = query.filters.min_importance
            if query.filters.max_importance is not None:
                backend_query["max_importance"] = query.filters.max_importance
        
        return backend_query
    
    def _calculate_score(self, memory: Memory, query: MemoryQuery) -> float:
        """Calculate a relevance score for a memory given a query."""
        # Simple implementation: return importance as score
        # In a real implementation, this would use embeddings and similarity
        return memory.metadata.importance


# =============================================================================
# Main Memory Store
# =============================================================================


class MemoryStore(BaseMemoryStore):
    """
    Main memory store implementation for the Memory Engine.
    
    This class provides a unified interface for storing and managing memories
    of all types. It supports:
    - All memory types (short-term, long-term, working, etc.)
    - Multiple storage backends
    - Memory versioning
    - Memory expiration (TTL)
    - Memory search and filtering
    - Batch operations
    
    Example:
        ```python
        from tangku_agentos.memory_engine import MemoryStore, SQLiteBackend
        
        # Create a store with SQLite backend
        backend = SQLiteBackend("memories.db")
        store = MemoryStore(backend)
        
        # Initialize the store
        await store.initialize()
        
        # Add a memory
        from tangku_agentos.memory_engine import Memory, MemoryMetadata, MemoryType
        memory = Memory(
            content="Hello, world!",
            metadata=MemoryMetadata(
                memory_type=MemoryType.WORKING,
                source="user",
            ),
        )
        memory_id = await store.add_memory(memory)
        
        # Retrieve the memory
        retrieved = await store.get_memory(memory_id)
        print(retrieved.content)
        
        # Shutdown the store
        await store.shutdown()
        ```
    """
    
    def __init__(
        self,
        backend: Optional[IMemoryBackend] = None,
        config: Optional[MemoryConfig] = None,
    ):
        """
        Initialize the memory store.
        
        Args:
            backend: The storage backend to use. If None, uses SQLite in-memory.
            config: Configuration for the memory store
        """
        if backend is None:
            from .backend import SQLiteBackend
            backend = SQLiteBackend(":memory:")
        
        super().__init__(backend, config)
        self._versioning_enabled = config.versioning if config else True
        self._ttl_enabled = True
    
    async def add_memory(
        self,
        memory: Memory,
        overwrite: bool = False,
    ) -> str:
        """Add a new memory to the store."""
        # Set expiration if TTL is configured
        if self._ttl_enabled and self.config.ttl:
            memory.metadata.expires_at = datetime.utcnow() + timedelta(
                seconds=self.config.ttl
            )
        
        return await super().add_memory(memory, overwrite)
    
    async def get_memory(self, memory_id: str) -> Optional[Memory]:
        """Retrieve a memory by its ID."""
        memory = await super().get_memory(memory_id)
        
        # Check if memory has expired
        if memory and memory.metadata.expires_at:
            if datetime.utcnow() > memory.metadata.expires_at:
                # Memory has expired, delete it and return None
                await self.delete_memory(memory_id)
                return None
        
        return memory
    
    async def update_memory(
        self,
        memory_id: str,
        content: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        embedding: Optional[List[float]] = None,
    ) -> Memory:
        """Update an existing memory."""
        # Handle versioning
        if self._versioning_enabled:
            existing_memory = await self.get_memory(memory_id)
            if existing_memory:
                # Create a new version
                new_version = existing_memory.metadata.version + 1
                metadata = metadata or {}
                metadata["version"] = new_version
                metadata["parent_id"] = memory_id
        
        return await super().update_memory(
            memory_id, content, metadata, embedding
        )
    
    async def search_memories(
        self,
        query: Union[str, MemoryQuery],
    ) -> List[MemorySearchResult]:
        """Search for memories matching a query."""
        # Convert string query to MemoryQuery if needed
        if isinstance(query, str):
            query = MemoryQuery(query=query)
        
        # Use the parent implementation
        results = await super().search_memories(query)
        
        # Filter out expired memories
        now = datetime.utcnow()
        results = [
            result for result in results
            if not result.memory.metadata.expires_at or result.memory.metadata.expires_at > now
        ]
        
        return results
    
    async def list_memories(
        self,
        memory_type: Optional[MemoryType] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
        filters: Optional[MemoryFilter] = None,
    ) -> List[Memory]:
        """List memories with optional filtering."""
        # Use the parent implementation
        memories = await super().list_memories(
            memory_type, limit, offset, filters
        )
        
        # Filter out expired memories
        now = datetime.utcnow()
        memories = [
            memory for memory in memories
            if not memory.metadata.expires_at or memory.metadata.expires_at > now
        ]
        
        return memories
    
    async def get_stats(self) -> MemoryStats:
        """Get statistics about the memory store."""
        stats = await super().get_stats()
        
        # Add TTL information
        stats.by_backend[self.backend.backend_type]["ttl_enabled"] = self._ttl_enabled
        stats.by_backend[self.backend.backend_type]["versioning_enabled"] = self._versioning_enabled
        
        return stats
    
    async def cleanup_expired(self) -> int:
        """
        Remove all expired memories from the store.
        
        Returns:
            Number of memories removed
        """
        if not self._ttl_enabled:
            return 0
        
        # Get all memories
        all_memories = await self.list_memories()
        
        # Find expired memories
        now = datetime.utcnow()
        expired_ids = [
            memory.memory_id for memory in all_memories
            if memory.metadata.expires_at and memory.metadata.expires_at <= now
        ]
        
        # Delete expired memories
        if expired_ids:
            count = await self.delete_memories(expired_ids)
            logger.info(f"Cleaned up {count} expired memories")
            return count
        
        return 0
    
    async def get_by_type(self, memory_type: MemoryType) -> List[Memory]:
        """
        Get all memories of a specific type.
        
        Args:
            memory_type: The type of memories to retrieve
            
        Returns:
            List of memories of the specified type
        """
        return await self.list_memories(memory_type=memory_type)
    
    async def get_by_tag(self, tag: str) -> List[Memory]:
        """
        Get all memories with a specific tag.
        
        Args:
            tag: The tag to filter by
            
        Returns:
            List of memories with the specified tag
        """
        filters = MemoryFilter(tags=[tag])
        return await self.list_memories(filters=filters)
    
    async def get_by_source(self, source: str) -> List[Memory]:
        """
        Get all memories from a specific source.
        
        Args:
            source: The source to filter by
            
        Returns:
            List of memories from the specified source
        """
        filters = MemoryFilter(source=source)
        return await self.list_memories(filters=filters)
    
    async def get_by_author(self, author: str) -> List[Memory]:
        """
        Get all memories by a specific author.
        
        Args:
            author: The author to filter by
            
        Returns:
            List of memories by the specified author
        """
        filters = MemoryFilter(author=author)
        return await self.list_memories(filters=filters)
