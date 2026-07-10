"""
Keyword Search for TangkuAgentOS AI Foundation Framework.

Performs keyword-based search on knowledge and memory.
"""
from typing import Any, Optional, Dict, List
from dataclasses import dataclass, field
import logging
import re
from collections import defaultdict

logger = logging.getLogger(__name__)


@dataclass
class KeywordSearchResult:
    """Result of a keyword search operation."""
    query: str
    results: List[Dict[str, Any]]
    scores: List[float]
    metadata: Dict[str, Any] = field(default_factory=dict)


class KeywordSearcher:
    """Performs keyword-based search for TangkuAgentOS.

    This class provides methods for performing keyword-based search
    on knowledge and memory entries, returning results ranked by relevance.
    """

    def __init__(self):
        """Initialize the KeywordSearcher."""
        logger.info("KeywordSearcher initialized.")

    async def search(
        self,
        query: str,
        target_data: List[Dict[str, Any]],
        text_key: str = "content",
        top_k: int = 10,
    ) -> KeywordSearchResult:
        """Perform keyword-based search on a list of target data.

        Args:
            query: The search query.
            target_data: List of dictionaries containing text to search.
            text_key: The key in the dictionaries containing the text to search.
            top_k: Number of top results to return.

        Returns:
            KeywordSearchResult containing the search results.
        """
        # Tokenize the query
        query_terms = self._tokenize(query)
        if not query_terms:
            return KeywordSearchResult(
                query=query,
                results=[],
                scores=[],
                metadata={"error": "No valid query terms"},
            )

        # Score each target
        scored_results = []
        for item in target_data:
            text = item.get(text_key, "")
            score = self._calculate_score(text, query_terms)
            if score > 0:
                scored_results.append({
                    "text": text,
                    "score": score,
                    "metadata": item,
                })

        # Sort by score and limit
        scored_results.sort(key=lambda x: x["score"], reverse=True)
        results = scored_results[:top_k]
        scores = [result["score"] for result in results]

        logger.info(f"Performed keyword search for query: {query[:50]}...")
        return KeywordSearchResult(
            query=query,
            results=results,
            scores=scores,
            metadata={"top_k": top_k, "query_terms": query_terms},
        )

    def _tokenize(self, text: str) -> List[str]:
        """Tokenize text into terms.

        Args:
            text: The text to tokenize.

        Returns:
            List of tokens (terms).
        """
        # Simple tokenization: split on whitespace and remove punctuation
        text = re.sub(r'[\W_]+', ' ', text.lower())
        return [term for term in text.split() if term]

    def _calculate_score(self, text: str, query_terms: List[str]) -> float:
        """Calculate the relevance score for a text based on query terms.

        Args:
            text: The text to score.
            query_terms: List of query terms.

        Returns:
            Relevance score between 0.0 and 1.0.
        """
        if not query_terms:
            return 0.0

        text_terms = self._tokenize(text)
        term_counts = defaultdict(int)
        for term in text_terms:
            term_counts[term] += 1

        # Calculate term frequency scores
        scores = []
        for query_term in query_terms:
            if query_term in term_counts:
                # TF-IDF-like scoring (simplified)
                tf = term_counts[query_term] / len(text_terms) if text_terms else 0
                idf = 1.0  # Placeholder: in a real implementation, this would use IDF
                scores.append(tf * idf)

        # Return average score
        return sum(scores) / len(query_terms) if scores else 0.0

    async def search_with_boost(
        self,
        query: str,
        target_data: List[Dict[str, Any]],
        text_key: str = "content",
        boost_fields: Optional[Dict[str, float]] = None,
        top_k: int = 10,
    ) -> KeywordSearchResult:
        """Perform keyword search with field boosting.

        Args:
            query: The search query.
            target_data: List of dictionaries containing text to search.
            text_key: The key in the dictionaries containing the text to search.
            boost_fields: Dictionary of field names and their boost factors.
            top_k: Number of top results to return.

        Returns:
            KeywordSearchResult containing the search results.
        """
        boost_fields = boost_fields or {}
        query_terms = self._tokenize(query)

        scored_results = []
        for item in target_data:
            score = 0.0
            for field, boost in boost_fields.items():
                if field in item:
                    field_score = self._calculate_score(item[field], query_terms)
                    score += field_score * boost
            if text_key in item:
                text_score = self._calculate_score(item[text_key], query_terms)
                score += text_score

            if score > 0:
                scored_results.append({
                    "text": item.get(text_key, ""),
                    "score": score,
                    "metadata": item,
                })

        scored_results.sort(key=lambda x: x["score"], reverse=True)
        results = scored_results[:top_k]
        scores = [result["score"] for result in results]

        return KeywordSearchResult(
            query=query,
            results=results,
            scores=scores,
            metadata={"top_k": top_k, "boost_fields": boost_fields},
        )
