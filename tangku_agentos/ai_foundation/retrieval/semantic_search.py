"""
Semantic Search for TangkuAgentOS AI Foundation Framework.

Performs semantic search using embeddings.
"""
from typing import Any, Optional, Dict, List
from dataclasses import dataclass, field
import logging
import numpy as np
from ..embeddings.embedding_registry import EmbeddingRegistry
from ..embeddings.embedding_similarity import EmbeddingSimilarity

logger = logging.getLogger(__name__)


@dataclass
class SemanticSearchResult:
    """Result of a semantic search operation."""
    query: str
    results: List[Dict[str, Any]]
    scores: List[float]
    metadata: Dict[str, Any] = field(default_factory=dict)


class SemanticSearcher:
    """Performs semantic search for TangkuAgentOS.

    This class uses embeddings to perform semantic search on knowledge
    and memory entries, returning results ranked by relevance.
    """

    def __init__(
        self,
        embedding_registry: EmbeddingRegistry,
        embedding_similarity: EmbeddingSimilarity,
    ):
        """Initialize the SemanticSearcher.

        Args:
            embedding_registry: The EmbeddingRegistry instance to use.
            embedding_similarity: The EmbeddingSimilarity instance to use.
        """
        self._embedding_registry = embedding_registry
        self._embedding_similarity = embedding_similarity
        logger.info("SemanticSearcher initialized.")

    async def search(
        self,
        query: str,
        target_texts: List[str],
        model_name: str = "default",
        top_k: int = 10,
        **kwargs: Any,
    ) -> SemanticSearchResult:
        """Perform semantic search on a list of target texts.

        Args:
            query: The search query.
            target_texts: List of texts to search within.
            model_name: The name of the embedding model to use.
            top_k: Number of top results to return.
            **kwargs: Additional arguments for the embedding model.

        Returns:
            SemanticSearchResult containing the search results.
        """
        # Generate embedding for the query
        query_embedding = await self._embedding_registry.embed(query, model_name=model_name, **kwargs)

        # Generate embeddings for all target texts
        target_embeddings = await self._embedding_registry.embed_batch(
            target_texts, model_name=model_name, **kwargs
        )

        # Calculate similarity scores
        similarity_results = self._embedding_similarity.batch_similarity(
            query_embedding, target_embeddings
        )

        # Sort by similarity score
        sorted_results = sorted(
            zip(target_texts, [r.similarity for r in similarity_results]),
            key=lambda x: x[1],
            reverse=True,
        )

        results = [
            {"text": text, "score": score}
            for text, score in sorted_results[:top_k]
        ]
        scores = [result["score"] for result in results]

        logger.info(f"Performed semantic search for query: {query[:50]}...")
        return SemanticSearchResult(
            query=query,
            results=results,
            scores=scores,
            metadata={"model": model_name, "top_k": top_k},
        )

    async def search_with_metadata(
        self,
        query: str,
        target_data: List[Dict[str, Any]],
        text_key: str = "content",
        model_name: str = "default",
        top_k: int = 10,
        **kwargs: Any,
    ) -> SemanticSearchResult:
        """Perform semantic search on data with metadata.

        Args:
            query: The search query.
            target_data: List of dictionaries containing text and metadata.
            text_key: The key in the dictionaries containing the text to search.
            model_name: The name of the embedding model to use.
            top_k: Number of top results to return.
            **kwargs: Additional arguments for the embedding model.

        Returns:
            SemanticSearchResult containing the search results with metadata.
        """
        target_texts = [item.get(text_key, "") for item in target_data]
        search_result = await self.search(query, target_texts, model_name, top_k, **kwargs)

        # Include metadata in results
        results_with_metadata = []
        for i, result in enumerate(search_result.results):
            if i < len(target_data):
                result["metadata"] = target_data[i]
            results_with_metadata.append(result)

        return SemanticSearchResult(
            query=query,
            results=results_with_metadata,
            scores=search_result.scores,
            metadata=search_result.metadata,
        )

    async def find_similar(
        self,
        text: str,
        target_texts: List[str],
        model_name: str = "default",
        top_k: int = 5,
        **kwargs: Any,
    ) -> List[Dict[str, Any]]:
        """Find texts similar to a given text.

        Args:
            text: The text to find similar texts for.
            target_texts: List of texts to compare against.
            model_name: The name of the embedding model to use.
            top_k: Number of similar texts to return.
            **kwargs: Additional arguments for the embedding model.

        Returns:
            List of similar texts with their similarity scores.
        """
        search_result = await self.search(text, target_texts, model_name, top_k, **kwargs)
        return [
            {"text": result["text"], "score": score}
            for result, score in zip(search_result.results, search_result.scores)
        ]
