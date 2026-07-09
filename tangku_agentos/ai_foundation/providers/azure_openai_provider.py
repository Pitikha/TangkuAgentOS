"""
Azure OpenAI Provider Implementation for TangkuAgentOS AI Foundation Framework.
"""

from typing import Any, Optional, Dict, List, Type, AsyncIterator
from ..models.base_model import AIModel, ModelCapabilities, ModelModality
from .base_provider import BaseProvider


class AzureOpenAIModel(AIModel):
    """Azure OpenAI implementation of the AIModel interface."""

    def __init__(
        self,
        model_name: str,
        api_key: str,
        base_url: Optional[str] = None,
        **kwargs: Any,
    ):
        self._model_name = model_name
        self._api_key = api_key
        self._base_url = base_url or "https://{resource-name}.openai.azure.com/openai/deployments/{deployment-id}"

    @property
    def name(self) -> str:
        return self._model_name

    @property
    def provider(self) -> str:
        return "azure_openai"

    @property
    def capabilities(self) -> ModelCapabilities:
        if "gpt-4" in self._model_name:
            return ModelCapabilities(
                modalities=[
                    ModelModality.TEXT,
                    ModelModality.CHAT,
                    ModelModality.VISION,
                    ModelModality.TOOL_CALLING,
                    ModelModality.STRUCTURED_OUTPUT,
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
                pricing={"input": 0.03, "output": 0.06},
                latency_estimate=5.0,
                reliability_score=0.99,
            )
        elif "gpt-3.5" in self._model_name:
            return ModelCapabilities(
                modalities=[
                    ModelModality.TEXT,
                    ModelModality.CHAT,
                    ModelModality.TOOL_CALLING,
                ],
                max_context=16384,
                max_output=4096,
                streaming_support=True,
                vision_support=False,
                embedding_support=False,
                tool_calling_support=True,
                reasoning_support=False,
                json_mode=True,
                function_calling=True,
                pricing={"input": 0.0015, "output": 0.002},
                latency_estimate=2.0,
                reliability_score=0.98,
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
        """Generate a text completion using Azure OpenAI."""
        return f"Generated text for prompt: {prompt}"

    async def chat(
        self,
        messages: List[Dict[str, Any]],
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """Generate a chat completion using Azure OpenAI."""
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
        """Stream a chat completion using Azure OpenAI."""
        yield {"choices": [{"message": {"role": "assistant", "content": "Streamed response part 1"}}]}
        yield {"choices": [{"message": {"role": "assistant", "content": "Streamed response part 2"}}]}

    async def embed(self, text: str, **kwargs: Any) -> List[float]:
        """Generate embeddings using Azure OpenAI."""
        return [0.1] * 1536  # Placeholder embedding vector

    async def embed_batch(self, texts: List[str], **kwargs: Any) -> List[List[float]]:
        """Generate embeddings for a batch of texts using Azure OpenAI."""
        return [[0.1] * 1536 for _ in texts]


class AzureOpenAIProvider(BaseProvider):
    """Azure OpenAI implementation of the BaseProvider interface."""

    def __init__(self, api_key: str, base_url: Optional[str] = None):
        self._api_key = api_key
        self._base_url = base_url

    @property
    def name(self) -> str:
        return "azure_openai"

    @property
    def api_key(self) -> Optional[str]:
        return self._api_key

    @property
    def base_url(self) -> Optional[str]:
        return self._base_url

    def get_model_class(self) -> Type[AIModel]:
        return AzureOpenAIModel

    async def initialize(self, **kwargs: Any) -> None:
        """Initialize the Azure OpenAI provider."""
        pass

    async def list_models(self) -> List[str]:
        """List all available Azure OpenAI models."""
        return ["gpt-4", "gpt-3.5-turbo", "text-embedding-ada-002"]

    async def get_model_capabilities(self, model_name: str) -> ModelCapabilities:
        """Get the capabilities of a specific Azure OpenAI model."""
        model = AzureOpenAIModel(model_name, self._api_key, self._base_url)
        return model.capabilities

    async def create_model(self, model_name: str, **kwargs: Any) -> AIModel:
        """Create an instance of an Azure OpenAI model."""
        return AzureOpenAIModel(model_name, self._api_key, self._base_url, **kwargs)

    async def health_check(self) -> bool:
        """Perform a health check for the Azure OpenAI provider."""
        return True
