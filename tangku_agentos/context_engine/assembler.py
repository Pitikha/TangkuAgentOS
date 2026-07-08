#!/usr/bin/env python3
"""
Context Assembler for the TangkuAgentOS Context Engine.

This module implements context assembly from multiple sources with support for:
- Multi-source context assembly
- Context prioritization
- Context merging
- Context deduplication
- Context validation
- Metadata enrichment
- Source attribution
"""

from __future__ import annotations

import asyncio
import hashlib
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional, Tuple, Union
from uuid import uuid4

from .interfaces import IContextAssembler
from .models import (
    Context,
    ContextChunk,
    ContextMetadata,
    ContextSource,
    ContextSourceInfo,
    ContextType,
    ContextAssemblyResult,
    AssemblyConfig,
)
from .exceptions import (
    ContextError,
    ContextAssemblyError,
    ContextSourceError,
    ContextMergeError,
    ContextDeduplicationError,
    ContextValidationError,
)

logger = logging.getLogger(__name__)


# =============================================================================
# Base Context Assembler
# =============================================================================


class BaseContextAssembler(IContextAssembler):
    """
    Base class for context assembler implementations.
    
    This class provides common functionality for context assembly.
    Subclasses should implement specific assembly strategies.
    """
    
    def __init__(self, config: Optional[AssemblyConfig] = None):
        """
        Initialize the context assembler.
        
        Args:
            config: Configuration for the assembler
        """
        self.config = config or AssemblyConfig()
        self._sources: Dict[str, Any] = {}
        self._initialized = False
        self._lock = asyncio.Lock()
    
    async def initialize(self, config: Optional[Dict[str, Any]] = None) -> None:
        """Initialize the context assembler."""
        async with self._lock:
            if self._initialized:
                return
            
            if config:
                for key, value in config.items():
                    setattr(self.config, key, value)
            
            self._initialized = True
            logger.info(f"Initialized {self.__class__.__name__}")
    
    async def shutdown(self) -> None:
        """Shutdown the context assembler."""
        async with self._lock:
            if not self._initialized:
                return
            
            self._sources.clear()
            self._initialized = False
            logger.info(f"Shut down {self.__class__.__name__}")
    
    async def add_source(
        self,
        source_name: str,
        source: Any,
        priority: Optional[int] = None,
    ) -> None:
        """Add a context source to the assembler."""
        async with self._lock:
            if source_name in self._sources:
                raise ContextError(
                    message=f"Source '{source_name}' already registered",
                    code="SOURCE_EXISTS",
                )
            
            self._sources[source_name] = {
                "source": source,
                "priority": priority or 0,
            }
            logger.debug(f"Added source: {source_name} (priority: {priority})")
    
    async def remove_source(self, source_name: str) -> None:
        """Remove a context source from the assembler."""
        async with self._lock:
            if source_name not in self._sources:
                raise ContextError(
                    message=f"Source '{source_name}' not found",
                    code="SOURCE_NOT_FOUND",
                )
            
            del self._sources[source_name]
            logger.debug(f"Removed source: {source_name}")
    
    async def get_source(self, source_name: str) -> Any:
        """Get a context source by name."""
        if source_name not in self._sources:
            raise ContextError(
                message=f"Source '{source_name}' not found",
                code="SOURCE_NOT_FOUND",
            )
        return self._sources[source_name]["source"]
    
    async def list_sources(self) -> List[str]:
        """List all registered context sources."""
        return list(self._sources.keys())
    
    async def assemble(
        self,
        sources: List[Dict[str, Any]],
        config: Optional[AssemblyConfig] = None,
    ) -> ContextAssemblyResult:
        """Assemble context from multiple sources."""
        if not self._initialized:
            await self.initialize()
        
        # Use provided config or default
        assembly_config = config or self.config
        
        start_time = datetime.now()
        result = ContextAssemblyResult(
            context=Context(),
            assembly_time=0.0,
        )
        
        try:
            # Collect chunks from all sources
            all_chunks = []
            used_sources = []
            
            for source_spec in sources:
                source_name = source_spec.get("source")
                query = source_spec.get("query", "")
                parameters = source_spec.get("parameters", {})
                
                try:
                    # Get the source
                    if source_name in self._sources:
                        source = self._sources[source_name]["source"]
                    elif hasattr(self, f"_get_{source_name}_source"):
                        source = getattr(self, f"_get_{source_name}_source")()
                    else:
                        raise ContextSourceError(
                            source=source_name,
                            source_id="",
                            query=query,
                            message=f"Source '{source_name}' not found",
                        )
                    
                    # Get context from the source
                    if hasattr(source, "provide"):
                        source_context = await source.provide(
                            query=query,
                            filters=parameters.get("filters"),
                            limit=parameters.get("limit"),
                            offset=parameters.get("offset"),
                        )
                    elif hasattr(source, "get_context"):
                        source_context = await source.get_context(query)
                    else:
                        raise ContextSourceError(
                            source=source_name,
                            source_id="",
                            query=query,
                            message=f"Source '{source_name}' has no provide method",
                        )
                    
                    # Add chunks to the result
                    for chunk in source_context.chunks:
                        # Create source info
                        source_info = ContextSourceInfo(
                            source=ContextSource[source_name.upper()],
                            source_id=source_name,
                            query=query,
                            parameters=parameters,
                        )
                        
                        # Create a new chunk with source info
                        new_chunk = ContextChunk(
                            chunk_id=str(uuid4()),
                            content=chunk.content,
                            metadata=chunk.metadata,
                            token_count=chunk.token_count,
                            source_info=source_info,
                        )
                        all_chunks.append(new_chunk)
                    
                    used_sources.append(ContextSource[source_name.upper()])
                    
                except Exception as e:
                    logger.error(f"Error assembling from source {source_name}: {e}")
                    raise ContextSourceError(
                        source=source_name,
                        source_id="",
                        query=query,
                        message=f"Failed to assemble from source: {e}",
                        cause=e,
                    )
            
            # Create the assembled context
            result.context = Context(
                context_id=str(uuid4()),
                chunks=all_chunks,
                metadata=ContextMetadata(
                    source=ContextSource.MEMORY_ENGINE,
                    timestamp=datetime.now(),
                ),
            )
            
            # Apply assembly operations
            if assembly_config.deduplication:
                result.context = await self.deduplicate(result.context)
            
            result.context = await self.prioritize(result.context)
            result.context = await self.merge(result.context)
            
            # Calculate statistics
            result.chunks_added = len(result.context.chunks)
            result.sources_used = used_sources
            result.assembly_time = (datetime.now() - start_time).total_seconds()
            
            # Validate the assembled context
            await self._validate_context(result.context)
            
        except Exception as e:
            raise ContextAssemblyError(
                source="assembler",
                message=f"Assembly failed: {e}",
                cause=e,
            )
        
        return result
    
    async def prioritize(
        self,
        context: Context,
        config: Optional[Dict[str, Any]] = None,
    ) -> Context:
        """Prioritize chunks in a context."""
        # Sort chunks by priority (descending)
        context.chunks.sort(
            key=lambda x: x.metadata.priority.value,
            reverse=True,
        )
        return context
    
    async def merge(
        self,
        context: Context,
        config: Optional[Dict[str, Any]] = None,
    ) -> Context:
        """Merge chunks in a context."""
        # Default implementation: no merging, just return the context
        return context
    
    async def deduplicate(
        self,
        context: Context,
        config: Optional[Dict[str, Any]] = None,
    ) -> Context:
        """Remove duplicate chunks from a context."""
        seen_contents = set()
        unique_chunks = []
        duplicates_removed = 0
        
        for chunk in context.chunks:
            # Create a hash of the content for deduplication
            content_hash = hashlib.md5(chunk.content.encode()).hexdigest()
            
            if content_hash not in seen_contents:
                seen_contents.add(content_hash)
                unique_chunks.append(chunk)
            else:
                duplicates_removed += 1
        
        context.chunks = unique_chunks
        return context
    
    async def _validate_context(self, context: Context) -> None:
        """Validate an assembled context."""
        if not context.chunks:
            raise ContextValidationError(
                field="chunks",
                value=[],
                expected="non-empty list",
                message="Assembled context has no chunks",
            )
        
        for chunk in context.chunks:
            if not chunk.content:
                raise ContextValidationError(
                    field="content",
                    value=chunk.content,
                    expected="non-empty string",
                    message=f"Chunk {chunk.chunk_id} has empty content",
                )


