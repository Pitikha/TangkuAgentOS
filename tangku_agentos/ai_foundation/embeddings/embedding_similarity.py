"""
Embedding Similarity for TangkuAgentOS AI Foundation Framework.

Calculates similarity between embeddings using various metrics.
"""
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
import logging
import math
import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class SimilarityResult:
    """Result of a similarity calculation."""
    similarity: float
    metric: str
    metadata: Dict[str, Any] = field(default_factory=dict)


class EmbeddingSimilarity:
    """Calculates similarity between embeddings for TangkuAgentOS.

    This class provides methods for calculating similarity between
    embedding vectors using various metrics (e.g., cosine, Euclidean, dot product).
    """

    def __init__(self):
        """Initialize the EmbeddingSimilarity."""
        logger.info("EmbeddingSimilarity initialized.")

    def cosine_similarity(
        self,
        embedding1: List[float],
        embedding2: List[float],
    ) -> SimilarityResult:
        """Calculate cosine similarity between two embeddings.

        Args:
            embedding1: The first embedding vector.
            embedding2: The second embedding vector.

        Returns:
            SimilarityResult containing the cosine similarity score.
        """
        try:
            dot_product = np.dot(embedding1, embedding2)
            norm1 = np.linalg.norm(embedding1)
            norm2 = np.linalg.norm(embedding2)
            similarity = dot_product / (norm1 * norm2) if (norm1 * norm2) != 0 else 0.0
            return SimilarityResult(
                similarity=float(similarity),
                metric="cosine",
            )
        except Exception as e:
            logger.error(f"Error calculating cosine similarity: {e}")
            return SimilarityResult(
                similarity=0.0,
                metric="cosine",
                metadata={"error": str(e)},
            )

    def euclidean_distance(
        self,
        embedding1: List[float],
        embedding2: List[float],
    ) -> SimilarityResult:
        """Calculate Euclidean distance between two embeddings.

        Args:
            embedding1: The first embedding vector.
            embedding2: The second embedding vector.

        Returns:
            SimilarityResult containing the Euclidean distance.
        """
        try:
            distance = math.sqrt(sum((a - b) ** 2 for a, b in zip(embedding1, embedding2)))
            # Convert distance to similarity (inverse relationship)
            similarity = 1.0 / (1.0 + distance)
            return SimilarityResult(
                similarity=float(similarity),
                metric="euclidean",
            )
        except Exception as e:
            logger.error(f"Error calculating Euclidean distance: {e}")
            return SimilarityResult(
                similarity=0.0,
                metric="euclidean",
                metadata={"error": str(e)},
            )

    def dot_product(
        self,
        embedding1: List[float],
        embedding2: List[float],
    ) -> SimilarityResult:
        """Calculate dot product similarity between two embeddings.

        Args:
            embedding1: The first embedding vector.
            embedding2: The second embedding vector.

        Returns:
            SimilarityResult containing the dot product similarity score.
        """
        try:
            dot_product = np.dot(embedding1, embedding2)
            return SimilarityResult(
                similarity=float(dot_product),
                metric="dot_product",
            )
        except Exception as e:
            logger.error(f"Error calculating dot product: {e}")
            return SimilarityResult(
                similarity=0.0,
                metric="dot_product",
                metadata={"error": str(e)},
            )

    def batch_similarity(
        self,
        query_embedding: List[float],
        target_embeddings: List[List[float]],
        metric: str = "cosine",
    ) -> List[SimilarityResult]:
        """Calculate similarity between a query embedding and a list of target embeddings.

        Args:
            query_embedding: The query embedding vector.
            target_embeddings: List of target embedding vectors.
            metric: The similarity metric to use (e.g., "cosine", "euclidean", "dot_product").

        Returns:
            List of SimilarityResult objects for each target embedding.
        """
        similarity_func = getattr(self, metric, self.cosine_similarity)
        results = []
        for target_embedding in target_embeddings:
            result = similarity_func(query_embedding, target_embedding)
            results.append(result)
        return results

    def find_most_similar(
        self,
        query_embedding: List[float],
        target_embeddings: List[List[float]],
        metric: str = "cosine",
        top_k: int = 1,
    ) -> List[SimilarityResult]:
        """Find the most similar embeddings to a query embedding.

        Args:
            query_embedding: The query embedding vector.
            target_embeddings: List of target embedding vectors.
            metric: The similarity metric to use.
            top_k: Number of most similar embeddings to return.

        Returns:
            List of SimilarityResult objects for the most similar embeddings.
        """
        results = self.batch_similarity(query_embedding, target_embeddings, metric)
        results.sort(key=lambda x: x.similarity, reverse=True)
        return results[:top_k]
