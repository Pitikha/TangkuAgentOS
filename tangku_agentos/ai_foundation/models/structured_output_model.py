"""
Structured Output Model for TangkuAgentOS AI Foundation Framework.

This module defines the StructuredOutputModel interface for AI models that support structured outputs.
"""

from typing import Any, Optional, Dict, List, AsyncIterator
from .base_model import AIModel, ModelCapabilities, ModelModality


class StructuredOutputModel(AIModel):
    """Abstract base class for structured output AI models."""

    @property
    def capabilities(self) -> ModelCapabilities:
        """Default capabilities for a structured output model."""
        return ModelCapabilities(
            modalities=[ModelModality.TEXT, ModelModality.CHAT, ModelModality.STRUCTURED_OUTPUT],
            max_context=8192,
            max_output=2048,
            streaming_support=True,
            vision_support=False,
            embedding_support=False,
            tool_calling_support=True,
            reasoning_support=True,
            json_mode=True,
            function_calling=True,
            pricing={"input": 0.002, "output": 0.004},
            latency_estimate=2.0,
            reliability_score=0.96,
        )

    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        **kwargs: Any,
    ) -> str:
        """Generate a text completion with structured output support."""
        raise NotImplementedError("Structured output models must implement the generate method.")

    async def chat(
        self,
        messages: List[Dict[str, Any]],
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """Generate a chat completion with structured output support."""
        raise NotImplementedError("Structured output models must implement the chat method.")

    async def stream_chat(
        self,
        messages: List[Dict[str, Any]],
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        **kwargs: Any,
    ) -> AsyncIterator[Dict[str, Any]]:
        """Stream a chat completion with structured output support."""
        raise NotImplementedError("Structured output models must implement the stream_chat method.")

    async def embed(self, text: str, **kwargs: Any) -> List[float]:
        """Generate embeddings for the input text (not supported for structured output models)."""
        raise NotImplementedError("Structured output models do not support embeddings by default.")

    async def embed_batch(self, texts: List[str], **kwargs: Any) -> List[List[float]]:
        """Generate embeddings for a batch of texts (not supported for structured output models)."""
        raise NotImplementedError("Structured output models do not support batch embeddings by default.")