# =============================================================================
# Multi-Source Context Assembler
# =============================================================================


class MultiSourceAssembler(BaseContextAssembler):
    """
    Context assembler that gathers context from multiple sources.
    
    This assembler supports:
    - Parallel or sequential assembly from multiple sources
    - Source-specific queries and parameters
    - Priority-based source ordering
    - Error handling for individual sources
    """
    
    def __init__(self, config: Optional[AssemblyConfig] = None):
        """
        Initialize the multi-source assembler.
        
        Args:
            config: Configuration for the assembler
        """
        super().__init__(config)
    
    async def assemble(
        self,
        sources: List[Dict[str, Any]],
        config: Optional[AssemblyConfig] = None,
    ) -> ContextAssemblyResult:
        """Assemble context from multiple sources."""
        if not self._initialized:
            await self.initialize()
        
        # Use provided config or default
        assembly_config = config or self.config
        
        start_time = datetime.now()
        result = ContextAssemblyResult(
            context=Context(),
            assembly_time=0.0,
        )
        
        try:
            # Determine assembly mode
            if assembly_config.mode == ContextAssemblyMode.PARALLEL:
                result = await self._assemble_parallel(sources, assembly_config)
            elif assembly_config.mode == ContextAssemblyMode.SEQUENTIAL:
                result = await self._assemble_sequential(sources, assembly_config)
            elif assembly_config.mode == ContextAssemblyMode.MERGE:
                result = await self._assemble_merge(sources, assembly_config)
            elif assembly_config.mode == ContextAssemblyMode.PRIORITY:
                result = await self._assemble_priority(sources, assembly_config)
            else:
                # Default to parallel
                result = await self._assemble_parallel(sources, assembly_config)
            
            # Apply post-assembly operations
            if assembly_config.deduplication:
                result.context = await self.deduplicate(result.context)
            
            result.context = await self.prioritize(result.context)
            
            # Calculate final statistics
            result.assembly_time = (datetime.now() - start_time).total_seconds()
            
            # Validate the assembled context
            await self._validate_context(result.context)
            
        except Exception as e:
            raise ContextAssemblyError(
                source="multi_source_assembler",
                message=f"Multi-source assembly failed: {e}",
                cause=e,
            )
        
        return result
    
    async def _assemble_parallel(
        self,
        sources: List[Dict[str, Any]],
        config: AssemblyConfig,
    ) -> ContextAssemblyResult:
        """Assemble context from sources in parallel."""
        result = ContextAssemblyResult(
            context=Context(),
            chunks_added=0,
            sources_used=[],
        )
        
        # Sort sources by priority (highest first)
        sorted_sources = sorted(
            sources,
            key=lambda x: self._sources.get(x.get("source"), {}).get("priority", 0),
            reverse=True,
        )
        
        # Process sources in parallel
        tasks = []
        for source_spec in sorted_sources:
            source_name = source_spec.get("source")
            query = source_spec.get("query", "")
            parameters = source_spec.get("parameters", {})
            
            task = asyncio.create_task(
                self._get_source_context(source_name, query, parameters)
            )
            tasks.append(task)
        
        # Wait for all tasks to complete
        source_contexts = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results
        for i, source_spec in enumerate(sorted_sources):
            source_name = source_spec.get("source")
            source_context = source_contexts[i]
            
            if isinstance(source_context, Exception):
                logger.error(f"Error assembling from source {source_name}: {source_context}")
                continue
            
            if source_context:
                # Add chunks to the result
                for chunk in source_context.chunks:
                    # Create source info
                    source_info = ContextSourceInfo(
                        source=ContextSource[source_name.upper()],
                        source_id=source_name,
                        query=source_spec.get("query", ""),
                        parameters=source_spec.get("parameters", {}),
                    )
                    
                    # Create a new chunk with source info
                    new_chunk = ContextChunk(
                        chunk_id=str(uuid4()),
                        content=chunk.content,
                        metadata=chunk.metadata,
                        token_count=chunk.token_count,
                        source_info=source_info,
                    )
                    result.context.chunks.append(new_chunk)
                    result.chunks_added += 1
                
                result.sources_used.append(ContextSource[source_name.upper()])
        
        return result
    
    async def _assemble_sequential(
        self,
        sources: List[Dict[str, Any]],
        config: AssemblyConfig,
    ) -> ContextAssemblyResult:
        """Assemble context from sources sequentially."""
        result = ContextAssemblyResult(
            context=Context(),
            chunks_added=0,
            sources_used=[],
        )
        
        # Sort sources by priority (highest first)
        sorted_sources = sorted(
            sources,
            key=lambda x: self._sources.get(x.get("source"), {}).get("priority", 0),
            reverse=True,
        )
        
        # Process sources sequentially
        for source_spec in sorted_sources:
            source_name = source_spec.get("source")
            query = source_spec.get("query", "")
            parameters = source_spec.get("parameters", {})
            
            try:
                source_context = await self._get_source_context(source_name, query, parameters)
                
                if source_context:
                    # Add chunks to the result
                    for chunk in source_context.chunks:
                        # Create source info
                        source_info = ContextSourceInfo(
                            source=ContextSource[source_name.upper()],
                            source_id=source_name,
                            query=query,
                            parameters=parameters,
                        )
                        
                        # Create a new chunk with source info
                        new_chunk = ContextChunk(
                            chunk_id=str(uuid4()),
                            content=chunk.content,
                            metadata=chunk.metadata,
                            token_count=chunk.token_count,
                            source_info=source_info,
                        )
                        result.context.chunks.append(new_chunk)
                        result.chunks_added += 1
                    
                    result.sources_used.append(ContextSource[source_name.upper()])
                    
            except Exception as e:
                logger.error(f"Error assembling from source {source_name}: {e}")
                continue
        
        return result
    
    async def _assemble_merge(
        self,
        sources: List[Dict[str, Any]],
        config: AssemblyConfig,
    ) -> ContextAssemblyResult:
        """Assemble context by merging from all sources."""
        # First, get all contexts
        contexts = []
        for source_spec in sources:
            source_name = source_spec.get("source")
            query = source_spec.get("query", "")
            parameters = source_spec.get("parameters", {})
            
            try:
                source_context = await self._get_source_context(source_name, query, parameters)
                if source_context:
                    contexts.append(source_context)
            except Exception as e:
                logger.error(f"Error assembling from source {source_name}: {e}")
                continue
        
        # Merge all contexts
        result = ContextAssemblyResult(
            context=Context(),
            chunks_added=0,
            sources_used=[],
        )
        
        for context in contexts:
            for chunk in context.chunks:
                result.context.chunks.append(chunk)
                result.chunks_added += 1
        
        # Update source list
        for source_spec in sources:
            source_name = source_spec.get("source")
            result.sources_used.append(ContextSource[source_name.upper()])
        
        return result
    
    async def _assemble_priority(
        self,
        sources: List[Dict[str, Any]],
        config: AssemblyConfig,
    ) -> ContextAssemblyResult:
        """Assemble context based on source priority."""
        # Sort sources by priority
        sorted_sources = sorted(
            sources,
            key=lambda x: self._sources.get(x.get("source"), {}).get("priority", 0),
            reverse=True,
        )
        
        result = ContextAssemblyResult(
            context=Context(),
            chunks_added=0,
            sources_used=[],
        )
        
        # Process sources in priority order
        for source_spec in sorted_sources:
            source_name = source_spec.get("source")
            query = source_spec.get("query", "")
            parameters = source_spec.get("parameters", {})
            
            try:
                source_context = await self._get_source_context(source_name, query, parameters)
                
                if source_context:
                    # Add chunks to the result
                    for chunk in source_context.chunks:
                        # Create source info
                        source_info = ContextSourceInfo(
                            source=ContextSource[source_name.upper()],
                            source_id=source_name,
                            query=query,
                            parameters=parameters,
                        )
                        
                        # Create a new chunk with source info
                        new_chunk = ContextChunk(
                            chunk_id=str(uuid4()),
                            content=chunk.content,
                            metadata=chunk.metadata,
                            token_count=chunk.token_count,
                            source_info=source_info,
                        )
                        result.context.chunks.append(new_chunk)
                        result.chunks_added += 1
                    
                    result.sources_used.append(ContextSource[source_name.upper()])
                    
                    # If we have enough context, stop here
                    if config.max_sources and len(result.sources_used) >= config.max_sources:
                        break
                        
            except Exception as e:
                logger.error(f"Error assembling from source {source_name}: {e}")
                continue
        
        return result
    
    async def _get_source_context(
        self,
        source_name: str,
        query: str,
        parameters: Dict[str, Any],
    ) -> Optional[Context]:
        """Get context from a specific source."""
        try:
            # Get the source
            if source_name in self._sources:
                source = self._sources[source_name]["source"]
            elif hasattr(self, f"_get_{source_name}_source"):
                source = getattr(self, f"_get_{source_name}_source")()
            else:
                return None
            
            # Get context from the source
            if hasattr(source, "provide"):
                return await source.provide(
                    query=query,
                    filters=parameters.get("filters"),
                    limit=parameters.get("limit"),
                    offset=parameters.get("offset"),
                )
            elif hasattr(source, "get_context"):
                return await source.get_context(query)
            else:
                return None
                
        except Exception as e:
            logger.error(f"Error getting context from source {source_name}: {e}")
            return None


