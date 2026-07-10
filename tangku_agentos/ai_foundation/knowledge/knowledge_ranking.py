"""
Knowledge Ranking for TangkuAgentOS AI Foundation Framework.

This module handles ranking of knowledge entries based on relevance, confidence, and other metrics.
"""

from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
import logging
from datetime import datetime
from .knowledge_connector import KnowledgeType

logger = logging.getLogger(__name__)


@dataclass
class RankedKnowledge:
    """Represents a ranked knowledge entry."""
    knowledge_id: str
    knowledge_type: KnowledgeType
    data: Dict[str, Any]
    relevance_score: float
    confidence_score: float
    timestamp: datetime
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RankingResult:
    """Result of a knowledge ranking operation."""
    query: str
    ranked_knowledge: List[RankedKnowledge]
    metadata: Dict[str, Any] = field(default_factory=dict)


class KnowledgeRanker:
    """Handles ranking of knowledge entries for TangkuAgentOS.

    This class provides methods for ranking knowledge entries based on relevance,
    confidence, recency, and other metrics.
    """

    def __init__(self):
        """Initialize the KnowledgeRanker."""
        self._default_weights = {
            "relevance": 0.5,
            "confidence": 0.3,
            "recency": 0.2,
        }
        logger.info("KnowledgeRanker initialized.")

    async def rank(
        self,
        knowledge_entries: List[Dict[str, Any]],
        query: str,
        knowledge_types: Optional[List[KnowledgeType]] = None,
        limit: int = 10,
    ) -> RankingResult:
        """Rank knowledge entries based on relevance to a query.

        Args:
            knowledge_entries: List of knowledge entries to rank.
            query: The query to rank knowledge entries against.
            knowledge_types: Optional list of knowledge types to consider.
            limit: Maximum number of results to return.

        Returns:
            RankingResult containing the ranked knowledge entries.
        """
        ranked_knowledge = []
        for entry in knowledge_entries:
            relevance_score = self._calculate_relevance(entry, query)
            confidence_score = entry.get("confidence", 0.5)
            recency_score = self._calculate_recency(entry)

            composite_score = (
                self._default_weights["relevance"] * relevance_score +
                self._default_weights["confidence"] * confidence_score +
                self._default_weights["recency"] * recency_score
            )

            ranked_knowledge.append(
                RankedKnowledge(
                    knowledge_id=entry.get("id", ""),
                    knowledge_type=KnowledgeType(entry.get("knowledge_type", "document")),
                    data=entry,
                    relevance_score=relevance_score,
                    confidence_score=confidence_score,
                    timestamp=datetime.fromisoformat(entry.get("timestamp", datetime.utcnow().isoformat())),
                    metadata=entry.get("metadata", {}),
                )
            )

        ranked_knowledge.sort(
            key=lambda x: (
                x.relevance_score * self._default_weights["relevance"] +
                x.confidence_score * self._default_weights["confidence"] +
                self._calculate_recency_score(x.timestamp) * self._default_weights["recency"]
            ),
            reverse=True,
        )

        ranked_knowledge = ranked_knowledge[:limit]
        logger.info(f"Ranked {len(ranked_knowledge)} knowledge entries for query: {query[:50]}...")
        return RankingResult(
            query=query,
            ranked_knowledge=ranked_knowledge,
            metadata={"total_ranked": len(ranked_knowledge)},
        )

    def _calculate_relevance(self, entry: Dict[str, Any], query: str) -> float:
        """Calculate the relevance score for a knowledge entry.

        Args:
            entry: The knowledge entry to score.
            query: The query to score against.

        Returns:
            Relevance score between 0.0 and 1.0.
        """
        content = entry.get("content", "").lower()
        query_terms = query.lower().split()
        matches = sum(1 for term in query_terms if term in content)
        return min(matches / len(query_terms), 1.0) if query_terms else 0.0

    def _calculate_recency(self, entry: Dict[str, Any]) -> float:
        """Calculate the recency score for a knowledge entry.

        Args:
            entry: The knowledge entry to score.

        Returns:
            Recency score between 0.0 and 1.0.
        """
        timestamp_str = entry.get("timestamp", datetime.utcnow().isoformat())
        try:
            timestamp = datetime.fromisoformat(timestamp_str)
        except ValueError:
            timestamp = datetime.utcnow()

        time_diff = datetime.utcnow() - timestamp
        hours_diff = time_diff.total_seconds() / 3600
        return max(1.0 - (hours_diff / 168), 0.0)

    def _calculate_recency_score(self, timestamp: datetime) -> float:
        """Calculate the recency score for a timestamp.

        Args:
            timestamp: The timestamp to score.

        Returns:
            Recency score between 0.0 and 1.0.
        """
        time_diff = datetime.utcnow() - timestamp
        hours_diff = time_diff.total_seconds() / 3600
        return max(1.0 - (hours_diff / 168), 0.0)

    def set_weights(self, weights: Dict[str, float]) -> None:
        """Set the weights for ranking criteria.

        Args:
            weights: Dictionary of weights for relevance, confidence, and recency.
        """
        self._default_weights.update(weights)
        logger.info(f"Updated ranking weights: {self._default_weights}")
