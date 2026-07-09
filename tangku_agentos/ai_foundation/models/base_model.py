"""
Base AI Model Interface for TangkuAgentOS AI Foundation Framework.

This module defines the universal AIModel interface that all providers must implement.
"""

from abc import ABC, abstractmethod
from typing import Any, Optional, Dict, List, AsyncIterator
from dataclasses import dataclass
from enum import Enum


class ModelModality(Enum):
    """Supported AI model modalities."""
    TEXT = "text"
    CHAT = "chat"
    EMBEDDING = "embedding"
    VISION = "vision"
    AUDIO = "audio"
    IMAGE = "image"
    TOOL_CALLING = "tool_calling"
    STRUCTURED_OUTPUT = "structured_output"
    REASONING = "reasoning"


@dataclass
class ModelCapabilities:
    """Capabilities of an AI model."""
    modalities: List[ModelModality]
    max_context: int
    max_output: int
    streaming_support: bool
    vision_support: bool
    embedding_support: bool
    tool_calling_support: bool
    reasoning_support: bool
    json_mode: bool
    function_calling: bool
    pricing: Dict[str, float]  # e.g., {"input": 0.001, "output": 0.002}
    latency_estimate: float  # Estimated latency in seconds
    reliability_score: float  # 0.0 to 1.0


class AIModel(ABC):
    """Abstract base class for all AI models in TangkuAgentOS."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Unique name of the model."""
        pass

    @property
    @abstractmethod
    def provider(self) -> str:
        """Name of the provider (e.g., 'openai', 'anthropic')."""
        pass

    @property
    @abstractmethod
    def capabilities(self) -> ModelCapabilities:
        """Capabilities of the model."""
        pass

    @abstractmethod
    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        **kwargs: Any,
    ) -> str:
        """Generate a text completion."""
        pass

    @abstractmethod
    async def chat(
        self,
        messages: List[Dict[str, Any]],
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """Generate a chat completion."""
        pass

    @abstractmethod
    async def stream_chat(
        self,
        messages: List[Dict[str, Any]],
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        **kwargs: Any,
    ) -> AsyncIterator[Dict[str, Any]]:
        """Stream a chat completion."""
        pass

    @abstractmethod
    async def embed(
        self,
        text: str,
        **kwargs: Any,
    ) -> List[float]:
        """Generate embeddings for the input text."""
        pass

    @abstractmethod
    async def embed_batch(
        self,
        texts: List[str],
        **kwargs: Any,
    ) -> List[List[float]]:
        """Generate embeddings for a batch of texts."""
        pass
