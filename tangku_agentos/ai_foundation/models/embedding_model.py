"""
Embedding Model for TangkuAgentOS AI Foundation Framework.

This module defines the EmbeddingModel interface for embedding-based AI models.
"""

from typing import Any, Optional, Dict, List, AsyncIterator
from .base_model import AIModel, ModelCapabilities, ModelModality


class EmbeddingModel(AIModel):
    """Abstract base class for embedding-based AI models."""

    @property
    def capabilities(self) -> ModelCapabilities:
        """Default capabilities for an embedding model."""
        return ModelCapabilities(
            modalities=[ModelModality.EMBEDDING],
            max_context=8192,
            max_output=0,
            streaming_support=False,
            vision_support=False,
            embedding_support=True,
            tool_calling_support=False,
            reasoning_support=False,
            json_mode=False,
            function_calling=False,
            pricing={"input": 0.0001},
            latency_estimate=0.5,
            reliability_score=0.99,
        )

    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        **kwargs: Any,
    ) -> str:
        """Generate a text completion (not supported for embedding models)."""
        raise NotImplementedError("Embedding models do not support text generation.")

    async def chat(
        self,
        messages: List[Dict[str, Any]],
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """Generate a chat completion (not supported for embedding models)."""
        raise NotImplementedError("Embedding models do not support chat.")

    async def stream_chat(
        self,
        messages: List[Dict[str, Any]],
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        **kwargs: Any,
    ) -> AsyncIterator[Dict[str, Any]]:
        """Stream a chat completion (not supported for embedding models)."""
        raise NotImplementedError("Embedding models do not support streaming chat.")

    async def embed(self, text: str, **kwargs: Any) -> List[float]:
        """Generate embeddings for the input text."""
        raise NotImplementedError("Embedding models must implement the embed method.")

    async def embed_batch(self, texts: List[str], **kwargs: Any) -> List[List[float]]:
        """Generate embeddings for a batch of texts."""
        raise NotImplementedError("Embedding models must implement the embed_batch method.")
