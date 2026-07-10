"""
Knowledge Retrieval for TangkuAgentOS AI Foundation Framework.

This module handles advanced retrieval operations for knowledge,
including semantic search, filtering, and context-aware retrieval.
"""

from typing import Any, Optional, Dict, List, Union
from dataclasses import dataclass, field
import logging
from enum import Enum
from .knowledge_connector import KnowledgeConnector, KnowledgeType

logger = logging.getLogger(__name__)


class RetrievalStrategy(Enum):
    """Strategies for knowledge retrieval."""
    EXACT = "exact"
    SEMANTIC = "semantic"
    HYBRID = "hybrid"
    CONTEXT_AWARE = "context_aware"


@dataclass
class RetrievalResult:
    """Result of a knowledge retrieval operation."""
    query: str
    results: List[Dict[str, Any]]
    scores: List[float]
    knowledge_types: List[KnowledgeType]
    strategy: RetrievalStrategy
    metadata: Dict[str, Any] = field(default_factory=dict)


class KnowledgeRetriever:
    """Handles advanced retrieval of knowledge for TangkuAgentOS.

    This class provides methods for retrieving knowledge using various strategies,
    including semantic search, filtering, and context-aware retrieval.
    """

    def __init__(self, knowledge_connector: KnowledgeConnector):
        """Initialize the KnowledgeRetriever.

        Args:
            knowledge_connector: The KnowledgeConnector instance to use for retrieval.
        """
        self._knowledge_connector = knowledge_connector
        logger.info("KnowledgeRetriever initialized.")

    async def retrieve(
        self,
        query: str,
        knowledge_types: Optional[List[KnowledgeType]] = None,
        limit: int = 10,
        strategy: RetrievalStrategy = RetrievalStrategy.SEMANTIC,
        confidence_threshold: float = 0.5,
    ) -> RetrievalResult:
        """Retrieve knowledge entries matching a query using the specified strategy.

        Args:
            query: The retrieval query.
            knowledge_types: List of knowledge types to retrieve from.
            limit: Maximum number of results to return.
            strategy: The retrieval strategy to use.
            confidence_threshold: Minimum confidence score for results.

        Returns:
            RetrievalResult containing the results and metadata.
        """
        logger.debug(f"Retrieving knowledge with strategy: {strategy.value}")

        if strategy == RetrievalStrategy.EXACT:
            results = await self._exact_retrieval(query, knowledge_types, limit)
        elif strategy == RetrievalStrategy.SEMANTIC:
            results = await self._semantic_retrieval(query, knowledge_types, limit, confidence_threshold)
        elif strategy == RetrievalStrategy.HYBRID:
            results = await self._hybrid_retrieval(query, knowledge_types, limit, confidence_threshold)
        elif strategy == RetrievalStrategy.CONTEXT_AWARE:
            results = await self._context_aware_retrieval(query, knowledge_types, limit, confidence_threshold)
        else:
            results = await self._semantic_retrieval(query, knowledge_types, limit, confidence_threshold)

        knowledge_types_list = knowledge_types or [
            KnowledgeType.DOCUMENT,
            KnowledgeType.REPOSITORY,
            KnowledgeType.CODE,
        ]
        return RetrievalResult(
            query=query,
            results=results["results"],
            scores=results["scores"],
            knowledge_types=knowledge_types_list,
            strategy=strategy,
            metadata={"total_results": len(results["results"])},
        )

    async def _exact_retrieval(
        self,
        query: str,
        knowledge_types: Optional[List[KnowledgeType]] = None,
        limit: int = 10,
    ) -> Dict[str, Any]:
        """Perform exact retrieval of knowledge entries."""
        results = await self._knowledge_connector.search(
            query,
            knowledge_types,
            limit,
            confidence_threshold=1.0,
        )
        scores = [1.0] * len(results)
        return {"results": results, "scores": scores}

    async def _semantic_retrieval(
        self,
        query: str,
        knowledge_types: Optional[List[KnowledgeType]] = None,
        limit: int = 10,
        confidence_threshold: float = 0.5,
    ) -> Dict[str, Any]:
        """Perform semantic retrieval of knowledge entries."""
        results = await self._knowledge_connector.search(
            query,
            knowledge_types,
            limit,
            confidence_threshold,
        )
        scores = [result.get("score", 0.5) for result in results]
        return {"results": results, "scores": scores}

    async def _hybrid_retrieval(
        self,
        query: str,
        knowledge_types: Optional[List[KnowledgeType]] = None,
        limit: int = 10,
        confidence_threshold: float = 0.5,
    ) -> Dict[str, Any]:
        """Perform hybrid (exact + semantic) retrieval of knowledge entries."""
        exact_results = await self._exact_retrieval(query, knowledge_types, limit // 2)
        semantic_results = await self._semantic_retrieval(query, knowledge_types, limit // 2, confidence_threshold)

        combined_results = exact_results["results"] + semantic_results["results"]
        combined_scores = exact_results["scores"] + semantic_results["scores"]

        sorted_results = sorted(
            zip(combined_results, combined_scores),
            key=lambda x: x[1],
            reverse=True,
        )[:limit]

        results, scores = zip(*sorted_results) if sorted_results else ([], [])
        return {"results": list(results), "scores": list(scores)}

    async def _context_aware_retrieval(
        self,
        query: str,
        knowledge_types: Optional[List[KnowledgeType]] = None,
        limit: int = 10,
        confidence_threshold: float = 0.5,
    ) -> Dict[str, Any]:
        """Perform context-aware retrieval of knowledge entries."""
        return await self._semantic_retrieval(query, knowledge_types, limit, confidence_threshold)

    async def retrieve_by_metadata(
        self,
        metadata: Dict[str, Any],
        knowledge_types: Optional[List[KnowledgeType]] = None,
        limit: int = 10,
    ) -> RetrievalResult:
        """Retrieve knowledge entries matching specific metadata.

        Args:
            metadata: Metadata to match against.
            knowledge_types: List of knowledge types to retrieve from.
            limit: Maximum number of results to return.

        Returns:
            RetrievalResult containing the results and metadata.
        """
        logger.debug(f"Retrieving knowledge by metadata: {metadata}")
        knowledge_types_list = knowledge_types or [
            KnowledgeType.DOCUMENT,
            KnowledgeType.REPOSITORY,
            KnowledgeType.CODE,
        ]
        return RetrievalResult(
            query=str(metadata),
            results=[],
            scores=[],
            knowledge_types=knowledge_types_list,
            strategy=RetrievalStrategy.EXACT,
        )
