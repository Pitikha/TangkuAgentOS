"""
Custom Provider Implementation for TangkuAgentOS AI Foundation Framework.

This module allows for custom AI providers to be dynamically registered.
"""

from typing import Any, Optional, Dict, List, Type, AsyncIterator
from ..models.base_model import AIModel, ModelCapabilities, ModelModality
from .base_provider import BaseProvider


class CustomModel(AIModel):
    """Custom implementation of the AIModel interface."""

    def __init__(
        self,
        model_name: str,
        api_key: str,
        base_url: Optional[str] = None,
        capabilities: Optional[ModelCapabilities] = None,
        **kwargs: Any,
    ):
        self._model_name = model_name
        self._api_key = api_key
        self._base_url = base_url
        self._capabilities = capabilities or ModelCapabilities(
            modalities=[ModelModality.TEXT],
            max_context=4096,
            max_output=2048,
            streaming_support=True,
            vision_support=False,
            embedding_support=False,
            tool_calling_support=False,
            reasoning_support=False,
            json_mode=False,
            function_calling=False,
            pricing={"input": 0.001, "output": 0.002},
            latency_estimate=1.0,
            reliability_score=0.9,
        )

    @property
    def name(self) -> str:
        return self._model_name

    @property
    def provider(self) -> str:
        return "custom"

    @property
    def capabilities(self) -> ModelCapabilities:
        return self._capabilities

    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        **kwargs: Any,
    ) -> str:
        """Generate a text completion using a custom model."""
        return f"Generated text for prompt: {prompt}"

    async def chat(
        self,
        messages: List[Dict[str, Any]],
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """Generate a chat completion using a custom model."""
        return {
            "choices": [
                {
                    "message": {
                        "role": "assistant",
                        "content": f"Response to: {messages[-1].get('content', '')}",
                    }
                }
            ]
        }

    async def stream_chat(
        self,
        messages: List[Dict[str, Any]],
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        **kwargs: Any,
    ) -> AsyncIterator[Dict[str, Any]]:
        """Stream a chat completion using a custom model."""
        yield {"choices": [{"message": {"role": "assistant", "content": "Streamed response part 1"}}]}
        yield {"choices": [{"message": {"role": "assistant", "content": "Streamed response part 2"}}]}

    async def embed(self, text: str, **kwargs: Any) -> List[float]:
        """Generate embeddings using a custom model."""
        return [0.1] * 512  # Placeholder embedding vector

    async def embed_batch(self, texts: List[str], **kwargs: Any) -> List[List[float]]:
        """Generate embeddings for a batch of texts using a custom model."""
        return [[0.1] * 512 for _ in texts]


class CustomProvider(BaseProvider):
    """Custom implementation of the BaseProvider interface."""

    def __init__(
        self,
        name: str,
        api_key: str,
        base_url: Optional[str] = None,
        model_class: Optional[Type[AIModel]] = None,
        **kwargs: Any,
    ):
        self._name = name
        self._api_key = api_key
        self._base_url = base_url
        self._model_class = model_class or CustomModel

    @property
    def name(self) -> str:
        return self._name

    @property
    def api_key(self) -> Optional[str]:
        return self._api_key

    @property
    def base_url(self) -> Optional[str]:
        return self._base_url

    def get_model_class(self) -> Type[AIModel]:
        return self._model_class

    async def initialize(self, **kwargs: Any) -> None:
        """Initialize the custom provider."""
        pass

    async def list_models(self) -> List[str]:
        """List all available models for this custom provider."""
        return ["custom-model-1", "custom-model-2"]

    async def get_model_capabilities(self, model_name: str) -> ModelCapabilities:
        """Get the capabilities of a specific custom model."""
        model = self._model_class(model_name, self._api_key, self._base_url)
        return model.capabilities

    async def create_model(self, model_name: str, **kwargs: Any) -> AIModel:
        """Create an instance of a custom model."""
        return self._model_class(model_name, self._api_key, self._base_url, **kwargs)

    async def health_check(self) -> bool:
        """Perform a health check for the custom provider."""
        return True
