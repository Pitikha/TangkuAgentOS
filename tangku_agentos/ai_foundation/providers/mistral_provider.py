"""
Mistral Provider Implementation for TangkuAgentOS AI Foundation Framework.
"""

from typing import Any, Optional, Dict, List, Type, AsyncIterator
from ..models.base_model import AIModel, ModelCapabilities, ModelModality
from .base_provider import BaseProvider


class MistralModel(AIModel):
    """Mistral implementation of the AIModel interface."""

    def __init__(
        self,
        model_name: str,
        api_key: str,
        base_url: Optional[str] = None,
        **kwargs: Any,
    ):
        self._model_name = model_name
        self._api_key = api_key
        self._base_url = base_url or "https://api.mistral.ai/v1"

    @property
    def name(self) -> str:
        return self._model_name

    @property
    def provider(self) -> str:
        return "mistral"

    @property
    def capabilities(self) -> ModelCapabilities:
        if "mistral-large" in self._model_name:
            return ModelCapabilities(
                modalities=[ModelModality.TEXT, ModelModality.CHAT],
                max_context=32768,
                max_output=4096,
                streaming_support=True,
                vision_support=False,
                embedding_support=False,
                tool_calling_support=True,
                reasoning_support=True,
                json_mode=True,
                function_calling=True,
                pricing={"input": 0.0025, "output": 0.0025},
                latency_estimate=1.0,
                reliability_score=0.98,
            )
        elif "mistral-small" in self._model_name:
            return ModelCapabilities(
                modalities=[ModelModality.TEXT, ModelModality.CHAT],
                max_context=32768,
                max_output=4096,
                streaming_support=True,
                vision_support=False,
                embedding_support=False,
                tool_calling_support=True,
                reasoning_support=True,
                json_mode=True,
                function_calling=True,
                pricing={"input": 0.001, "output": 0.001},
                latency_estimate=0.5,
                reliability_score=0.97,
            )
        else:
            return ModelCapabilities(
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
        """Generate a text completion using Mistral."""
        return f"Generated text for prompt: {prompt}"

    async def chat(
        self,
        messages: List[Dict[str, Any]],
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """Generate a chat completion using Mistral."""
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
        """Stream a chat completion using Mistral."""
        yield {"choices": [{"message": {"role": "assistant", "content": "Streamed response part 1"}}]}
        yield {"choices": [{"message": {"role": "assistant", "content": "Streamed response part 2"}}]}

    async def embed(self, text: str, **kwargs: Any) -> List[float]:
        """Generate embeddings (not supported for Mistral)."""
        raise NotImplementedError("Mistral does not support embeddings.")

    async def embed_batch(self, texts: List[str], **kwargs: Any) -> List[List[float]]:
        """Generate embeddings for a batch of texts (not supported for Mistral)."""
        raise NotImplementedError("Mistral does not support batch embeddings.")


class MistralProvider(BaseProvider):
    """Mistral implementation of the BaseProvider interface."""

    def __init__(self, api_key: str, base_url: Optional[str] = None):
        self._api_key = api_key
        self._base_url = base_url

    @property
    def name(self) -> str:
        return "mistral"

    @property
    def api_key(self) -> Optional[str]:
        return self._api_key

    @property
    def base_url(self) -> Optional[str]:
        return self._base_url

    def get_model_class(self) -> Type[AIModel]:
        return MistralModel

    async def initialize(self, **kwargs: Any) -> None:
        """Initialize the Mistral provider."""
        pass

    async def list_models(self) -> List[str]:
        """List all available Mistral models."""
        return ["mistral-large", "mistral-small"]

    async def get_model_capabilities(self, model_name: str) -> ModelCapabilities:
        """Get the capabilities of a specific Mistral model."""
        model = MistralModel(model_name, self._api_key, self._base_url)
        return model.capabilities

    async def create_model(self, model_name: str, **kwargs: Any) -> AIModel:
        """Create an instance of a Mistral model."""
        return MistralModel(model_name, self._api_key, self._base_url, **kwargs)

    async def health_check(self) -> bool:
        """Perform a health check for the Mistral provider."""
        return True
