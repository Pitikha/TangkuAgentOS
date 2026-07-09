"""
Audio Model for TangkuAgentOS AI Foundation Framework.

This module defines the AudioModel interface for audio-based AI models.
"""

from typing import Any, Optional, Dict, List, AsyncIterator
from .base_model import AIModel, ModelCapabilities, ModelModality


class AudioModel(AIModel):
    """Abstract base class for audio-based AI models."""

    @property
    def capabilities(self) -> ModelCapabilities:
        """Default capabilities for an audio model."""
        return ModelCapabilities(
            modalities=[ModelModality.AUDIO, ModelModality.TEXT],
            max_context=25000,
            max_output=1000,
            streaming_support=True,
            vision_support=False,
            embedding_support=False,
            tool_calling_support=False,
            reasoning_support=False,
            json_mode=False,
            function_calling=False,
            pricing={"input": 0.006, "output": 0.012},
            latency_estimate=3.0,
            reliability_score=0.97,
        )

    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        **kwargs: Any,
    ) -> str:
        """Generate a text completion (not typically used for audio models)."""
        raise NotImplementedError("Audio models do not support text generation by default.")

    async def chat(
        self,
        messages: List[Dict[str, Any]],
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """Generate a chat completion with audio support."""
        raise NotImplementedError("Audio models must implement the chat method.")

    async def stream_chat(
        self,
        messages: List[Dict[str, Any]],
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        **kwargs: Any,
    ) -> AsyncIterator[Dict[str, Any]]:
        """Stream a chat completion with audio support."""
        raise NotImplementedError("Audio models must implement the stream_chat method.")

    async def embed(self, text: str, **kwargs: Any) -> List[float]:
        """Generate embeddings for the input text (not supported for audio models)."""
        raise NotImplementedError("Audio models do not support embeddings by default.")

    async def embed_batch(self, texts: List[str], **kwargs: Any) -> List[List[float]]:
        """Generate embeddings for a batch of texts (not supported for audio models)."""
        raise NotImplementedError("Audio models do not support batch embeddings by default.")
