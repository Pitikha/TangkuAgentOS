"""
Embedding Batch for TangkuAgentOS AI Foundation Framework.

Handles batch processing of embeddings for efficiency.
"""
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
import logging
import asyncio
from .embedding_registry import EmbeddingRegistry

logger = logging.getLogger(__name__)


@dataclass
class BatchResult:
    """Result of a batch embedding operation."""
    embeddings: List[List[float]]
    failed_indices: List[int]
    metadata: Dict[str, Any] = field(default_factory=dict)


class EmbeddingBatcher:
    """Handles batch processing of embeddings for TangkuAgentOS.

    This class provides methods for processing embeddings in batches
    to improve efficiency and throughput.
    """

    def __init__(self, embedding_registry: EmbeddingRegistry, batch_size: int = 32):
        """Initialize the EmbeddingBatcher.

        Args:
            embedding_registry: The EmbeddingRegistry instance to use.
            batch_size: The default batch size for embedding operations.
        """
        self._embedding_registry = embedding_registry
        self._batch_size = batch_size
        logger.info(f"EmbeddingBatcher initialized with batch size: {batch_size}")

    async def embed_batch(
        self,
        texts: List[str],
        model_name: str = "default",
        batch_size: Optional[int] = None,
        **kwargs: Any,
    ) -> BatchResult:
        """Generate embeddings for a batch of texts.

        Args:
            texts: The list of texts to embed.
            model_name: The name of the model to use.
            batch_size: The batch size for processing.
            **kwargs: Additional arguments for the embedding model.

        Returns:
            BatchResult containing the embeddings and metadata.
        """
        batch_size = batch_size or self._batch_size
        embeddings = []
        failed_indices = []

        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            try:
                batch_embeddings = await self._embedding_registry.embed_batch(
                    batch, model_name, **kwargs
                )
                embeddings.extend(batch_embeddings)
            except Exception as e:
                logger.error(f"Error embedding batch {i//batch_size}: {e}")
                failed_indices.extend(range(i, min(i + batch_size, len(texts))))

        logger.info(f"Embedded {len(embeddings)} texts with {len(failed_indices)} failures.")
        return BatchResult(
            embeddings=embeddings,
            failed_indices=failed_indices,
            metadata={"batch_size": batch_size, "model": model_name},
        )

    async def embed_batch_async(
        self,
        texts: List[str],
        model_name: str = "default",
        batch_size: Optional[int] = None,
        max_concurrency: int = 4,
        **kwargs: Any,
    ) -> BatchResult:
        """Generate embeddings for a batch of texts asynchronously.

        Args:
            texts: The list of texts to embed.
            model_name: The name of the model to use.
            batch_size: The batch size for processing.
            max_concurrency: Maximum number of concurrent batches.
            **kwargs: Additional arguments for the embedding model.

        Returns:
            BatchResult containing the embeddings and metadata.
        """
        batch_size = batch_size or self._batch_size
        embeddings = [None] * len(texts)
        failed_indices = []
        semaphore = asyncio.Semaphore(max_concurrency)

        async def process_batch(start_idx: int, end_idx: int) -> None:
            batch = texts[start_idx:end_idx]
            try:
                async with semaphore:
                    batch_embeddings = await self._embedding_registry.embed_batch(
                        batch, model_name, **kwargs
                    )
                    for i, embedding in enumerate(batch_embeddings):
                        embeddings[start_idx + i] = embedding
            except Exception as e:
                logger.error(f"Error embedding batch {start_idx//batch_size}: {e}")
                failed_indices.extend(range(start_idx, end_idx))

        tasks = []
        for i in range(0, len(texts), batch_size):
            end_idx = min(i + batch_size, len(texts))
            tasks.append(process_batch(i, end_idx))

        await asyncio.gather(*tasks)

        logger.info(f"Embedded {len(texts) - len(failed_indices)} texts asynchronously with {len(failed_indices)} failures.")
        return BatchResult(
            embeddings=[e for e in embeddings if e is not None],
            failed_indices=failed_indices,
            metadata={"batch_size": batch_size, "model": model_name, "concurrency": max_concurrency},
        )

    def set_batch_size(self, batch_size: int) -> None:
        """Set the default batch size.

        Args:
            batch_size: The new default batch size.
        """
        self._batch_size = batch_size
        logger.info(f"Set batch size to: {batch_size}")
