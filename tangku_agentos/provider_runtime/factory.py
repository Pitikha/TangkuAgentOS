from __future__ import annotations

from .interfaces import ProviderAdapter, ProviderFactory
from ..model_runtime.models import ModelConfiguration
from .providers import (
    AnthropicProvider,
    CustomProvider,
    DeepSeekProvider,
    GoogleProvider,
    GroqProvider,
    LocalModelProvider,
    LMStudioProvider,
    OllamaProvider,
    OpenAIProvider,
    OpenRouterProvider,
)


class ProviderFactory(ProviderFactory):
    """Factory for provider adapters."""

    def create(self, provider_id: str, configuration: ModelConfiguration) -> ProviderAdapter:
        provider_map = {
            "openrouter": OpenRouterProvider,
            "openai": OpenAIProvider,
            "anthropic": AnthropicProvider,
            "google": GoogleProvider,
            "groq": GroqProvider,
            "deepseek": DeepSeekProvider,
            "ollama": OllamaProvider,
            "lmstudio": LMStudioProvider,
            "local": LocalModelProvider,
            "azure_openai": OpenAIProvider,
            "azure-openai": OpenAIProvider,
            "mistral": CustomProvider,
            "cohere": CustomProvider,
            "together": CustomProvider,
            "together_ai": CustomProvider,
            "fireworks": CustomProvider,
            "fireworks_ai": CustomProvider,
        }
        provider_cls = provider_map.get(provider_id.lower(), CustomProvider)
        return provider_cls(provider_id, configuration.settings)
