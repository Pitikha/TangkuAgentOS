"""
Vision Model for TangkuAgentOS AI Foundation Framework.

This module defines the VisionModel interface for vision-based AI models.
"""

from typing import Any, Optional, Dict, List, AsyncIterator
from .base_model import AIModel, ModelCapabilities, ModelModality


class VisionModel(AIModel):
    """Abstract base class for vision-based AI models."""

    @property
    def capabilities(self) -> ModelCapabilities:
        """Default capabilities for a vision model."""
        return ModelCapabilities(
            modalities=[ModelModality.VISION, ModelModality.TEXT, ModelModality.CHAT],
            max_context=128000,
            max_output=4096,
            streaming_support=True,
            vision_support=True,
            embedding_support=False,
            tool_calling_support=True,
            reasoning_support=True,
            json_mode=True,
            function_calling=True,
            pricing={"input": 0.03, "output": 0.06},
            latency_estimate=5.0,
            reliability_score=0.98,
        )

    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        **kwargs: Any,
    ) -> str:
        """Generate a text completion (not typically used for vision models)."""
        raise NotImplementedError("Vision models do not support text generation by default.")

    async def chat(
        self,
        messages: List[Dict[str, Any]],
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """Generate a chat completion with vision support."""
        raise NotImplementedError("Vision models must implement the chat method.")

    async def stream_chat(
        self,
        messages: List[Dict[str, Any]],
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        **kwargs: Any,
    ) -> AsyncIterator[Dict[str, Any]]:
        """Stream a chat completion with vision support."""
        raise NotImplementedError("Vision models must implement the stream_chat method.")

    async def embed(self, text: str, **kwargs: Any) -> List[float]:
        """Generate embeddings for the input text (not supported for vision models)."""
        raise NotImplementedError("Vision models do not support embeddings by default.")

    async def embed_batch(self, texts: List[str], **kwargs: Any) -> List[List[float]]:
        """Generate embeddings for a batch of texts (not supported for vision models)."""
        raise NotImplementedError("Vision models do not support batch embeddings by default.")