# =============================================================================
# Priority Context Assembler
# =============================================================================


class PriorityAssembler(BaseContextAssembler):
    """
    Context assembler that prioritizes chunks based on importance.
    
    This assembler supports:
    - Priority-based chunk ordering
    - Priority threshold filtering
    - Dynamic priority adjustment
    """
    
    def __init__(self, config: Optional[AssemblyConfig] = None):
        """
        Initialize the priority assembler.
        
        Args:
            config: Configuration for the assembler
        """
        super().__init__(config)
    
    async def prioritize(
        self,
        context: Context,
        config: Optional[Dict[str, Any]] = None,
    ) -> Context:
        """Prioritize chunks in a context based on priority."""
        # Get threshold from config or use default
        threshold = self.config.priority_threshold
        if config and "priority_threshold" in config:
            threshold = ContextPriority[config["priority_threshold"]]
        
        # Filter chunks by priority threshold
        filtered_chunks = [
            chunk for chunk in context.chunks
            if chunk.metadata.priority.value >= threshold.value
        ]
        
        # Sort by priority (descending)
        filtered_chunks.sort(
            key=lambda x: x.metadata.priority.value,
            reverse=True,
        )
        
        # Create new context with prioritized chunks
        prioritized_context = Context(
            context_id=context.context_id,
            chunks=filtered_chunks,
            metadata=context.metadata,
        )
        
        return prioritized_context


