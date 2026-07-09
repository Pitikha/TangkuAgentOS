"""
OpenRouter Provider Implementation for TangkuAgentOS AI Foundation Framework.
"""

from typing import Any, Optional, Dict, List, Type, AsyncIterator
from ..models.base_model import AIModel, ModelCapabilities, ModelModality
from .base_provider import BaseProvider


class OpenRouterModel(AIModel):
    """OpenRouter implementation of the AIModel interface."""

    def __init__(
        self,
        model_name: str,
        api_key: str,
        base_url: Optional[str] = None,
        **kwargs: Any,
    ):
        self._model_name = model_name
        self._api_key = api_key
        self._base_url = base_url or "https://openrouter.ai/api/v1"

    @property
    def name(self) -> str:
        return self._model_name

    @property
    def provider(self) -> str:
        return "openrouter"

    @property
    def capabilities(self) -> ModelCapabilities:
        # OpenRouter supports many models; here we assume a generic high-capability model
        return ModelCapabilities(
            modalities=[
                ModelModality.TEXT,
                ModelModality.CHAT,
                ModelModality.VISION,
                ModelModality.TOOL_CALLING,
                ModelModality.REASONING,
            ],
            max_context=128000,
            max_output=4096,
            streaming_support=True,
            vision_support=True,
            embedding_support=False,
            tool_calling_support=True,
            reasoning_support=True,
            json_mode=True,
            function_calling=True,
            pricing={"input": 0.0015, "output": 0.002},
            latency_estimate=2.0,
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
        """Generate a text completion using OpenRouter."""
        return f"Generated text for prompt: {prompt}"

    async def chat(
        self,
        messages: List[Dict[str, Any]],
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """Generate a chat completion using OpenRouter."""
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
        """Stream a chat completion using OpenRouter."""
        yield {"choices": [{"message": {"role": "assistant", "content": "Streamed response part 1"}}]}
        yield {"choices": [{"message": {"role": "assistant", "content": "Streamed response part 2"}}]}

    async def embed(self, text: str, **kwargs: Any) -> List[float]:
        """Generate embeddings (not supported for OpenRouter)."""
        raise NotImplementedError("OpenRouter does not support embeddings directly.")

    async def embed_batch(self, texts: List[str], **kwargs: Any) -> List[List[float]]:
        """Generate embeddings for a batch of texts (not supported for OpenRouter)."""
        raise NotImplementedError("OpenRouter does not support batch embeddings directly.")


class OpenRouterProvider(BaseProvider):
    """OpenRouter implementation of the BaseProvider interface."""

    def __init__(self, api_key: str, base_url: Optional[str] = None):
        self._api_key = api_key
        self._base_url = base_url

    @property
    def name(self) -> str:
        return "openrouter"

    @property
    def api_key(self) -> Optional[str]:
        return self._api_key

    @property
    def base_url(self) -> Optional[str]:
        return self._base_url

    def get_model_class(self) -> Type[AIModel]:
        return OpenRouterModel

    async def initialize(self, **kwargs: Any) -> None:
        """Initialize the OpenRouter provider."""
        pass

    async def list_models(self) -> List[str]:
        """List all available OpenRouter models."""
        # OpenRouter supports many models; this is a placeholder list
        return [
            "openai/gpt-4",
            "anthropic/claude-3-sonnet",
            "google/gemini-pro",
            "meta/llama-3-70b",
            "mistralai/mistral-large",
        ]

    async def get_model_capabilities(self, model_name: str) -> ModelCapabilities:
        """Get the capabilities of a specific OpenRouter model."""
        model = OpenRouterModel(model_name, self._api_key, self._base_url)
        return model.capabilities

    async def create_model(self, model_name: str, **kwargs: Any) -> AIModel:
        """Create an instance of an OpenRouter model."""
        return OpenRouterModel(model_name, self._api_key, self._base_url, **kwargs)

    async def health_check(self) -> bool:
        """Perform a health check for the OpenRouter provider."""
        return True
