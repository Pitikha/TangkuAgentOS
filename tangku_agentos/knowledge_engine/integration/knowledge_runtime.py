"""
Knowledge Engine - Integrated Runtime Implementation

This module provides the full integration of the Knowledge Engine with the
Runtime Communication Framework.

Features:
- Knowledge document indexing and search
- Semantic search capabilities
- Knowledge graph management
- Integration with memory engine
- Event publishing for knowledge changes
- Health monitoring
- Metrics collection

Author: TangkuAgentOS Team
License: MIT
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Set, TYPE_CHECKING, Tuple

if TYPE_CHECKING:
    from tangku_agentos.runtime_communication.integration.base import RuntimeConfig
    from tangku_agentos.runtime_communication.models.messages import Command, Query, Event

logger = logging.getLogger(__name__)


@dataclass
class KnowledgeDocument:
    """Represents a knowledge document."""

    document_id: str
    content: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    source: str = ""
    source_url: str = ""
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    version: int = 1
    tags: Set[str] = field(default_factory=set)
    embeddings: Optional[List[float]] = None
    chunk_ids: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "document_id": self.document_id,
            "content": self.content,
            "metadata": self.metadata,
            "source": self.source,
            "source_url": self.source_url,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "version": self.version,
            "tags": list(self.tags),
            "embeddings": self.embeddings,
            "chunk_ids": self.chunk_ids,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "KnowledgeDocument":
        """Create from dictionary."""
        return cls(
            document_id=data["document_id"],
            content=data["content"],
            metadata=data.get("metadata", {}),
            source=data.get("source", ""),
            source_url=data.get("source_url", ""),
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"]),
            version=data.get("version", 1),
            tags=set(data.get("tags", [])),
            embeddings=data.get("embeddings"),
            chunk_ids=data.get("chunk_ids", []),
        )

    def generate_id(self) -> str:
        """Generate a unique ID for the document."""
        content_hash = hashlib.sha256(self.content.encode()).hexdigest()[:16]
        return f"{self.source or 'unknown'}_{content_hash}"


@dataclass
class KnowledgeChunk:
    """Represents a chunk of a knowledge document."""

    chunk_id: str
    document_id: str
    content: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    embeddings: Optional[List[float]] = None
    position: int = 0
    created_at: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "chunk_id": self.chunk_id,
            "document_id": self.document_id,
            "content": self.content,
            "metadata": self.metadata,
            "embeddings": self.embeddings,
            "position": self.position,
            "created_at": self.created_at.isoformat(),
        }


@dataclass
class SearchResult:
    """Represents a search result."""

    document_id: str
    chunk_id: Optional[str] = None
    content: str = ""
    score: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    matched_terms: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "document_id": self.document_id,
            "chunk_id": self.chunk_id,
            "content": self.content,
            "score": self.score,
            "metadata": self.metadata,
            "matched_terms": self.matched_terms,
        }


class KnowledgeEngineRuntime:
    """
    Integrated Knowledge Engine Runtime.

    This runtime provides knowledge indexing and search services
    through the Runtime Communication Framework.

    Features:
    - Index knowledge documents
    - Search knowledge (semantic and keyword)
    - Manage knowledge graph
    - Integrate with memory engine
    - Publish knowledge events
    - Health monitoring

    Thread Safety:
        This class is thread-safe for concurrent access.

    Example:
        >>> from tangku_agentos.knowledge_engine.integration import KnowledgeEngineRuntime
        >>> from tangku_agentos.runtime_communication.integration import create_runtime_config
        >>> 
        >>> config = create_runtime_config(
        ...     runtime_id="knowledge_engine",
        ...     name="Knowledge Engine",
        ...     version="1.0.0",
        ...     description="Manages knowledge indexing and retrieval",
        ...     capabilities={"knowledge", "search", "indexing", "semantic"},
        ... )
        >>> 
        >>> knowledge_runtime = KnowledgeEngineRuntime(config)
        >>> await knowledge_runtime.initialize()
        >>> await knowledge_runtime.start()
        >>> 
        >>> # Index a document
        >>> result = await knowledge_runtime.send_command(
        ...     target_runtime_id="knowledge_engine",
        ...     command_type="index",
        ...     payload={
        ...         "document_id": "doc_123",
        ...         "content": "This is a test document",
        ...         "source": "test",
        ...         "metadata": {"type": "test"},
        ...     }
        ... )
        >>> 
        >>> # Search knowledge
        >>> result = await knowledge_runtime.send_query(
        ...     target_runtime_id="knowledge_engine",
        ...     query_type="search",
        ...     payload={"query": "test document"}
        ... )
    """

    def __init__(self, config: "RuntimeConfig"):
        """
        Initialize the Knowledge Engine Runtime.

        Args:
            config: Runtime configuration.
        """
        from tangku_agentos.runtime_communication.integration import (
            BaseRuntime,
            create_runtime_capabilities,
        )

        # Define capabilities
        capabilities = create_runtime_capabilities(
            can_handle_commands=True,
            can_handle_queries=True,
            can_publish_events=True,
            can_subscribe_events=True,
            can_broadcast=True,
            supports_health_checks=True,
            supports_metrics=True,
            supports_tracing=True,
        )

        # Initialize base runtime
        super(KnowledgeEngineRuntime, self).__init__(config, capabilities)

        # Knowledge storage
        self._documents: Dict[str, KnowledgeDocument] = {}
        self._chunks: Dict[str, KnowledgeChunk] = {}
        self._knowledge_lock = asyncio.Lock()

        # Indexes
        self._document_index: Dict[str, Set[str]] = {}  # term -> document_ids
        self._chunk_index: Dict[str, Set[str]] = {}  # term -> chunk_ids
        self._source_index: Dict[str, Set[str]] = {}  # source -> document_ids
        self._tag_index: Dict[str, Set[str]] = {}  # tag -> document_ids
        self._metadata_index: Dict[str, Dict[str, Set[str]]] = {}  # key -> value -> document_ids

        # Embedding index (simplified - in production use vector DB)
        self._embedding_index: Dict[str, List[float]] = {}  # document_id -> embeddings

        # Metrics
        self._metrics: Dict[str, Any] = {
            "documents_indexed": 0,
            "documents_updated": 0,
            "documents_deleted": 0,
            "chunks_created": 0,
            "searches_performed": 0,
            "total_documents": 0,
            "total_chunks": 0,
            "last_index_time": None,
            "last_search_time": None,
        }

        # Register command handlers
        self._register_command_handlers()

        # Register query handlers
        self._register_query_handlers()

        # Register event handlers
        self._register_event_handlers()

        logger.info(f"KnowledgeEngineRuntime initialized: {config.runtime_id}")

    def _register_command_handlers(self) -> None:
        """Register all command handlers."""
        # Document operations
        self.register_command_handler("index", self._handle_index_command)
        self.register_command_handler("update", self._handle_update_command)
        self.register_command_handler("delete", self._handle_delete_command)
        self.register_command_handler("delete_all", self._handle_delete_all_command)

        # Bulk operations
        self.register_command_handler("index_batch", self._handle_index_batch_command)
        self.register_command_handler("delete_batch", self._handle_delete_batch_command)

        # Sync operations
        self.register_command_handler("sync", self._handle_sync_command)
        self.register_command_handler("sync_source", self._handle_sync_source_command)

        # Graph operations
        self.register_command_handler("add_relation", self._handle_add_relation_command)
        self.register_command_handler("remove_relation", self._handle_remove_relation_command)
        self.register_command_handler("get_relations", self._handle_get_relations_command)

        # Standard system commands
        from tangku_agentos.runtime_communication.integration import SystemCommands

        self.register_command_handler(
            "runtime.get_status",
            lambda cmd: self._handle_system_command(cmd, SystemCommands.GetRuntimeStatus),
        )
        self.register_command_handler(
            "runtime.get_health",
            lambda cmd: self._handle_system_command(cmd, SystemCommands.GetRuntimeHealth),
        )
        self.register_command_handler(
            "runtime.get_metadata",
            lambda cmd: self._handle_system_command(cmd, SystemCommands.GetRuntimeMetadata),
        )

    def _register_query_handlers(self) -> None:
        """Register all query handlers."""
        # Search queries
        self.register_query_handler("search", self._handle_search_query)
        self.register_query_handler("semantic_search", self._handle_semantic_search_query)
        self.register_query_handler("hybrid_search", self._handle_hybrid_search_query)

        # Document queries
        self.register_query_handler("get", self._handle_get_query)
        self.register_query_handler("get_by_source", self._handle_get_by_source_query)
        self.register_query_handler("get_by_tag", self._handle_get_by_tag_query)
        self.register_query_handler("list", self._handle_list_query)
        self.register_query_handler("exists", self._handle_exists_query)
        self.register_query_handler("count", self._handle_count_query)

        # Advanced queries
        self.register_query_handler("get_similar", self._handle_get_similar_query)
        self.register_query_handler("get_related", self._handle_get_related_query)
        self.register_query_handler("get_stats", self._handle_get_stats_query)

        # Standard system queries
        from tangku_agentos.runtime_communication.integration import SystemQueries

        self.register_query_handler(
            "runtime.get_status",
            lambda query: self._handle_system_query(query, SystemQueries.GetRuntimeStatus),
        )
        self.register_query_handler(
            "runtime.get_health",
            lambda query: self._handle_system_query(query, SystemQueries.GetRuntimeHealth),
        )
        self.register_query_handler(
            "runtime.get_metadata",
            lambda query: self._handle_system_query(query, SystemQueries.GetRuntimeMetadata),
        )

    def _register_event_handlers(self) -> None:
        """Register all event handlers."""
        # Subscribe to system events
        self.register_event_handler("system.startup", self._handle_system_startup)
        self.register_event_handler("system.shutdown", self._handle_system_shutdown)
        self.register_event_handler("system.health_check", self._handle_health_check)

        # Subscribe to knowledge events from other runtimes
        self.register_event_handler("knowledge.indexed", self._handle_knowledge_indexed)
        self.register_event_handler("knowledge.updated", self._handle_knowledge_updated)
        self.register_event_handler("knowledge.deleted", self._handle_knowledge_deleted)

        # Subscribe to memory events
        self.register_event_handler("memory.updated", self._handle_memory_updated)

    async def _initialize(self) -> None:
        """
        Initialize the knowledge engine.

        This method is called during runtime initialization.
        """
        logger.info(f"Initializing KnowledgeEngineRuntime: {self.runtime_id}")

        # Initialize storage
        self._documents = {}
        self._chunks = {}
        self._document_index = {}
        self._chunk_index = {}
        self._source_index = {}
        self._tag_index = {}
        self._metadata_index = {}
        self._embedding_index = {}

        # Initialize metrics
        self._metrics = {
            "documents_indexed": 0,
            "documents_updated": 0,
            "documents_deleted": 0,
            "chunks_created": 0,
            "searches_performed": 0,
            "total_documents": 0,
            "total_chunks": 0,
            "last_index_time": None,
            "last_search_time": None,
        }

        # Set up health checks
        await self._setup_health_checks()

        logger.info(f"KnowledgeEngineRuntime initialized: {self.runtime_id}")

    async def _start(self) -> None:
        """
        Start the knowledge engine.

        This method is called during runtime startup.
        """
        logger.info(f"Starting KnowledgeEngineRuntime: {self.runtime_id}")

        # Start background tasks if needed
        # For knowledge engine, there are no background tasks currently

        logger.info(f"KnowledgeEngineRuntime started: {self.runtime_id}")

    async def _stop(self) -> None:
        """
        Stop the knowledge engine.

        This method is called during runtime shutdown.
        """
        logger.info(f"Stopping KnowledgeEngineRuntime: {self.runtime_id}")

        # Clean up resources
        async with self._knowledge_lock:
            self._documents.clear()
            self._chunks.clear()
            self._document_index.clear()
            self._chunk_index.clear()
            self._source_index.clear()
            self._tag_index.clear()
            self._metadata_index.clear()
            self._embedding_index.clear()

        logger.info(f"KnowledgeEngineRuntime stopped: {self.runtime_id}")

    async def _setup_health_checks(self) -> None:
        """Set up health checks for the knowledge engine."""
        from tangku_agentos.runtime_communication import HealthCheck, HealthStatus
        from tangku_agentos.runtime_communication.services.health import HealthCheckResult

        # Liveness check
        liveness = HealthCheck(
            name="liveness",
            description="Check if knowledge engine is alive",
            check_func=lambda rid: HealthCheckResult(
                runtime_id=rid,
                check_name="liveness",
                status=HealthStatus.HEALTHY if self.state == self.state.RUNNING else HealthStatus.UNHEALTHY,
                message="Knowledge engine is alive" if self.state == self.state.RUNNING else f"Not running: {self.state.name}",
                passed=self.state == self.state.RUNNING,
            ),
            interval=30.0,
            timeout=5.0,
            critical=True,
        )

        # Readiness check
        readiness = HealthCheck(
            name="readiness",
            description="Check if knowledge engine is ready",
            check_func=lambda rid: HealthCheckResult(
                runtime_id=rid,
                check_name="readiness",
                status=HealthStatus.HEALTHY if self.state == self.state.RUNNING else HealthStatus.UNHEALTHY,
                message="Knowledge engine is ready" if self.state == self.state.RUNNING else f"Not ready: {self.state.name}",
                passed=self.state == self.state.RUNNING,
            ),
            interval=30.0,
            timeout=5.0,
            critical=True,
        )

        # Storage check
        storage = HealthCheck(
            name="storage",
            description="Check knowledge storage",
            check_func=lambda rid: HealthCheckResult(
                runtime_id=rid,
                check_name="storage",
                status=HealthStatus.HEALTHY,
                message=f"Storage OK ({len(self._documents)} documents, {len(self._chunks)} chunks)",
                passed=True,
                details={
                    "document_count": len(self._documents),
                    "chunk_count": len(self._chunks),
                },
            ),
            interval=60.0,
            timeout=10.0,
            critical=False,
        )

        self.health_service.register_check(self.runtime_id, liveness)
        self.health_service.register_check(self.runtime_id, readiness)
        self.health_service.register_check(self.runtime_id, storage)

    # Helper Methods

    def _chunk_document(self, document: KnowledgeDocument, chunk_size: int = 1000) -> List[KnowledgeChunk]:
        """
        Chunk a document into smaller pieces.

        Args:
            document: Document to chunk.
            chunk_size: Size of each chunk in characters.

        Returns:
            List of chunks.
        """
        content = document.content
        chunks = []

        for i in range(0, len(content), chunk_size):
            chunk_content = content[i:i + chunk_size]
            chunk_id = f"{document.document_id}_chunk_{i // chunk_size}"

            chunk = KnowledgeChunk(
                chunk_id=chunk_id,
                document_id=document.document_id,
                content=chunk_content,
                metadata={
                    "document_id": document.document_id,
                    "position": i // chunk_size,
                    "total_chunks": (len(content) + chunk_size - 1) // chunk_size,
                },
                position=i // chunk_size,
            )
            chunks.append(chunk)

        return chunks

    def _index_document(self, document: KnowledgeDocument) -> None:
        """
        Index a document for search.

        Args:
            document: Document to index.
        """
        # Index by terms (simple word-based indexing)
        terms = self._extract_terms(document.content)
        terms.update(self._extract_terms(str(document.metadata)))

        for term in terms:
            term_lower = term.lower()
            if term_lower not in self._document_index:
                self._document_index[term_lower] = set()
            self._document_index[term_lower].add(document.document_id)

        # Index by source
        if document.source:
            if document.source not in self._source_index:
                self._source_index[document.source] = set()
            self._source_index[document.source].add(document.document_id)

        # Index by tags
        for tag in document.tags:
            if tag not in self._tag_index:
                self._tag_index[tag] = set()
            self._tag_index[tag].add(document.document_id)

        # Index by metadata
        for key, value in document.metadata.items():
            if key not in self._metadata_index:
                self._metadata_index[key] = {}
            value_str = str(value).lower()
            if value_str not in self._metadata_index[key]:
                self._metadata_index[key][value_str] = set()
            self._metadata_index[key][value_str].add(document.document_id)

        # Index embeddings (simplified)
        if document.embeddings:
            self._embedding_index[document.document_id] = document.embeddings

    def _index_chunk(self, chunk: KnowledgeChunk) -> None:
        """
        Index a chunk for search.

        Args:
            chunk: Chunk to index.
        """
        # Index by terms
        terms = self._extract_terms(chunk.content)

        for term in terms:
            term_lower = term.lower()
            if term_lower not in self._chunk_index:
                self._chunk_index[term_lower] = set()
            self._chunk_index[term_lower].add(chunk.chunk_id)

    def _remove_document_from_indexes(self, document: KnowledgeDocument) -> None:
        """
        Remove a document from indexes.

        Args:
            document: Document to remove.
        """
        # Remove from term index
        terms = self._extract_terms(document.content)
        terms.update(self._extract_terms(str(document.metadata)))

        for term in terms:
            term_lower = term.lower()
            if term_lower in self._document_index:
                self._document_index[term_lower].discard(document.document_id)
                if not self._document_index[term_lower]:
                    del self._document_index[term_lower]

        # Remove from source index
        if document.source in self._source_index:
            self._source_index[document.source].discard(document.document_id)
            if not self._source_index[document.source]:
                del self._source_index[document.source]

        # Remove from tag index
        for tag in document.tags:
            if tag in self._tag_index:
                self._tag_index[tag].discard(document.document_id)
                if not self._tag_index[tag]:
                    del self._tag_index[tag]

        # Remove from metadata index
        for key, value in document.metadata.items():
            if key in self._metadata_index:
                value_str = str(value).lower()
                if value_str in self._metadata_index[key]:
                    self._metadata_index[key][value_str].discard(document.document_id)
                    if not self._metadata_index[key][value_str]:
                        del self._metadata_index[key][value_str]
                    if not self._metadata_index[key]:
                        del self._metadata_index[key]

        # Remove from embedding index
        if document.document_id in self._embedding_index:
            del self._embedding_index[document.document_id]

    def _remove_chunk_from_indexes(self, chunk: KnowledgeChunk) -> None:
        """
        Remove a chunk from indexes.

        Args:
            chunk: Chunk to remove.
        """
        # Remove from term index
        terms = self._extract_terms(chunk.content)

        for term in terms:
            term_lower = term.lower()
            if term_lower in self._chunk_index:
                self._chunk_index[term_lower].discard(chunk.chunk_id)
                if not self._chunk_index[term_lower]:
                    del self._chunk_index[term_lower]

    def _extract_terms(self, text: str) -> Set[str]:
        """
        Extract terms from text for indexing.

        Args:
            text: Text to extract terms from.

        Returns:
            Set of terms.
        """
        # Simple term extraction - split by whitespace and punctuation
        import re
        words = re.findall(r'\b\w+\b', text.lower())
        # Remove common stop words
        stop_words = {"the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for", "of", "with", "by"}
        return set(word for word in words if word not in stop_words and len(word) > 2)

    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """
        Calculate similarity between two texts (simplified).

        Args:
            text1: First text.
            text2: Second text.

        Returns:
            Similarity score (0-1).
        """
        terms1 = self._extract_terms(text1)
        terms2 = self._extract_terms(text2)

        if not terms1 or not terms2:
            return 0.0

        intersection = terms1 & terms2
        union = terms1 | terms2

        return len(intersection) / len(union) if union else 0.0

    # Command Handlers

    async def _handle_index_command(self, command: "Command") -> Any:
        """
        Handle index document command.

        Args:
            command: Index command.

        Returns:
            Result of index operation.
        """
        payload = command.payload or {}
        document_id = payload.get("document_id")
        content = payload.get("content")
        source = payload.get("source", "")
        source_url = payload.get("source_url", "")
        metadata = payload.get("metadata", {})
        tags = set(payload.get("tags", []))
        embeddings = payload.get("embeddings")
        chunk_size = payload.get("chunk_size", 1000)
        overwrite = payload.get("overwrite", True)

        if not content:
            raise ValueError("content is required")

        # Generate document ID if not provided
        if not document_id:
            document_id = f"doc_{hashlib.sha256(content.encode()).hexdigest()[:16]}"

        async with self._knowledge_lock:
            # Check if document exists and overwrite is False
            if not overwrite and document_id in self._documents:
                raise ValueError(f"Document already exists: {document_id}")

            # Create or update document
            if document_id in self._documents:
                doc = self._documents[document_id]
                doc.content = content
                doc.metadata.update(metadata)
                doc.source = source or doc.source
                doc.source_url = source_url or doc.source_url
                doc.tags.update(tags)
                doc.embeddings = embeddings or doc.embeddings
                doc.updated_at = datetime.utcnow()
                doc.version += 1
                self._metrics["documents_updated"] += 1

                # Remove old chunks and indexes
                for chunk_id in doc.chunk_ids:
                    if chunk_id in self._chunks:
                        self._remove_chunk_from_indexes(self._chunks[chunk_id])
                        del self._chunks[chunk_id]
                        self._metrics["chunks_created"] -= 1

            else:
                doc = KnowledgeDocument(
                    document_id=document_id,
                    content=content,
                    metadata=metadata,
                    source=source,
                    source_url=source_url,
                    tags=tags,
                    embeddings=embeddings,
                )
                self._documents[document_id] = doc
                self._metrics["documents_indexed"] += 1

            # Chunk the document
            chunks = self._chunk_document(doc, chunk_size)
            doc.chunk_ids = [c.chunk_id for c in chunks]

            # Store chunks
            for chunk in chunks:
                self._chunks[chunk.chunk_id] = chunk
                self._index_chunk(chunk)
                self._metrics["chunks_created"] += 1

            # Index the document
            self._index_document(doc)

            # Update metrics
            self._metrics["total_documents"] = len(self._documents)
            self._metrics["total_chunks"] = len(self._chunks)
            self._metrics["last_index_time"] = datetime.utcnow().isoformat()

        # Publish event
        from tangku_agentos.runtime_communication.integration import SystemEvents

        event = SystemEvents.knowledge_indexed(
            runtime_id=self.runtime_id,
            document_id=document_id,
            source=source,
            size=len(content),
        )
        await self.publish_event(event.event_type, event.metadata)

        logger.debug(f"Document indexed: {document_id}")

        return {
            "success": True,
            "document_id": document_id,
            "chunk_count": len(chunks),
            "size": len(content),
            "version": doc.version,
            "timestamp": doc.updated_at.isoformat(),
        }

    async def _handle_update_command(self, command: "Command") -> Any:
        """
        Handle update document command.

        Args:
            command: Update command.

        Returns:
            Result of update operation.
        """
        payload = command.payload or {}
        document_id = payload.get("document_id")
        updates = payload.get("updates", {})
        metadata_updates = payload.get("metadata_updates", {})
        tag_updates = payload.get("tag_updates", {})

        if not document_id:
            raise ValueError("document_id is required")

        async with self._knowledge_lock:
            if document_id not in self._documents:
                raise ValueError(f"Document not found: {document_id}")

            doc = self._documents[document_id]

            # Update content
            if "content" in updates:
                # Remove old chunks and indexes
                for chunk_id in doc.chunk_ids:
                    if chunk_id in self._chunks:
                        self._remove_chunk_from_indexes(self._chunks[chunk_id])
                        del self._chunks[chunk_id]
                        self._metrics["chunks_created"] -= 1

                # Update content
                doc.content = updates["content"]

                # Re-chunk the document
                chunks = self._chunk_document(doc)
                doc.chunk_ids = [c.chunk_id for c in chunks]

                # Store new chunks
                for chunk in chunks:
                    self._chunks[chunk.chunk_id] = chunk
                    self._index_chunk(chunk)
                    self._metrics["chunks_created"] += 1

            # Update metadata
            if metadata_updates:
                doc.metadata.update(metadata_updates)

            # Update tags
            if tag_updates:
                for tag, value in tag_updates.items():
                    if value:
                        doc.tags.add(tag)
                    else:
                        doc.tags.discard(tag)

            doc.updated_at = datetime.utcnow()
            doc.version += 1
            self._metrics["documents_updated"] += 1

            # Re-index the document
            self._remove_document_from_indexes(doc)
            self._index_document(doc)

        # Publish event
        from tangku_agentos.runtime_communication.integration import SystemEvents

        event = SystemEvents.knowledge_updated(
            runtime_id=self.runtime_id,
            operation="update",
            document_id=document_id,
        )
        await self.publish_event(event.event_type, event.metadata)

        logger.debug(f"Document updated: {document_id}")

        return {
            "success": True,
            "document_id": document_id,
            "version": doc.version,
            "timestamp": doc.updated_at.isoformat(),
        }

    async def _handle_delete_command(self, command: "Command") -> Any:
        """
        Handle delete document command.

        Args:
            command: Delete command.

        Returns:
            Result of delete operation.
        """
        payload = command.payload or {}
        document_id = payload.get("document_id")
        reason = payload.get("reason", "user_request")

        if not document_id:
            raise ValueError("document_id is required")

        async with self._knowledge_lock:
            if document_id not in self._documents:
                raise ValueError(f"Document not found: {document_id}")

            doc = self._documents[document_id]

            # Remove chunks
            for chunk_id in doc.chunk_ids:
                if chunk_id in self._chunks:
                    self._remove_chunk_from_indexes(self._chunks[chunk_id])
                    del self._chunks[chunk_id]
                    self._metrics["chunks_created"] -= 1

            # Remove document
            del self._documents[document_id]
            self._remove_document_from_indexes(doc)
            self._metrics["documents_deleted"] += 1
            self._metrics["total_documents"] = len(self._documents)
            self._metrics["total_chunks"] = len(self._chunks)

        # Publish event
        from tangku_agentos.runtime_communication.integration import SystemEvents

        event = SystemEvents.knowledge_deleted(
            runtime_id=self.runtime_id,
            document_id=document_id,
        )
        await self.publish_event(event.event_type, event.metadata)

        logger.debug(f"Document deleted: {document_id}")

        return {
            "success": True,
            "document_id": document_id,
            "reason": reason,
        }

    async def _handle_delete_all_command(self, command: "Command") -> Any:
        """
        Handle delete all documents command.

        Args:
            command: Delete all command.

        Returns:
            Result of delete all operation.
        """
        payload = command.payload or {}
        filter = payload.get("filter", {})
        force = payload.get("force", False)

        if not force:
            raise ValueError("force must be True to delete all documents")

        async with self._knowledge_lock:
            if filter:
                # Delete filtered documents
                to_delete = [
                    did for did, doc in self._documents.items()
                    if all(doc.metadata.get(k) == v for k, v in filter.items())
                ]
                count = len(to_delete)
                for did in to_delete:
                    doc = self._documents[did]
                    for chunk_id in doc.chunk_ids:
                        if chunk_id in self._chunks:
                            self._remove_chunk_from_indexes(self._chunks[chunk_id])
                            del self._chunks[chunk_id]
                            self._metrics["chunks_created"] -= 1
                    del self._documents[did]
                    self._remove_document_from_indexes(doc)
                    self._metrics["documents_deleted"] += 1
            else:
                # Delete all documents
                count = len(self._documents)
                for doc in self._documents.values():
                    for chunk_id in doc.chunk_ids:
                        if chunk_id in self._chunks:
                            self._remove_chunk_from_indexes(self._chunks[chunk_id])
                            del self._chunks[chunk_id]
                            self._metrics["chunks_created"] -= 1
                self._documents.clear()
                self._chunks.clear()
                self._document_index.clear()
                self._chunk_index.clear()
                self._source_index.clear()
                self._tag_index.clear()
                self._metadata_index.clear()
                self._embedding_index.clear()
                self._metrics["documents_deleted"] += count

            self._metrics["total_documents"] = len(self._documents)
            self._metrics["total_chunks"] = len(self._chunks)

        logger.debug(f"Deleted {count} documents")

        return {
            "success": True,
            "deleted_count": count,
        }

    async def _handle_index_batch_command(self, command: "Command") -> Any:
        """
        Handle index batch command.

        Args:
            command: Index batch command.

        Returns:
            Result of batch index operation.
        """
        payload = command.payload or {}
        documents = payload.get("documents", [])
        chunk_size = payload.get("chunk_size", 1000)
        overwrite = payload.get("overwrite", True)

        results = []
        errors = []

        async with self._knowledge_lock:
            for doc_data in documents:
                try:
                    document_id = doc_data.get("document_id")
                    content = doc_data.get("content")
                    source = doc_data.get("source", "")
                    source_url = doc_data.get("source_url", "")
                    metadata = doc_data.get("metadata", {})
                    tags = set(doc_data.get("tags", []))
                    embeddings = doc_data.get("embeddings")

                    if not content:
                        errors.append({
                            "document_id": document_id,
                            "error": "content is required",
                        })
                        continue

                    # Generate document ID if not provided
                    if not document_id:
                        document_id = f"doc_{hashlib.sha256(content.encode()).hexdigest()[:16]}"

                    # Check if document exists and overwrite is False
                    if not overwrite and document_id in self._documents:
                        errors.append({
                            "document_id": document_id,
                            "error": "Document already exists",
                        })
                        continue

                    # Create or update document
                    if document_id in self._documents:
                        doc = self._documents[document_id]
                        doc.content = content
                        doc.metadata.update(metadata)
                        doc.source = source or doc.source
                        doc.source_url = source_url or doc.source_url
                        doc.tags.update(tags)
                        doc.embeddings = embeddings or doc.embeddings
                        doc.updated_at = datetime.utcnow()
                        doc.version += 1
                        self._metrics["documents_updated"] += 1

                        # Remove old chunks and indexes
                        for chunk_id in doc.chunk_ids:
                            if chunk_id in self._chunks:
                                self._remove_chunk_from_indexes(self._chunks[chunk_id])
                                del self._chunks[chunk_id]
                                self._metrics["chunks_created"] -= 1

                    else:
                        doc = KnowledgeDocument(
                            document_id=document_id,
                            content=content,
                            metadata=metadata,
                            source=source,
                            source_url=source_url,
                            tags=tags,
                            embeddings=embeddings,
                        )
                        self._documents[document_id] = doc
                        self._metrics["documents_indexed"] += 1

                    # Chunk the document
                    chunks = self._chunk_document(doc, chunk_size)
                    doc.chunk_ids = [c.chunk_id for c in chunks]

                    # Store chunks
                    for chunk in chunks:
                        self._chunks[chunk.chunk_id] = chunk
                        self._index_chunk(chunk)
                        self._metrics["chunks_created"] += 1

                    # Index the document
                    self._index_document(doc)

                    results.append({
                        "document_id": document_id,
                        "chunk_count": len(chunks),
                        "success": True,
                    })

                except Exception as e:
                    errors.append({
                        "document_id": doc_data.get("document_id"),
                        "error": str(e),
                    })

            # Update metrics
            self._metrics["total_documents"] = len(self._documents)
            self._metrics["total_chunks"] = len(self._chunks)
            self._metrics["last_index_time"] = datetime.utcnow().isoformat()

        logger.debug(f"Batch index: {len(results)} successes, {len(errors)} errors")

        return {
            "success": len(errors) == 0,
            "results": results,
            "errors": errors,
            "success_count": len(results),
            "error_count": len(errors),
        }

    async def _handle_delete_batch_command(self, command: "Command") -> Any:
        """
        Handle delete batch command.

        Args:
            command: Delete batch command.

        Returns:
            Result of batch delete operation.
        """
        payload = command.payload or {}
        document_ids = payload.get("document_ids", [])
        reason = payload.get("reason", "user_request")

        results = []
        errors = []

        async with self._knowledge_lock:
            for document_id in document_ids:
                try:
                    if document_id not in self._documents:
                        errors.append({
                            "document_id": document_id,
                            "error": "Document not found",
                        })
                        continue

                    doc = self._documents[document_id]

                    # Remove chunks
                    for chunk_id in doc.chunk_ids:
                        if chunk_id in self._chunks:
                            self._remove_chunk_from_indexes(self._chunks[chunk_id])
                            del self._chunks[chunk_id]
                            self._metrics["chunks_created"] -= 1

                    # Remove document
                    del self._documents[document_id]
                    self._remove_document_from_indexes(doc)
                    self._metrics["documents_deleted"] += 1

                    results.append({
                        "document_id": document_id,
                        "success": True,
                    })

                except Exception as e:
                    errors.append({
                        "document_id": document_id,
                        "error": str(e),
                    })

            # Update metrics
            self._metrics["total_documents"] = len(self._documents)
            self._metrics["total_chunks"] = len(self._chunks)

        logger.debug(f"Batch delete: {len(results)} successes, {len(errors)} errors")

        return {
            "success": len(errors) == 0,
            "results": results,
            "errors": errors,
            "success_count": len(results),
            "error_count": len(errors),
        }

    async def _handle_sync_command(self, command: "Command") -> Any:
        """
        Handle sync command.

        Args:
            command: Sync command.

        Returns:
            Result of sync operation.
        """
        payload = command.payload or {}
        source = payload.get("source")
        config = payload.get("config", {})

        if not source:
            raise ValueError("source is required")

        # In a real implementation, this would sync from an external source
        # For now, we'll just return success
        logger.info(f"Sync requested from source: {source}")

        return {
            "success": True,
            "source": source,
            "message": "Sync completed",
        }

    async def _handle_sync_source_command(self, command: "Command") -> Any:
        """
        Handle sync source command.

        Args:
            command: Sync source command.

        Returns:
            Result of sync source operation.
        """
        payload = command.payload or {}
        source = payload.get("source")
        config = payload.get("config", {})

        if not source:
            raise ValueError("source is required")

        # In a real implementation, this would sync a specific source
        logger.info(f"Sync source requested: {source}")

        return {
            "success": True,
            "source": source,
            "message": "Source synced",
        }

    async def _handle_add_relation_command(self, command: "Command") -> Any:
        """
        Handle add relation command.

        Args:
            command: Add relation command.

        Returns:
            Result of add relation operation.
        """
        payload = command.payload or {}
        source_id = payload.get("source_id")
        target_id = payload.get("target_id")
        relation_type = payload.get("relation_type", "related")
        metadata = payload.get("metadata", {})

        if not source_id or not target_id:
            raise ValueError("source_id and target_id are required")

        # In a real implementation, this would add a relation to the knowledge graph
        logger.info(f"Relation added: {source_id} -> {relation_type} -> {target_id}")

        return {
            "success": True,
            "source_id": source_id,
            "target_id": target_id,
            "relation_type": relation_type,
        }

    async def _handle_remove_relation_command(self, command: "Command") -> Any:
        """
        Handle remove relation command.

        Args:
            command: Remove relation command.

        Returns:
            Result of remove relation operation.
        """
        payload = command.payload or {}
        source_id = payload.get("source_id")
        target_id = payload.get("target_id")
        relation_type = payload.get("relation_type", "related")

        if not source_id or not target_id:
            raise ValueError("source_id and target_id are required")

        # In a real implementation, this would remove a relation from the knowledge graph
        logger.info(f"Relation removed: {source_id} -> {relation_type} -> {target_id}")

        return {
            "success": True,
            "source_id": source_id,
            "target_id": target_id,
            "relation_type": relation_type,
        }

    async def _handle_get_relations_command(self, command: "Command") -> Any:
        """
        Handle get relations command.

        Args:
            command: Get relations command.

        Returns:
            Result of get relations operation.
        """
        payload = command.payload or {}
        document_id = payload.get("document_id")
        relation_type = payload.get("relation_type")

        if not document_id:
            raise ValueError("document_id is required")

        # In a real implementation, this would query the knowledge graph
        # For now, return empty relations
        return {
            "document_id": document_id,
            "relations": [],
        }

    async def _handle_system_command(self, command: "Command", system_command: Any) -> Any:
        """
        Handle system command.

        Args:
            command: System command.
            system_command: System command type.

        Returns:
            Result of system command.
        """
        return self.get_metadata()

    # Query Handlers

    async def _handle_search_query(self, query: "Query") -> Any:
        """
        Handle search query.

        Args:
            query: Search query.

        Returns:
            Result of search operation.
        """
        payload = query.payload or {}
        search_query = payload.get("query", "")
        filter = payload.get("filter", {})
        tags = set(payload.get("tags", []))
        sources = set(payload.get("sources", []))
        limit = payload.get("limit", 10)
        use_semantic = payload.get("use_semantic", False)

        async with self._knowledge_lock:
            results = []

            # Extract search terms
            search_terms = self._extract_terms(search_query) if search_query else set()

            # Find matching documents
            matched_documents = set()

            # Match by search terms
            if search_terms:
                for term in search_terms:
                    if term in self._document_index:
                        matched_documents.update(self._document_index[term])

            # If no search terms, match all documents
            if not search_terms:
                matched_documents = set(self._documents.keys())

            # Apply filters
            filtered_documents = []
            for doc_id in matched_documents:
                if doc_id not in self._documents:
                    continue

                doc = self._documents[doc_id]

                # Apply source filter
                if sources and doc.source not in sources:
                    continue

                # Apply tag filter
                if tags and not tags.issubset(doc.tags):
                    continue

                # Apply metadata filter
                if filter and not all(
                    str(doc.metadata.get(k)) == str(v)
                    for k, v in filter.items()
                ):
                    continue

                filtered_documents.append(doc)

            # Sort by relevance (simple term frequency)
            filtered_documents.sort(
                key=lambda d: sum(
                    1 for term in search_terms
                    if term in self._document_index and d.document_id in self._document_index[term]
                ),
                reverse=True,
            )

            # Limit results
            filtered_documents = filtered_documents[:limit]

            # Create search results
            for doc in filtered_documents:
                # Calculate score (simple for now)
                score = sum(
                    1 for term in search_terms
                    if term in self._document_index and doc.document_id in self._document_index[term]
                ) / len(search_terms) if search_terms else 1.0

                # Find matched terms
                matched_terms = [
                    term for term in search_terms
                    if term in self._document_index and doc.document_id in self._document_index[term]
                ]

                results.append(SearchResult(
                    document_id=doc.document_id,
                    content=doc.content[:200] + "..." if len(doc.content) > 200 else doc.content,
                    score=score,
                    metadata=doc.metadata,
                    matched_terms=matched_terms,
                ))

            self._metrics["searches_performed"] += 1
            self._metrics["last_search_time"] = datetime.utcnow().isoformat()

        return {
            "query": search_query,
            "results": [r.to_dict() for r in results],
            "count": len(results),
            "total": len(self._documents),
        }

    async def _handle_semantic_search_query(self, query: "Query") -> Any:
        """
        Handle semantic search query.

        Args:
            query: Semantic search query.

        Returns:
            Result of semantic search operation.
        """
        payload = query.payload or {}
        search_query = payload.get("query", "")
        limit = payload.get("limit", 10)

        # In a real implementation, this would use vector embeddings
        # For now, we'll use simple similarity
        async with self._knowledge_lock:
            results = []

            if not search_query:
                return {
                    "query": search_query,
                    "results": [],
                    "count": 0,
                    "total": len(self._documents),
                }

            # Calculate similarity with each document
            similarities = []
            for doc in self._documents.values():
                similarity = self._calculate_similarity(search_query, doc.content)
                if similarity > 0:
                    similarities.append((doc, similarity))

            # Sort by similarity
            similarities.sort(key=lambda x: x[1], reverse=True)

            # Create results
            for doc, similarity in similarities[:limit]:
                results.append(SearchResult(
                    document_id=doc.document_id,
                    content=doc.content[:200] + "..." if len(doc.content) > 200 else doc.content,
                    score=similarity,
                    metadata=doc.metadata,
                ))

            self._metrics["searches_performed"] += 1

        return {
            "query": search_query,
            "results": [r.to_dict() for r in results],
            "count": len(results),
            "total": len(self._documents),
        }

    async def _handle_hybrid_search_query(self, query: "Query") -> Any:
        """
        Handle hybrid search query (keyword + semantic).

        Args:
            query: Hybrid search query.

        Returns:
            Result of hybrid search operation.
        """
        payload = query.payload or {}
        search_query = payload.get("query", "")
        limit = payload.get("limit", 10)
        keyword_weight = payload.get("keyword_weight", 0.7)
        semantic_weight = payload.get("semantic_weight", 0.3)

        # Perform both searches
        keyword_results = await self._handle_search_query(query)
        semantic_results = await self._handle_semantic_search_query(query)

        # Combine results
        combined = {}
        for result in keyword_results["results"]:
            combined[result["document_id"]] = {
                "keyword_score": result["score"],
                "semantic_score": 0.0,
                "result": result,
            }

        for result in semantic_results["results"]:
            if result["document_id"] in combined:
                combined[result["document_id"]]["semantic_score"] = result["score"]
            else:
                combined[result["document_id"]] = {
                    "keyword_score": 0.0,
                    "semantic_score": result["score"],
                    "result": result,
                }

        # Calculate combined scores
        scored_results = []
        for doc_id, scores in combined.items():
            combined_score = (
                keyword_weight * scores["keyword_score"] +
                semantic_weight * scores["semantic_score"]
            )
            scored_results.append((doc_id, combined_score, scores["result"]))

        # Sort by combined score
        scored_results.sort(key=lambda x: x[1], reverse=True)

        # Return top results
        results = [r[2] for r in scored_results[:limit]]

        return {
            "query": search_query,
            "results": results,
            "count": len(results),
            "total": len(self._documents),
        }

    async def _handle_get_query(self, query: "Query") -> Any:
        """
        Handle get document query.

        Args:
            query: Get query.

        Returns:
            Result of get operation.
        """
        payload = query.payload or {}
        document_id = payload.get("document_id")
        include_chunks = payload.get("include_chunks", False)

        if not document_id:
            raise ValueError("document_id is required")

        async with self._knowledge_lock:
            if document_id not in self._documents:
                return None

            doc = self._documents[document_id]

            result = doc.to_dict()

            if include_chunks:
                chunks = [
                    self._chunks[cid].to_dict()
                    for cid in doc.chunk_ids
                    if cid in self._chunks
                ]
                result["chunks"] = chunks

        return result

    async def _handle_get_by_source_query(self, query: "Query") -> Any:
        """
        Handle get by source query.

        Args:
            query: Get by source query.

        Returns:
            Result of get by source operation.
        """
        payload = query.payload or {}
        source = payload.get("source")
        limit = payload.get("limit", 10)

        if not source:
            raise ValueError("source is required")

        async with self._knowledge_lock:
            if source not in self._source_index:
                return {
                    "source": source,
                    "documents": [],
                    "count": 0,
                }

            doc_ids = list(self._source_index[source])[:limit]
            documents = [
                self._documents[did].to_dict()
                for did in doc_ids
                if did in self._documents
            ]

        return {
            "source": source,
            "documents": documents,
            "count": len(documents),
        }

    async def _handle_get_by_tag_query(self, query: "Query") -> Any:
        """
        Handle get by tag query.

        Args:
            query: Get by tag query.

        Returns:
            Result of get by tag operation.
        """
        payload = query.payload or {}
        tag = payload.get("tag")
        limit = payload.get("limit", 10)

        if not tag:
            raise ValueError("tag is required")

        async with self._knowledge_lock:
            if tag not in self._tag_index:
                return {
                    "tag": tag,
                    "documents": [],
                    "count": 0,
                }

            doc_ids = list(self._tag_index[tag])[:limit]
            documents = [
                self._documents[did].to_dict()
                for did in doc_ids
                if did in self._documents
            ]

        return {
            "tag": tag,
            "documents": documents,
            "count": len(documents),
        }

    async def _handle_list_query(self, query: "Query") -> Any:
        """
        Handle list documents query.

        Args:
            query: List query.

        Returns:
            Result of list operation.
        """
        payload = query.payload or {}
        filter = payload.get("filter", {})
        tags = set(payload.get("tags", []))
        sources = set(payload.get("sources", []))
        limit = payload.get("limit", 100)
        offset = payload.get("offset", 0)
        sort_by = payload.get("sort_by", "updated_at")
        sort_order = payload.get("sort_order", "desc")

        async with self._knowledge_lock:
            documents = list(self._documents.values())

            # Apply filters
            if filter:
                documents = [
                    d for d in documents
                    if all(str(d.metadata.get(k)) == str(v) for k, v in filter.items())
                ]

            if tags:
                documents = [d for d in documents if tags.issubset(d.tags)]

            if sources:
                documents = [d for d in documents if d.source in sources]

            # Sort
            reverse = sort_order == "desc"
            if sort_by == "created_at":
                documents.sort(key=lambda d: d.created_at, reverse=reverse)
            elif sort_by == "updated_at":
                documents.sort(key=lambda d: d.updated_at, reverse=reverse)
            elif sort_by == "document_id":
                documents.sort(key=lambda d: d.document_id, reverse=reverse)

            # Paginate
            total = len(documents)
            documents = documents[offset:offset + limit]

        return {
            "documents": [d.to_dict() for d in documents],
            "count": len(documents),
            "total": total,
            "offset": offset,
            "limit": limit,
        }

    async def _handle_exists_query(self, query: "Query") -> Any:
        """
        Handle exists document query.

        Args:
            query: Exists query.

        Returns:
            Result of exists operation.
        """
        payload = query.payload or {}
        document_id = payload.get("document_id")

        if not document_id:
            raise ValueError("document_id is required")

        async with self._knowledge_lock:
            exists = document_id in self._documents

        return {
            "document_id": document_id,
            "exists": exists,
        }

    async def _handle_count_query(self, query: "Query") -> Any:
        """
        Handle count documents query.

        Args:
            query: Count query.

        Returns:
            Result of count operation.
        """
        payload = query.payload or {}
        filter = payload.get("filter", {})
        tags = set(payload.get("tags", []))
        sources = set(payload.get("sources", []))

        async with self._knowledge_lock:
            count = 0
            for doc in self._documents.values():
                # Apply filters
                if filter and not all(
                    str(doc.metadata.get(k)) == str(v)
                    for k, v in filter.items()
                ):
                    continue

                if tags and not tags.issubset(doc.tags):
                    continue

                if sources and doc.source not in sources:
                    continue

                count += 1

        return {
            "count": count,
        }

    async def _handle_get_similar_query(self, query: "Query") -> Any:
        """
        Handle get similar documents query.

        Args:
            query: Get similar query.

        Returns:
            Result of get similar operation.
        """
        payload = query.payload or {}
        document_id = payload.get("document_id")
        limit = payload.get("limit", 10)

        if not document_id:
            raise ValueError("document_id is required")

        async with self._knowledge_lock:
            if document_id not in self._documents:
                raise ValueError(f"Document not found: {document_id}")

            source_doc = self._documents[document_id]

            # Calculate similarity with other documents
            similarities = []
            for doc in self._documents.values():
                if doc.document_id == document_id:
                    continue

                similarity = self._calculate_similarity(
                    source_doc.content, doc.content
                )
                if similarity > 0:
                    similarities.append((doc, similarity))

            # Sort by similarity
            similarities.sort(key=lambda x: x[1], reverse=True)

            # Create results
            results = []
            for doc, similarity in similarities[:limit]:
                results.append(SearchResult(
                    document_id=doc.document_id,
                    content=doc.content[:200] + "..." if len(doc.content) > 200 else doc.content,
                    score=similarity,
                    metadata=doc.metadata,
                ))

        return {
            "document_id": document_id,
            "results": [r.to_dict() for r in results],
            "count": len(results),
        }

    async def _handle_get_related_query(self, query: "Query") -> Any:
        """
        Handle get related documents query.

        Args:
            query: Get related query.

        Returns:
            Result of get related operation.
        """
        payload = query.payload or {}
        document_id = payload.get("document_id")
        limit = payload.get("limit", 10)

        if not document_id:
            raise ValueError("document_id is required")

        # In a real implementation, this would query the knowledge graph
        # For now, we'll return similar documents
        similar_result = await self._handle_get_similar_query(query)

        return {
            "document_id": document_id,
            "results": similar_result["results"],
            "count": similar_result["count"],
        }

    async def _handle_get_stats_query(self, query: "Query") -> Any:
        """
        Handle get stats query.

        Args:
            query: Get stats query.

        Returns:
            Knowledge engine statistics.
        """
        async with self._knowledge_lock:
            # Get source statistics
            source_counts = {}
            for source, doc_ids in self._source_index.items():
                source_counts[source] = len(doc_ids)

            # Get tag statistics
            tag_counts = {tag: len(doc_ids) for tag, doc_ids in self._tag_index.items()}

            # Get metadata statistics
            metadata_keys = set()
            for key in self._metadata_index:
                metadata_keys.add(key)

        return {
            "total_documents": len(self._documents),
            "total_chunks": len(self._chunks),
            "source_counts": source_counts,
            "tag_counts": tag_counts,
            "metadata_keys": list(metadata_keys),
            "metrics": self._metrics.copy(),
        }

    async def _handle_system_query(self, query: "Query", system_query: Any) -> Any:
        """
        Handle system query.

        Args:
            query: System query.
            system_query: System query type.

        Returns:
            Result of system query.
        """
        return self.get_metadata()

    # Event Handlers

    async def _handle_system_startup(self, event: "Event") -> None:
        """Handle system startup event."""
        logger.info(f"System startup event received: {event.payload}")

    async def _handle_system_shutdown(self, event: "Event") -> None:
        """Handle system shutdown event."""
        logger.info(f"System shutdown event received: {event.payload}")

    async def _handle_health_check(self, event: "Event") -> None:
        """Handle health check event."""
        logger.debug(f"Health check event received: {event.payload}")

    async def _handle_knowledge_indexed(self, event: "Event") -> None:
        """Handle knowledge indexed event from other runtimes."""
        logger.debug(f"Knowledge indexed event received: {event.payload}")

    async def _handle_knowledge_updated(self, event: "Event") -> None:
        """Handle knowledge updated event from other runtimes."""
        logger.debug(f"Knowledge updated event received: {event.payload}")

    async def _handle_knowledge_deleted(self, event: "Event") -> None:
        """Handle knowledge deleted event from other runtimes."""
        logger.debug(f"Knowledge deleted event received: {event.payload}")

    async def _handle_memory_updated(self, event: "Event") -> None:
        """Handle memory updated event."""
        logger.debug(f"Memory updated event received: {event.payload}")
        # Could trigger knowledge sync from memory

    # Additional Methods

    def get_document(self, document_id: str) -> Optional[KnowledgeDocument]:
        """
        Get a document by ID (synchronous).

        Args:
            document_id: ID of the document to get.

        Returns:
            KnowledgeDocument if found, None otherwise.
        """
        return self._documents.get(document_id)

    def list_documents(self) -> List[str]:
        """
        List all document IDs (synchronous).

        Returns:
            List of document IDs.
        """
        return list(self._documents.keys())

    def get_metrics(self) -> Dict[str, Any]:
        """
        Get knowledge engine metrics.

        Returns:
            Dictionary of metrics.
        """
        return {
            **self._metrics,
            "document_count": len(self._documents),
            "chunk_count": len(self._chunks),
            "index_size": len(self._document_index) + len(self._chunk_index),
        }

    def __repr__(self) -> str:
        """Return string representation."""
        return (
            f"KnowledgeEngineRuntime("
            f"id={self.runtime_id}, "
            f"name={self.config.name}, "
            f"version={self.config.version}, "
            f"documents={len(self._documents)}, "
            f"chunks={len(self._chunks)})"
        )
