"""
Providers for the AI Foundation Framework.
"""

from .base_provider import BaseProvider
from .openai_provider import OpenAIProvider, OpenAIModel
from .anthropic_provider import AnthropicProvider, AnthropicModel
from .gemini_provider import GeminiProvider, GeminiModel
from .groq_provider import GroqProvider, GroqModel
from .mistral_provider import MistralProvider, MistralModel
from .openrouter_provider import OpenRouterProvider, OpenRouterModel
from .ollama_provider import OllamaProvider, OllamaModel
from .togetherai_provider import TogetherAIProvider, TogetherAIModel
from .cohere_provider import CohereProvider, CohereModel
from .azure_openai_provider import AzureOpenAIProvider, AzureOpenAIModel
from .vertex_ai_provider import VertexAIProvider, VertexAIModel
from .aws_bedrock_provider import AWSBedrockProvider, AWSBedrockModel
from .huggingface_provider import HuggingFaceProvider, HuggingFaceModel
from .custom_provider import CustomProvider, CustomModel

__all__ = [
    # Base
    "BaseProvider",
    # OpenAI
    "OpenAIProvider",
    "OpenAIModel",
    # Anthropic
    "AnthropicProvider",
    "AnthropicModel",
    # Gemini
    "GeminiProvider",
    "GeminiModel",
    # Groq
    "GroqProvider",
    "GroqModel",
    # Mistral
    "MistralProvider",
    "MistralModel",
    # OpenRouter
    "OpenRouterProvider",
    "OpenRouterModel",
    # Ollama
    "OllamaProvider",
    "OllamaModel",
    # TogetherAI
    "TogetherAIProvider",
    "TogetherAIModel",
    # Cohere
    "CohereProvider",
    "CohereModel",
    # Azure OpenAI
    "AzureOpenAIProvider",
    "AzureOpenAIModel",
    # Vertex AI
    "VertexAIProvider",
    "VertexAIModel",
    # AWS Bedrock
    "AWSBedrockProvider",
    "AWSBedrockModel",
    # Hugging Face
    "HuggingFaceProvider",
    "HuggingFaceModel",
    # Custom
    "CustomProvider",
    "CustomModel",
]
