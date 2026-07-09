"""
Chat Model for TangkuAgentOS AI Foundation Framework.

This module defines the ChatModel interface for chat-based AI models.
"""

from typing import Any, Optional, Dict, List, AsyncIterator
from .base_model import AIModel, ModelCapabilities, ModelModality


class ChatModel(AIModel):
    """Abstract base class for chat-based AI models."""

    @property
    def capabilities(self) -> ModelCapabilities:
        """Default capabilities for a chat model."""
        return ModelCapabilities(
            modalities=[ModelModality.CHAT, ModelModality.TEXT],
            max_context=4096,
            max_output=2048,
            streaming_support=True,
            vision_support=False,
            embedding_support=False,
            tool_calling_support=False,
            reasoning_support=False,
            json_mode=True,
            function_calling=False,
            pricing={"input": 0.001, "output": 0.002},
            latency_estimate=1.0,
            reliability_score=0.95,
        )

    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        **kwargs: Any,
    ) -> str:
        """Generate a text completion using chat."""
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        response = await self.chat(messages, max_tokens, temperature, **kwargs)
        return response.get("choices", [{}])[0].get("message", {}).get("content", "")

    async def chat(
        self,
        messages: List[Dict[str, Any]],
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """Generate a chat completion."""
        raise NotImplementedError("Chat models must implement the chat method.")

    async def stream_chat(
        self,
        messages: List[Dict[str, Any]],
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        **kwargs: Any,
    ) -> AsyncIterator[Dict[str, Any]]:
        """Stream a chat completion."""
        raise NotImplementedError("Chat models must implement the stream_chat method.")

    async def embed(self, text: str, **kwargs: Any) -> List[float]:
        """Generate embeddings for the input text."""
        raise NotImplementedError("Chat models do not support embeddings by default.")

    async def embed_batch(self, texts: List[str], **kwargs: Any) -> List[List[float]]:
        """Generate embeddings for a batch of texts."""
        raise NotImplementedError("Chat models do not support batch embeddings by default.")