# =============================================================================
# Merge Context Assembler
# =============================================================================


class MergeAssembler(BaseContextAssembler):
    """
    Context assembler that merges similar chunks.
    
    This assembler supports:
    - Semantic merging of similar chunks
    - Content-based merging
    - Configurable merge strategies
    """
    
    def __init__(self, config: Optional[AssemblyConfig] = None):
        """
        Initialize the merge assembler.
        
        Args:
            config: Configuration for the assembler
        """
        super().__init__(config)
        self._merge_strategy = config.merge_strategy if config else "concatenate"
    
    async def merge(
        self,
        context: Context,
        config: Optional[Dict[str, Any]] = None,
    ) -> Context:
        """Merge similar chunks in a context."""
        if not context.chunks:
            return context
        
        # Group chunks by similarity
        groups = await self._group_similar_chunks(context.chunks)
        
        # Merge chunks in each group
        merged_chunks = []
        for group in groups:
            if len(group) == 1:
                merged_chunks.append(group[0])
            else:
                merged_chunk = await self._merge_chunks(group)
                merged_chunks.append(merged_chunk)
        
        # Create new context with merged chunks
        merged_context = Context(
            context_id=context.context_id,
            chunks=merged_chunks,
            metadata=context.metadata,
        )
        
        return merged_context
    
    async def _group_similar_chunks(
        self,
        chunks: List[ContextChunk],
    ) -> List[List[ContextChunk]]:
        """Group similar chunks together."""
        # Simple implementation: group by source
        # In a real implementation, this would use embeddings and similarity
        groups = {}
        for chunk in chunks:
            source = chunk.metadata.source.name
            if source not in groups:
                groups[source] = []
            groups[source].append(chunk)
        
        return list(groups.values())
    
    async def _merge_chunks(self, chunks: List[ContextChunk]) -> ContextChunk:
        """Merge multiple chunks into one."""
        if self._merge_strategy == "concatenate":
            # Simple concatenation
            merged_content = "\n\n".join(chunk.content for chunk in chunks)
            merged_token_count = sum(chunk.token_count for chunk in chunks)
            
            # Use metadata from the first chunk
            first_chunk = chunks[0]
            merged_chunk = ContextChunk(
                chunk_id=str(uuid4()),
                content=merged_content,
                metadata=first_chunk.metadata,
                token_count=merged_token_count,
                source_info=first_chunk.source_info,
            )
            return merged_chunk
        
        elif self._merge_strategy == "summarize":
            # In a real implementation, this would use an LLM to summarize
            # For now, just concatenate
            return await self._merge_chunks(chunks)  # Fallback to concatenate
        
        else:
            # Default to concatenate
            return await self._merge_chunks(chunks)


