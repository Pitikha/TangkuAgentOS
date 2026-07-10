"""
Retrieval Pipeline for TangkuAgentOS AI Foundation Framework.

Implements Retrieval-Augmented Generation (RAG) for knowledge and memory.
"""
from typing import Any, Optional, Dict, List
from dataclasses import dataclass, field
import logging
from .hybrid_retrieval import HybridRetriever
from ..knowledge.knowledge_connector import KnowledgeConnector
from ..memory.memory_connector import MemoryConnector

logger = logging.getLogger(__name__)


@dataclass
class RetrievalResult:
    """Result of a retrieval operation."""
    query: str
    results: List[Dict[str, Any]]
    scores: List[float]
    source: str


class RetrievalPipeline:
    """Manages retrieval for knowledge and memory in TangkuAgentOS.

    This class provides a unified interface for retrieving information
    from knowledge and memory using various strategies.
    """

    def __init__(
        self,
        knowledge_connector: KnowledgeConnector,
        memory_connector: MemoryConnector,
    ):
        """Initialize the RetrievalPipeline.

        Args:
            knowledge_connector: The KnowledgeConnector instance to use.
            memory_connector: The MemoryConnector instance to use.
        """
        self._knowledge_connector = knowledge_connector
        self._memory_connector = memory_connector
        self._hybrid_retriever = HybridRetriever(knowledge_connector, memory_connector)
        logger.info("RetrievalPipeline initialized.")

    async def retrieve(
        self,
        query: str,
        sources: Optional[List[str]] = None,
        limit: int = 10,
    ) -> List[RetrievalResult]:
        """Retrieve relevant information from knowledge and memory.

        Args:
            query: The retrieval query.
            sources: List of sources to retrieve from (e.g., ["knowledge", "memory"]).
            limit: Maximum number of results to return.

        Returns:
            List of RetrievalResult objects.
        """
        results = []

        if not sources or "knowledge" in sources:
            knowledge_results = await self._knowledge_connector.search(query, limit=limit)
            results.append(
                RetrievalResult(
                    query=query,
                    results=knowledge_results,
                    scores=[1.0] * len(knowledge_results),
                    source="knowledge",
                )
            )

        if not sources or "memory" in sources:
            memory_results = await self._memory_connector.search(query, limit=limit)
            results.append(
                RetrievalResult(
                    query=query,
                    results=memory_results,
                    scores=[1.0] * len(memory_results),
                    source="memory",
                )
            )

        logger.info(f"Retrieved {len(results)} results for query: {query[:50]}...")
        return results

    async def hybrid_retrieve(
        self,
        query: str,
        sources: Optional[List[str]] = None,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        """Perform hybrid retrieval (semantic + keyword).

        Args:
            query: The retrieval query.
            sources: List of sources to retrieve from.
            limit: Maximum number of results to return.

        Returns:
            List of combined retrieval results.
        """
        retrieval_results = await self.retrieve(query, sources, limit)
        combined_results = []
        for result in retrieval_results:
            combined_results.extend(result.results)
        return combined_results[:limit]

    async def semantic_retrieve(
        self,
        query: str,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        """Perform semantic retrieval.

        Args:
            query: The retrieval query.
            limit: Maximum number of results to return.

        Returns:
            List of semantic retrieval results.
        """
        return await self._knowledge_connector.search(query, limit=limit)

    async def keyword_retrieve(
        self,
        query: str,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        """Perform keyword-based retrieval.

        Args:
            query: The retrieval query.
            limit: Maximum number of results to return.

        Returns:
            List of keyword-based retrieval results.
        """
        # Placeholder: In a real implementation, this would use keyword search
        return await self._knowledge_connector.search(query, limit=limit)
