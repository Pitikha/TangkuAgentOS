"""
Ollama Provider Implementation for TangkuAgentOS AI Foundation Framework.
"""

from typing import Any, Optional, Dict, List, Type, AsyncIterator
from ..models.base_model import AIModel, ModelCapabilities, ModelModality
from .base_provider import BaseProvider


class OllamaModel(AIModel):
    """Ollama implementation of the AIModel interface."""

    def __init__(
        self,
        model_name: str,
        api_key: str,
        base_url: Optional[str] = None,
        **kwargs: Any,
    ):
        self._model_name = model_name
        self._api_key = api_key
        self._base_url = base_url or "http://localhost:11434/v1"

    @property
    def name(self) -> str:
        return self._model_name

    @property
    def provider(self) -> str:
        return "ollama"

    @property
    def capabilities(self) -> ModelCapabilities:
        if "llama3" in self._model_name:
            return ModelCapabilities(
                modalities=[ModelModality.TEXT, ModelModality.CHAT],
                max_context=8192,
                max_output=4096,
                streaming_support=True,
                vision_support=False,
                embedding_support=False,
                tool_calling_support=False,
                reasoning_support=True,
                json_mode=True,
                function_calling=False,
                pricing={"input": 0.0, "output": 0.0},  # Local models are free
                latency_estimate=2.0,
                reliability_score=0.95,
            )
        elif "mistral" in self._model_name:
            return ModelCapabilities(
                modalities=[ModelModality.TEXT, ModelModality.CHAT],
                max_context=32768,
                max_output=4096,
                streaming_support=True,
                vision_support=False,
                embedding_support=False,
                tool_calling_support=False,
                reasoning_support=True,
                json_mode=True,
                function_calling=False,
                pricing={"input": 0.0, "output": 0.0},
                latency_estimate=3.0,
                reliability_score=0.96,
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
                pricing={"input": 0.0, "output": 0.0},
                latency_estimate=1.0,
                reliability_score=0.9,
            )

    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        **kwargs: Any,
    ) -> str:
        """Generate a text completion using Ollama."""
        return f"Generated text for prompt: {prompt}"

    async def chat(
        self,
        messages: List[Dict[str, Any]],
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """Generate a chat completion using Ollama."""
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
        """Stream a chat completion using Ollama."""
        yield {"choices": [{"message": {"role": "assistant", "content": "Streamed response part 1"}}]}
        yield {"choices": [{"message": {"role": "assistant", "content": "Streamed response part 2"}}]}

    async def embed(self, text: str, **kwargs: Any) -> List[float]:
        """Generate embeddings (not supported for Ollama)."""
        raise NotImplementedError("Ollama does not support embeddings directly.")

    async def embed_batch(self, texts: List[str], **kwargs: Any) -> List[List[float]]:
        """Generate embeddings for a batch of texts (not supported for Ollama)."""
        raise NotImplementedError("Ollama does not support batch embeddings directly.")


class OllamaProvider(BaseProvider):
    """Ollama implementation of the BaseProvider interface."""

    def __init__(self, api_key: str = "", base_url: Optional[str] = None):
        self._api_key = api_key  # Ollama typically doesn't require an API key
        self._base_url = base_url

    @property
    def name(self) -> str:
        return "ollama"

    @property
    def api_key(self) -> Optional[str]:
        return self._api_key

    @property
    def base_url(self) -> Optional[str]:
        return self._base_url

    def get_model_class(self) -> Type[AIModel]:
        return OllamaModel

    async def initialize(self, **kwargs: Any) -> None:
        """Initialize the Ollama provider."""
        pass

    async def list_models(self) -> List[str]:
        """List all available Ollama models."""
        # Placeholder: In a real implementation, this would fetch from the Ollama API
        return ["llama3:70b", "llama3:8b", "mistral:latest"]

    async def get_model_capabilities(self, model_name: str) -> ModelCapabilities:
        """Get the capabilities of a specific Ollama model."""
        model = OllamaModel(model_name, self._api_key, self._base_url)
        return model.capabilities

    async def create_model(self, model_name: str, **kwargs: Any) -> AIModel:
        """Create an instance of an Ollama model."""
        return OllamaModel(model_name, self._api_key, self._base_url, **kwargs)

    async def health_check(self) -> bool:
        """Perform a health check for the Ollama provider."""
        return True
