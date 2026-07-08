#!/usr/bin/env python3
"""
Context Builder for the TangkuAgentOS Context Engine.

This module implements context building from various data sources with support for:
- Context construction from raw data
- Metadata enrichment
- Chunk creation and management
- Source attribution
"""

from __future__ import annotations

import asyncio
import hashlib
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple, Union
from uuid import uuid4

from .interfaces import IContextBuilder
from .models import (
    Context,
    ContextChunk,
    ContextMetadata,
    ContextSource,
    ContextSourceInfo,
    ContextType,
)
from .exceptions import (
    ContextError,
    ContextValidationError,
)

logger = logging.getLogger(__name__)


# =============================================================================
# Base Context Builder
# =============================================================================


class BaseContextBuilder(IContextBuilder):
    """
    Base class for context builder implementations.
    
    This class provides common functionality for building contexts.
    Subclasses should implement specific building strategies.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the context builder.
        
        Args:
            config: Configuration for the builder
        """
        self.config = config or {}
        self._initialized = False
        self._lock = asyncio.Lock()
    
    async def initialize(self, config: Optional[Dict[str, Any]] = None) -> None:
        """Initialize the context builder."""
        async with self._lock:
            if self._initialized:
                return
            
            if config:
                self.config.update(config)
            
            self._initialized = True
            logger.info(f"Initialized {self.__class__.__name__}")
    
    async def shutdown(self) -> None:
        """Shutdown the context builder."""
        async with self._lock:
            if not self._initialized:
                return
            
            self._initialized = False
            logger.info(f"Shut down {self.__class__.__name__}")
    
    async def build(
        self,
        data: Any,
        source: ContextSource,
        metadata: Optional[Dict[str, Any]] = None,
        config: Optional[Dict[str, Any]] = None,
    ) -> Context:
        """Build a context from raw data."""
        if not self._initialized:
            await self.initialize()
        
        # Convert data to string if it's not already
        if not isinstance(data, str):
            data = str(data)
        
        # Create a single chunk from the data
        chunk = await self.build_chunk(data, source, metadata)
        
        # Create the context
        context = Context(
            context_id=str(uuid4()),
            chunks=[chunk],
            metadata=ContextMetadata(
                source=source,
                timestamp=datetime.now(),
                author=metadata.get("author", "system") if metadata else "system",
                tags=metadata.get("tags", []) if metadata else [],
                custom=metadata or {},
            ),
        )
        
        # Enrich metadata
        context = await self.enrich_metadata(context, metadata)
        
        return context
    
    async def build_chunk(
        self,
        content: str,
        source: ContextSource,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> ContextChunk:
        """Build a context chunk from content."""
        # Calculate token count (simple implementation)
        token_count = self._count_tokens(content)
        
        # Create metadata
        chunk_metadata = ContextMetadata(
            source=source,
            timestamp=datetime.now(),
            priority=metadata.get("priority", ContextSource.MEDIUM) if metadata else ContextSource.MEDIUM,
            author=metadata.get("author", "system") if metadata else "system",
            tags=metadata.get("tags", []) if metadata else [],
            custom=metadata or {},
        )
        
        # Create source info
        source_info = ContextSourceInfo(
            source=source,
            query=metadata.get("query", "") if metadata else "",
            parameters=metadata.get("parameters", {}) if metadata else {},
        )
        
        # Create the chunk
        chunk = ContextChunk(
            chunk_id=str(uuid4()),
            content=content,
            metadata=chunk_metadata,
            token_count=token_count,
            source_info=source_info,
        )
        
        return chunk
    
    async def enrich_metadata(
        self,
        context: Context,
        additional_metadata: Optional[Dict[str, Any]] = None,
    ) -> Context:
        """Enrich context metadata with additional information."""
        # Add additional metadata to the context
        if additional_metadata:
            for key, value in additional_metadata.items():
                if hasattr(context.metadata, key):
                    setattr(context.metadata, key, value)
                else:
                    context.metadata.custom[key] = value
        
        # Add metadata to chunks if not already present
        for chunk in context.chunks:
            if not chunk.metadata.author:
                chunk.metadata.author = context.metadata.author
            if not chunk.metadata.tags:
                chunk.metadata.tags = context.metadata.tags
        
        return context
    
    async def attribute_sources(
        self,
        context: Context,
        source_info: Dict[str, ContextSourceInfo],
    ) -> Context:
        """Add source attribution to context chunks."""
        for chunk in context.chunks:
            if chunk.chunk_id in source_info:
                chunk.source_info = source_info[chunk.chunk_id]
        
        return context
    
    def _count_tokens(self, text: str) -> int:
        """
        Count the number of tokens in a text.
        
        This is a simple implementation that counts words.
        In a real implementation, this would use a proper tokenizer.
        """
        if not text:
            return 0
        
        # Simple word count as a proxy for token count
        words = text.split()
        return len(words)


# =============================================================================
# Metadata Enricher
# =============================================================================


class MetadataEnricher(BaseContextBuilder):
    """
    Context builder that specializes in metadata enrichment.
    
    This builder adds rich metadata to contexts, including:
    - Timestamps
    - Source attribution
    - Priority scoring
    - Tags and categories
    - Custom metadata fields
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the metadata enricher.
        
        Args:
            config: Configuration for the enricher
        """
        super().__init__(config)
        self._enrichment_rules = config.get("enrichment_rules", {})
    
    async def initialize(self, config: Optional[Dict[str, Any]] = None) -> None:
        """Initialize the metadata enricher."""
        await super().initialize(config)
        
        # Load enrichment rules if provided
        if config and "enrichment_rules" in config:
            self._enrichment_rules = config["enrichment_rules"]
    
    async def build(
        self,
        data: Any,
        source: ContextSource,
        metadata: Optional[Dict[str, Any]] = None,
        config: Optional[Dict[str, Any]] = None,
    ) -> Context:
        """Build a context with enriched metadata."""
        # First, build the basic context
        context = await super().build(data, source, metadata, config)
        
        # Apply enrichment rules
        context = await self._apply_enrichment_rules(context)
        
        return context
    
    async def enrich_metadata(
        self,
        context: Context,
        additional_metadata: Optional[Dict[str, Any]] = None,
    ) -> Context:
        """Enrich context metadata with additional information."""
        # Apply basic enrichment
        context = await super().enrich_metadata(context, additional_metadata)
        
        # Apply enrichment rules
        context = await self._apply_enrichment_rules(context)
        
        return context
    
    async def _apply_enrichment_rules(self, context: Context) -> Context:
        """Apply enrichment rules to the context."""
        # Apply rules based on source
        source_rules = self._enrichment_rules.get("sources", {}).get(context.metadata.source.name, {})
        
        for key, value in source_rules.items():
            if hasattr(context.metadata, key):
                setattr(context.metadata, key, value)
            else:
                context.metadata.custom[key] = value
        
        # Apply rules based on content
        content_rules = self._enrichment_rules.get("content", {})
        for pattern, metadata in content_rules.items():
            if pattern in context.content:
                for key, value in metadata.items():
                    if hasattr(context.metadata, key):
                        setattr(context.metadata, key, value)
                    else:
                        context.metadata.custom[key] = value
        
        # Apply priority rules
        priority_rules = self._enrichment_rules.get("priority", {})
        for pattern, priority in priority_rules.items():
            if pattern in context.content:
                context.metadata.priority = ContextSource[priority]
        
        # Apply tags based on content
        tag_rules = self._enrichment_rules.get("tags", {})
        for pattern, tags in tag_rules.items():
            if pattern in context.content:
                context.metadata.tags.extend(tags)
        
        return context


# =============================================================================
# Context Builder (Main Implementation)
# =============================================================================


class ContextBuilder(MetadataEnricher):
    """
    Main context builder implementation.
    
    This class provides a comprehensive context building system with support for:
    - Context construction from various data sources
    - Metadata enrichment
    - Chunk creation and management
    - Source attribution
    - Configurable building strategies
    
    Example:
        ```python
        from tangku_agentos.context_engine import ContextBuilder, ContextSource
        
        # Create the builder
        builder = ContextBuilder()
        
        # Build a context from raw data
        context = await builder.build(
            data="This is some context data",
            source=ContextSource.MEMORY_ENGINE,
            metadata={"author": "user", "tags": ["example"]},
        )
        
        print(f"Built context with {len(context.chunks)} chunks")
        ```
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the context builder.
        
        Args:
            config: Configuration for the builder
        """
        super().__init__(config)
        self._chunk_size_limit = config.get("chunk_size_limit", 1024) if config else 1024
    
    async def initialize(self, config: Optional[Dict[str, Any]] = None) -> None:
        """Initialize the context builder."""
        await super().initialize(config)
        
        if config and "chunk_size_limit" in config:
            self._chunk_size_limit = config["chunk_size_limit"]
    
    async def build(
        self,
        data: Any,
        source: ContextSource,
        metadata: Optional[Dict[str, Any]] = None,
        config: Optional[Dict[str, Any]] = None,
    ) -> Context:
        """Build a context from raw data."""
        if not self._initialized:
            await self.initialize()
        
        # Convert data to string if it's not already
        if not isinstance(data, str):
            data = str(data)
        
        # Split data into chunks if it exceeds the size limit
        chunks = await self._split_into_chunks(data, source, metadata)
        
        # Create the context
        context = Context(
            context_id=str(uuid4()),
            chunks=chunks,
            metadata=ContextMetadata(
                source=source,
                timestamp=datetime.now(),
                author=metadata.get("author", "system") if metadata else "system",
                tags=metadata.get("tags", []) if metadata else [],
                custom=metadata or {},
            ),
        )
        
        # Enrich metadata
        context = await self.enrich_metadata(context, metadata)
        
        return context
    
    async def build_chunk(
        self,
        content: str,
        source: ContextSource,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> ContextChunk:
        """Build a context chunk from content."""
        chunk = await super().build_chunk(content, source, metadata)
        
        # Add chunk-specific metadata
        if metadata:
            if "chunk_priority" in metadata:
                chunk.metadata.priority = ContextSource[metadata["chunk_priority"]]
            if "chunk_tags" in metadata:
                chunk.metadata.tags.extend(metadata["chunk_tags"])
        
        return chunk
    
    async def _split_into_chunks(
        self,
        data: str,
        source: ContextSource,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> List[ContextChunk]:
        """Split data into chunks based on size limit."""
        chunks = []
        
        # If data is small enough, create a single chunk
        if len(data) <= self._chunk_size_limit:
            chunk = await self.build_chunk(data, source, metadata)
            chunks.append(chunk)
            return chunks
        
        # Split data into chunks
        # Simple implementation: split by paragraphs
        paragraphs = data.split("\n\n")
        current_chunk = ""
        
        for paragraph in paragraphs:
            if len(current_chunk) + len(paragraph) + 2 <= self._chunk_size_limit:
                current_chunk += ("\n\n" if current_chunk else "") + paragraph
            else:
                if current_chunk:
                    chunk = await self.build_chunk(current_chunk, source, metadata)
                    chunks.append(chunk)
                current_chunk = paragraph
        
        # Add the last chunk
        if current_chunk:
            chunk = await self.build_chunk(current_chunk, source, metadata)
            chunks.append(chunk)
        
        return chunks
    
    async def build_from_list(
        self,
        items: List[Any],
        source: ContextSource,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Context:
        """
        Build a context from a list of items.
        
        Args:
            items: List of items to build context from
            source: The source of the items
            metadata: Optional metadata for the context
            
        Returns:
            The built context
        """
        chunks = []
        for item in items:
            chunk = await self.build_chunk(str(item), source, metadata)
            chunks.append(chunk)
        
        context = Context(
            context_id=str(uuid4()),
            chunks=chunks,
            metadata=ContextMetadata(
                source=source,
                timestamp=datetime.now(),
                author=metadata.get("author", "system") if metadata else "system",
                tags=metadata.get("tags", []) if metadata else [],
                custom=metadata or {},
            ),
        )
        
        context = await self.enrich_metadata(context, metadata)
        return context
    
    async def build_from_dict(
        self,
        data: Dict[str, Any],
        source: ContextSource,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Context:
        """
        Build a context from a dictionary.
        
        Args:
            data: Dictionary to build context from
            source: The source of the data
            metadata: Optional metadata for the context
            
        Returns:
            The built context
        """
        # Convert dictionary to string representation
        import json
        data_str = json.dumps(data, indent=2)
        
        return await self.build(data_str, source, metadata)
    
    async def enrich_metadata(
        self,
        context: Context,
        additional_metadata: Optional[Dict[str, Any]] = None,
    ) -> Context:
        """Enrich context metadata with additional information."""
        # Apply basic enrichment
        context = await super().enrich_metadata(context, additional_metadata)
        
        # Add context-level metadata
        context.metadata.custom["chunk_count"] = len(context.chunks)
        context.metadata.custom["total_tokens"] = context.token_count
        
        return context
