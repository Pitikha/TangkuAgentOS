"""
Hybrid Retrieval for TangkuAgentOS AI Foundation Framework.

Combines semantic and keyword-based retrieval for improved results.
"""
from typing import Any, Optional, Dict, List
from dataclasses import dataclass, field
import logging
from ..knowledge.knowledge_connector import KnowledgeConnector
from ..memory.memory_connector import MemoryConnector

logger = logging.getLogger(__name__)


@dataclass
class HybridResult:
    """Result of a hybrid retrieval operation."""
    query: str
    semantic_results: List[Dict[str, Any]]
    keyword_results: List[Dict[str, Any]]
    combined_results: List[Dict[str, Any]]
    metadata: Dict[str, Any] = field(default_factory=dict)


class HybridRetriever:
    """Performs hybrid retrieval for TangkuAgentOS.

    This class combines semantic and keyword-based retrieval to
    provide more comprehensive and accurate results.
    """

    def __init__(
        self,
        knowledge_connector: KnowledgeConnector,
        memory_connector: MemoryConnector,
    ):
        """Initialize the HybridRetriever.

        Args:
            knowledge_connector: The KnowledgeConnector instance to use.
            memory_connector: The MemoryConnector instance to use.
        """
        self._knowledge_connector = knowledge_connector
        self._memory_connector = memory_connector
        logger.info("HybridRetriever initialized.")

    async def retrieve(
        self,
        query: str,
        sources: Optional[List[str]] = None,
        limit: int = 10,
    ) -> HybridResult:
        """Perform hybrid retrieval (semantic + keyword).

        Args:
            query: The retrieval query.
            sources: List of sources to retrieve from (e.g., ["knowledge", "memory"]).
            limit: Maximum number of results to return.

        Returns:
            HybridResult containing semantic, keyword, and combined results.
        """
        semantic_results = []
        keyword_results = []

        if not sources or "knowledge" in sources:
            semantic_results = await self._knowledge_connector.search(query, limit=limit)
            keyword_results = await self._knowledge_connector.search(query, limit=limit)

        if not sources or "memory" in sources:
            semantic_memory_results = await self._memory_connector.search(query, limit=limit // 2)
            keyword_memory_results = await self._memory_connector.search(query, limit=limit // 2)
            semantic_results.extend(semantic_memory_results)
            keyword_results.extend(keyword_memory_results)

        combined_results = self._combine_results(semantic_results, keyword_results, limit)

        logger.info(f"Performed hybrid retrieval for query: {query[:50]}...")
        return HybridResult(
            query=query,
            semantic_results=semantic_results,
            keyword_results=keyword_results,
            combined_results=combined_results,
            metadata={"total_results": len(combined_results)},
        )

    def _combine_results(
        self,
        semantic_results: List[Dict[str, Any]],
        keyword_results: List[Dict[str, Any]],
        limit: int,
    ) -> List[Dict[str, Any]]:
        """Combine semantic and keyword results.

        Args:
            semantic_results: List of semantic retrieval results.
            keyword_results: List of keyword retrieval results.
            limit: Maximum number of results to return.

        Returns:
            List of combined and deduplicated results.
        """
        combined = semantic_results + keyword_results
        # Deduplicate by ID
        seen_ids = set()
        deduplicated = []
        for result in combined:
            result_id = result.get("id", "")
            if result_id not in seen_ids:
                seen_ids.add(result_id)
                deduplicated.append(result)
        # Sort by score (if available) and limit
        deduplicated.sort(key=lambda x: x.get("score", 0.0), reverse=True)
        return deduplicated[:limit]

    async def retrieve_with_weights(
        self,
        query: str,
        semantic_weight: float = 0.7,
        keyword_weight: float = 0.3,
        limit: int = 10,
    ) -> HybridResult:
        """Perform weighted hybrid retrieval.

        Args:
            query: The retrieval query.
            semantic_weight: Weight for semantic results (0.0 to 1.0).
            keyword_weight: Weight for keyword results (0.0 to 1.0).
            limit: Maximum number of results to return.

        Returns:
            HybridResult containing weighted combined results.
        """
        semantic_results = await self._knowledge_connector.search(query, limit=limit)
        keyword_results = await self._knowledge_connector.search(query, limit=limit)

        # Apply weights to scores
        for result in semantic_results:
            result["weighted_score"] = result.get("score", 0.5) * semantic_weight
        for result in keyword_results:
            result["weighted_score"] = result.get("score", 0.5) * keyword_weight

        combined = semantic_results + keyword_results
        combined.sort(key=lambda x: x.get("weighted_score", 0.0), reverse=True)

        return HybridResult(
            query=query,
            semantic_results=semantic_results,
            keyword_results=keyword_results,
            combined_results=combined[:limit],
            metadata={"semantic_weight": semantic_weight, "keyword_weight": keyword_weight},
        )
