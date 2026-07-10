"""
AI Foundation Framework - Retrieval Pipeline

This module provides the RetrievalPipeline class for implementing
Retrieval-Augmented Generation (RAG).
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from typing import Any, Dict, List, Optional, Set, TYPE_CHECKING

if TYPE_CHECKING:
    from tangku_agentos.ai_foundation.retrieval.result import RetrievalResult
    from tangku_agentos.ai_foundation.core.config import AIConfig
    from tangku_agentos.ai_foundation.core.foundation import AIFoundation

logger = logging.getLogger(__name__)


class RetrievalStrategy(Enum):
    """Strategy for retrieval."""
    SEMANTIC = auto()
    KEYWORD = auto()
    HYBRID = auto()
    GRAPH = auto()
    REPOSITORY = auto()
    WORKSPACE = auto()
    CUSTOM = auto()


@dataclass
class RetrievalPipelineMetrics:
    """Metrics for the retrieval pipeline."""
    retrievals: int = 0
    items_retrieved: int = 0
    memory_retrievals: int = 0
    knowledge_retrievals: int = 0
    embedding_operations: int = 0
    rerank_operations: int = 0
    errors: int = 0
    last_error: Optional[str] = None
    last_error_time: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "retrievals": self.retrievals,
            "items_retrieved": self.items_retrieved,
            "memory_retrievals": self.memory_retrievals,
            "knowledge_retrievals": self.knowledge_retrievals,
            "embedding_operations": self.embedding_operations,
            "rerank_operations": self.rerank_operations,
            "errors": self.errors,
            "last_error": self.last_error,
            "last_error_time": self.last_error_time.isoformat() if self.last_error_time else None,
        }


class RetrievalPipeline:
    """
    Pipeline for Retrieval-Augmented Generation (RAG).
    
    This class implements a comprehensive retrieval pipeline that combines
    information from multiple sources including memory, knowledge, and
    embeddings to provide relevant context for AI operations.
    
    Thread Safety:
        This class is thread-safe for concurrent access.
    
    Example:
        >>> from tangku_agentos.ai_foundation import RetrievalPipeline
        >>> 
        >>> # Create pipeline
        >>> pipeline = RetrievalPipeline()
        >>> 
        >>> # Retrieve information
        >>> result = await pipeline.retrieve("What is AI?")
        >>> 
        >>> # Get the best result
        >>> best = result.best_item
        >>> print(best.content)
    """

    def __init__(self, config: "AIConfig", foundation: "AIFoundation"):
        """
        Initialize the retrieval pipeline.
        
        Args:
            config: AI Foundation configuration.
            foundation: AI Foundation instance.
        """
        self._config = config
        self._foundation = foundation
        self._metrics = RetrievalPipelineMetrics()
        self._lock = asyncio.Lock()
        self._initialized = False
        self._started = False
        
        logger.info("RetrievalPipeline initialized")

    @property
    def config(self) -> "AIConfig":
        """Get the configuration."""
        return self._config

    @property
    def foundation(self) -> "AIFoundation":
        """Get the AI Foundation instance."""
        return self._foundation

    @property
    def metrics(self) -> RetrievalPipelineMetrics:
        """Get the retrieval pipeline metrics."""
        return self._metrics

    @property
    def is_initialized(self) -> bool:
        """Check if the pipeline is initialized."""
        return self._initialized

    @property
    def is_started(self) -> bool:
        """Check if the pipeline is started."""
        return self._started

    async def initialize(self) -> None:
        """
        Initialize the retrieval pipeline.
        """
        if self._initialized:
            logger.warning("RetrievalPipeline already initialized")
            return
        
        logger.info("Initializing RetrievalPipeline...")
        
        self._initialized = True
        logger.info("RetrievalPipeline initialized successfully")

    async def start(self) -> None:
        """
        Start the retrieval pipeline.
        """
        if self._started:
            logger.warning("RetrievalPipeline already started")
            return
        
        if not self._initialized:
            await self.initialize()
        
        logger.info("Starting RetrievalPipeline...")
        
        self._started = True
        logger.info("RetrievalPipeline started successfully")

    async def stop(self) -> None:
        """
        Stop the retrieval pipeline.
        """
        if not self._started:
            logger.warning("RetrievalPipeline not started")
            return
        
        logger.info("Stopping RetrievalPipeline...")
        
        self._started = False
        logger.info("RetrievalPipeline stopped successfully")

    async def retrieve(
        self,
        query: str,
        limit: int = 10,
        min_score: float = 0.0,
        strategy: Optional[RetrievalStrategy] = None,
        use_memory: bool = True,
        use_knowledge: bool = True,
        use_embeddings: bool = True,
        rerank: bool = True,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> "RetrievalResult":
        """
        Retrieve information relevant to the query.
        
        This method implements the full retrieval pipeline:
        1. Retrieve from memory (if enabled)
        2. Retrieve from knowledge (if enabled)
        3. Generate embeddings and search (if enabled)
        4. Combine and rerank results (if enabled)
        
        Args:
            query: Search query.
            limit: Maximum number of results to return.
            min_score: Minimum relevance score for results.
            strategy: Retrieval strategy to use.
            use_memory: Whether to use memory retrieval.
            use_knowledge: Whether to use knowledge retrieval.
            use_embeddings: Whether to use embedding-based retrieval.
            rerank: Whether to rerank results.
            metadata: Additional metadata.
        
        Returns:
            RetrievalResult with retrieved information.
        """
        from tangku_agentos.ai_foundation.retrieval.result import RetrievalResult, RetrievedItem, RetrievalSource
        
        async with self._lock:
            self._metrics.retrievals += 1
            
            try:
                # Determine strategy
                actual_strategy = strategy or self._get_default_strategy()
                
                # Create result
                result = RetrievalResult(
                    query=query,
                    strategy=actual_strategy,
                    metadata=metadata or {},
                )
                
                # Retrieve from different sources based on strategy
                if actual_strategy == RetrievalStrategy.SEMANTIC:
                    await self._retrieve_semantic(result, query, limit, use_memory, use_knowledge, use_embeddings)
                elif actual_strategy == RetrievalStrategy.KEYWORD:
                    await self._retrieve_keyword(result, query, limit, use_memory, use_knowledge)
                elif actual_strategy == RetrievalStrategy.HYBRID:
                    await self._retrieve_hybrid(result, query, limit, use_memory, use_knowledge, use_embeddings)
                elif actual_strategy == RetrievalStrategy.GRAPH:
                    await self._retrieve_graph(result, query, limit)
                elif actual_strategy == RetrievalStrategy.REPOSITORY:
                    await self._retrieve_repository(result, query, limit)
                elif actual_strategy == RetrievalStrategy.WORKSPACE:
                    await self._retrieve_workspace(result, query, limit)
                else:
                    await self._retrieve_hybrid(result, query, limit, use_memory, use_knowledge, use_embeddings)
                
                # Rerank results if enabled
                if rerank and result.count > 1:
                    await self._rerank_results(result)
                
                # Filter by minimum score
                result = result.filter_by_score(min_score)
                
                # Sort by score
                result.sort_by_score(descending=True)
                
                # Update metrics
                self._metrics.items_retrieved += result.count
                
                return result
                
            except Exception as e:
                self._metrics.errors += 1
                self._metrics.last_error = str(e)
                self._metrics.last_error_time = datetime.utcnow()
                logger.error(f"Retrieval failed: {e}")
                raise

    def _get_default_strategy(self) -> RetrievalStrategy:
        """Get the default retrieval strategy from configuration."""
        strategy_str = self._config.retrieval.retrieval_strategy
        try:
            return RetrievalStrategy[strategy_str.upper()]
        except (KeyError, ValueError):
            return RetrievalStrategy.HYBRID

    async def _retrieve_semantic(
        self,
        result: "RetrievalResult",
        query: str,
        limit: int,
        use_memory: bool,
        use_knowledge: bool,
        use_embeddings: bool,
    ) -> None:
        """Retrieve using semantic search."""
        from tangku_agentos.ai_foundation.retrieval.result import RetrievedItem, RetrievalSource
        
        # Use embeddings for semantic search
        if use_embeddings:
            self._metrics.embedding_operations += 1
            
            # In a real implementation, this would use the EmbeddingManager
            # For now, add mock results
            for i in range(min(limit, 3)):
                result.add_item(RetrievedItem(
                    content=f"Semantic result for: {query}",
                    source=RetrievalSource.EMBEDDING,
                    score=0.9 - (i * 0.1),
                    metadata={"type": "semantic"},
                ))

    async def _retrieve_keyword(
        self,
        result: "RetrievalResult",
        query: str,
        limit: int,
        use_memory: bool,
        use_knowledge: bool,
    ) -> None:
        """Retrieve using keyword search."""
        from tangku_agentos.ai_foundation.retrieval.result import RetrievedItem, RetrievalSource
        
        # Use keyword search
        # In a real implementation, this would use keyword-based search
        # For now, add mock results
        for i in range(min(limit, 3)):
            result.add_item(RetrievedItem(
                content=f"Keyword result for: {query}",
                source=RetrievalSource.KEYWORD,
                score=0.8 - (i * 0.1),
                metadata={"type": "keyword"},
            ))

    async def _retrieve_hybrid(
        self,
        result: "RetrievalResult",
        query: str,
        limit: int,
        use_memory: bool,
        use_knowledge: bool,
        use_embeddings: bool,
    ) -> None:
        """Retrieve using hybrid approach (semantic + keyword)."""
        # Retrieve from memory
        if use_memory and self._config.memory.enabled:
            await self._retrieve_from_memory(result, query, limit)
        
        # Retrieve from knowledge
        if use_knowledge and self._config.knowledge.enabled:
            await self._retrieve_from_knowledge(result, query, limit)
        
        # Retrieve using embeddings
        if use_embeddings:
            await self._retrieve_semantic(result, query, limit, False, False, True)

    async def _retrieve_from_memory(
        self,
        result: "RetrievalResult",
        query: str,
        limit: int,
    ) -> None:
        """Retrieve from memory."""
        from tangku_agentos.ai_foundation.retrieval.result import RetrievedItem, RetrievalSource
        
        self._metrics.memory_retrievals += 1
        
        try:
            # Use MemoryConnector to retrieve from memory
            memory_result = await self._foundation.memory.retrieve(
                query=query,
                limit=limit,
            )
            
            # Add memory results
            for i, memory_item in enumerate(memory_result.results):
                result.add_item(RetrievedItem(
                    content=memory_item,
                    source=RetrievalSource.MEMORY,
                    score=memory_result.scores[i] if i < len(memory_result.scores) else 0.5,
                    metadata={"type": "memory"},
                ))
        
        except Exception as e:
            logger.warning(f"Memory retrieval failed: {e}")

    async def _retrieve_from_knowledge(
        self,
        result: "RetrievalResult",
        query: str,
        limit: int,
    ) -> None:
        """Retrieve from knowledge."""
        from tangku_agentos.ai_foundation.retrieval.result import RetrievedItem, RetrievalSource
        
        self._metrics.knowledge_retrievals += 1
        
        try:
            # Use KnowledgeConnector to retrieve from knowledge
            knowledge_result = await self._foundation.knowledge.retrieve(
                query=query,
                limit=limit,
            )
            
            # Add knowledge results
            for i, knowledge_item in enumerate(knowledge_result.results):
                result.add_item(RetrievedItem(
                    content=knowledge_item,
                    source=RetrievalSource.KNOWLEDGE,
                    score=knowledge_result.scores[i] if i < len(knowledge_result.scores) else 0.5,
                    metadata={"type": "knowledge"},
                ))
        
        except Exception as e:
            logger.warning(f"Knowledge retrieval failed: {e}")

    async def _retrieve_graph(
        self,
        result: "RetrievalResult",
        query: str,
        limit: int,
    ) -> None:
        """Retrieve using graph search."""
        from tangku_agentos.ai_foundation.retrieval.result import RetrievedItem, RetrievalSource
        
        # In a real implementation, this would use graph-based search
        # For now, add mock results
        for i in range(min(limit, 3)):
            result.add_item(RetrievedItem(
                content=f"Graph result for: {query}",
                source=RetrievalSource.GRAPH,
                score=0.85 - (i * 0.05),
                metadata={"type": "graph"},
            ))

    async def _retrieve_repository(
        self,
        result: "RetrievalResult",
        query: str,
        limit: int,
    ) -> None:
        """Retrieve from repository."""
        from tangku_agentos.ai_foundation.retrieval.result import RetrievedItem, RetrievalSource
        
        # In a real implementation, this would integrate with Repository Intelligence
        # For now, add mock results
        for i in range(min(limit, 3)):
            result.add_item(RetrievedItem(
                content=f"Repository result for: {query}",
                source=RetrievalSource.REPOSITORY,
                score=0.8 - (i * 0.1),
                metadata={"type": "repository"},
            ))

    async def _retrieve_workspace(
        self,
        result: "RetrievalResult",
        query: str,
        limit: int,
    ) -> None:
        """Retrieve from workspace."""
        from tangku_agentos.ai_foundation.retrieval.result import RetrievedItem, RetrievalSource
        
        # In a real implementation, this would integrate with Workspace Engine
        # For now, add mock results
        for i in range(min(limit, 3)):
            result.add_item(RetrievedItem(
                content=f"Workspace result for: {query}",
                source=RetrievalSource.WORKSPACE,
                score=0.75 - (i * 0.05),
                metadata={"type": "workspace"},
            ))

    async def _rerank_results(self, result: "RetrievalResult") -> None:
        """Rerank results using a more sophisticated algorithm."""
        self._metrics.rerank_operations += 1
        
        # In a real implementation, this would use a reranking model
        # For now, just sort by score
        result.sort_by_score(descending=True)

    async def get_info(self) -> Dict[str, Any]:
        """
        Get information about the retrieval pipeline.
        
        Returns:
            Dictionary with retrieval pipeline information.
        """
        return {
            "status": "active" if self._initialized and self._started else "inactive",
            "metrics": self._metrics.to_dict(),
            "config": {
                "strategy": self._get_default_strategy().value,
                "use_memory": self._config.memory.enabled,
                "use_knowledge": self._config.knowledge.enabled,
                "use_embeddings": self._config.embeddings.enabled,
                "rerank": self._config.retrieval.rerank_enabled,
            }
        }

    async def reset(self) -> None:
        """
        Reset the retrieval pipeline.
        
        This method resets all state and metrics.
        """
        logger.info("Resetting RetrievalPipeline...")
        
        self._metrics = RetrievalPipelineMetrics()
        self._initialized = False
        self._started = False
        
        logger.info("RetrievalPipeline reset successfully")

    def __repr__(self) -> str:
        """Return string representation."""
        return (
            f"RetrievalPipeline("
            f"initialized={self._initialized}, "
            f"started={self._started}, "
            f"retrievals={self._metrics.retrievals})"
        )