# =============================================================================
# Context Assembler (Main Implementation)
# =============================================================================


class ContextAssembler(MultiSourceAssembler):
    """
    Main context assembler implementation.
    
    This class provides a comprehensive context assembly system with support for:
    - Multi-source assembly (parallel, sequential, merge, priority)
    - Context prioritization
    - Context merging
    - Context deduplication
    - Context validation
    - Metadata enrichment
    - Source attribution
    
    Example:
        ```python
        from tangku_agentos.context_engine import ContextAssembler, ContextSource
        
        # Create the assembler
        assembler = ContextAssembler()
        
        # Add sources
        await assembler.add_source("memory", memory_provider)
        await assembler.add_source("knowledge", knowledge_provider)
        
        # Assemble context
        result = await assembler.assemble([
            {"source": "memory", "query": "recent conversation"},
            {"source": "knowledge", "query": "relevant documents"},
        ])
        
        # Get the assembled context
        context = result.context
        print(f"Assembled {len(context.chunks)} chunks from {len(result.sources_used)} sources")
        ```
    """
    
    def __init__(self, config: Optional[AssemblyConfig] = None):
        """
        Initialize the context assembler.
        
        Args:
            config: Configuration for the assembler
        """
        super().__init__(config)
        self._metadata_enricher = None
    
    async def initialize(self, config: Optional[Dict[str, Any]] = None) -> None:
        """Initialize the context assembler."""
        await super().initialize(config)
        
        # Initialize metadata enricher
        from .builder import MetadataEnricher
        self._metadata_enricher = MetadataEnricher()
    
    async def assemble(
        self,
        sources: List[Dict[str, Any]],
        config: Optional[AssemblyConfig] = None,
    ) -> ContextAssemblyResult:
        """Assemble context from multiple sources."""
        # Call the parent implementation
        result = await super().assemble(sources, config)
        
        # Enrich metadata
        if self._metadata_enricher:
            result.context = await self._metadata_enricher.enrich(result.context)
        
        return result
    
    async def prioritize(
        self,
        context: Context,
        config: Optional[Dict[str, Any]] = None,
    ) -> Context:
        """Prioritize chunks in a context."""
        # Use priority assembler for prioritization
        priority_assembler = PriorityAssembler(self.config)
        return await priority_assembler.prioritize(context, config)
    
    async def merge(
        self,
        context: Context,
        config: Optional[Dict[str, Any]] = None,
    ) -> Context:
        """Merge chunks in a context."""
        # Use merge assembler for merging
        merge_assembler = MergeAssembler(self.config)
        return await merge_assembler.merge(context, config)
    
    async def deduplicate(
        self,
        context: Context,
        config: Optional[Dict[str, Any]] = None,
    ) -> Context:
        """Remove duplicate chunks from a context."""
        # Use semantic deduplication if available
        if hasattr(self, "_semantic_deduplication"):
            return await self._semantic_deduplication(context)
        else:
            return await super().deduplicate(context)
    
    async def _semantic_deduplication(self, context: Context) -> Context:
        """Remove semantically similar chunks from a context."""
        # In a real implementation, this would use embeddings and similarity
        # For now, fall back to content-based deduplication
        return await super().deduplicate(context)
    
    async def add_source(
        self,
        source_name: str,
        source: Any,
        priority: Optional[int] = None,
    ) -> None:
        """Add a context source to the assembler."""
        await super().add_source(source_name, source, priority)
        logger.info(f"Added context source: {source_name} (priority: {priority})")
    
    async def remove_source(self, source_name: str) -> None:
        """Remove a context source from the assembler."""
        await super().remove_source(source_name)
        logger.info(f"Removed context source: {source_name}")
