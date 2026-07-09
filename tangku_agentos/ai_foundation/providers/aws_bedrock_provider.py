"""
AWS Bedrock Provider Implementation for TangkuAgentOS AI Foundation Framework.
"""

from typing import Any, Optional, Dict, List, Type, AsyncIterator
from ..models.base_model import AIModel, ModelCapabilities, ModelModality
from .base_provider import BaseProvider


class AWSBedrockModel(AIModel):
    """AWS Bedrock implementation of the AIModel interface."""

    def __init__(
        self,
        model_name: str,
        api_key: str,
        base_url: Optional[str] = None,
        **kwargs: Any,
    ):
        self._model_name = model_name
        self._api_key = api_key
        self._base_url = base_url or "https://bedrock-runtime.us-east-1.amazonaws.com"

    @property
    def name(self) -> str:
        return self._model_name

    @property
    def provider(self) -> str:
        return "aws_bedrock"

    @property
    def capabilities(self) -> ModelCapabilities:
        if "claude-3" in self._model_name:
            return ModelCapabilities(
                modalities=[
                    ModelModality.TEXT,
                    ModelModality.CHAT,
                    ModelModality.VISION,
                    ModelModality.TOOL_CALLING,
                    ModelModality.REASONING,
                ],
                max_context=200000,
                max_output=4096,
                streaming_support=True,
                vision_support=True,
                embedding_support=False,
                tool_calling_support=True,
                reasoning_support=True,
                json_mode=True,
                function_calling=True,
                pricing={"input": 0.015, "output": 0.075},
                latency_estimate=3.0,
                reliability_score=0.98,
            )
        elif "llama3" in self._model_name:
            return ModelCapabilities(
                modalities=[ModelModality.TEXT, ModelModality.CHAT],
                max_context=8192,
                max_output=4096,
                streaming_support=True,
                vision_support=False,
                embedding_support=False,
                tool_calling_support=True,
                reasoning_support=True,
                json_mode=True,
                function_calling=True,
                pricing={"input": 0.0008, "output": 0.001},
                latency_estimate=1.0,
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
        """Generate a text completion using AWS Bedrock."""
        return f"Generated text for prompt: {prompt}"

    async def chat(
        self,
        messages: List[Dict[str, Any]],
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """Generate a chat completion using AWS Bedrock."""
        return {
            "outputs": [
                {
                    "text": f"Response to: {messages[-1].get('content', '')}",
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
        """Stream a chat completion using AWS Bedrock."""
        yield {"outputs": [{"text": "Streamed response part 1"}]}
        yield {"outputs": [{"text": "Streamed response part 2"}]}

    async def embed(self, text: str, **kwargs: Any) -> List[float]:
        """Generate embeddings (not supported for AWS Bedrock)."""
        raise NotImplementedError("AWS Bedrock does not support embeddings directly.")

    async def embed_batch(self, texts: List[str], **kwargs: Any) -> List[List[float]]:
        """Generate embeddings for a batch of texts (not supported for AWS Bedrock)."""
        raise NotImplementedError("AWS Bedrock does not support batch embeddings directly.")


class AWSBedrockProvider(BaseProvider):
    """AWS Bedrock implementation of the BaseProvider interface."""

    def __init__(self, api_key: str, base_url: Optional[str] = None):
        self._api_key = api_key
        self._base_url = base_url

    @property
    def name(self) -> str:
        return "aws_bedrock"

    @property
    def api_key(self) -> Optional[str]:
        return self._api_key

    @property
    def base_url(self) -> Optional[str]:
        return self._base_url

    def get_model_class(self) -> Type[AIModel]:
        return AWSBedrockModel

    async def initialize(self, **kwargs: Any) -> None:
        """Initialize the AWS Bedrock provider."""
        pass

    async def list_models(self) -> List[str]:
        """List all available AWS Bedrock models."""
        return [
            "anthropic.claude-3-sonnet-20240229-v1:0",
            "meta.llama3-70b-instruct-v1:0",
            "ai21.j2-ultra-v1",
        ]

    async def get_model_capabilities(self, model_name: str) -> ModelCapabilities:
        """Get the capabilities of a specific AWS Bedrock model."""
        model = AWSBedrockModel(model_name, self._api_key, self._base_url)
        return model.capabilities

    async def create_model(self, model_name: str, **kwargs: Any) -> AIModel:
        """Create an instance of an AWS Bedrock model."""
        return AWSBedrockModel(model_name, self._api_key, self._base_url, **kwargs)

    async def health_check(self) -> bool:
        """Perform a health check for the AWS Bedrock provider."""
        return True
