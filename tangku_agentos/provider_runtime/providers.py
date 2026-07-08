"""Provider implementations for the TangkuAgentOS Provider Runtime."""

from __future__ import annotations

import json
from typing import Any, Dict, List, Optional, Tuple, TYPE_CHECKING

if TYPE_CHECKING:
    from .types import ProviderCapability, ProviderID, ProviderRequest, ProviderResponse, ProviderSettings

from .constants import ProviderCapability, ProviderID
from .integration import HTTPProviderAdapter
from .interfaces import ProviderAdapter


def _build_messages(input_value: Any) -> List[Dict[str, Any]]:
    """Build messages for chat-based providers."""
    if isinstance(input_value, list):
        return input_value
    return [{"role": "user", "content": str(input_value)}]


def _build_text(input_value: Any) -> str:
    """Build text for text-based providers."""
    if isinstance(input_value, list):
        pieces: List[str] = []
        for item in input_value:
            if isinstance(item, dict):
                pieces.append(str(item.get("content", "")))
            else:
                pieces.append(str(item))
        return "\n".join(filter(None, pieces))
    return str(input_value)


def _build_anthropic_prompt(input_value: Any) -> str:
    """Build prompt for Anthropic providers."""
    if isinstance(input_value, list):
        sections: List[str] = []
        for item in input_value:
            if not isinstance(item, dict):
                continue
            role = str(item.get("role", "user")).lower()
            content = str(item.get("content", ""))
            if role in {"assistant", "ai", "bot", "system"}:
                sections.append(f"\n\nAssistant: {content}")
            else:
                sections.append(f"\n\nHuman: {content}")
        return "".join(sections).strip() + "\n\nAssistant: "
    return str(input_value)


class BaseProvider(HTTPProviderAdapter):
    """Base class for all HTTP-based providers."""

    def __init__(
        self,
        provider_id: ProviderID,
        settings: Optional[ProviderSettings] = None,
        base_url: str = "",
        headers: Optional[Dict[str, str]] = None,
        timeout_seconds: float = 30.0,
        max_retries: int = 3,
    ) -> None:
        settings = settings or {}
        headers = headers or {}
        if "api_key" in settings:
            headers["Authorization"] = f"Bearer {settings['api_key']}"
        headers.update(settings.get("headers", {}))
        super().__init__(
            provider_id=provider_id,
            configuration=settings,
            base_url=base_url or settings.get("base_url", ""),
            headers=headers,
            timeout_seconds=timeout_seconds,
            max_retries=max_retries,
        )

    @property
    def capabilities(self) -> Dict[ProviderCapability, bool]:
        """Get the provider's capabilities."""
        return {
            ProviderCapability.CHAT: True,
            ProviderCapability.STREAMING: True,
        }

    def supports(self, capability: ProviderCapability) -> bool:
        """Check if the provider supports a capability."""
        return self.capabilities.get(capability, False)


class OpenAIProvider(BaseProvider):
    """OpenAI provider implementation."""

    def __init__(
        self,
        provider_id: ProviderID = ProviderID.OPENAI.value,
        settings: Optional[ProviderSettings] = None,
    ) -> None:
        headers = {}
        if settings and "api_key" in settings:
            headers["Authorization"] = f"Bearer {settings['api_key']}"
        if settings and "organization" in settings:
            headers["OpenAI-Organization"] = str(settings["organization"])
        super().__init__(
            provider_id=provider_id,
            settings=settings,
            base_url=settings.get("base_url", "https://api.openai.com/v1") if settings else "https://api.openai.com/v1",
            headers=headers,
        )

    @property
    def capabilities(self) -> Dict[ProviderCapability, bool]:
        return {
            ProviderCapability.CHAT: True,
            ProviderCapability.STREAMING: True,
            ProviderCapability.FUNCTION_CALLING: True,
            ProviderCapability.EMBEDDINGS: True,
            ProviderCapability.VISION: True,
            ProviderCapability.AUDIO: True,
            ProviderCapability.IMAGE_GENERATION: True,
        }

    def _build_payload(self, request: ProviderRequest) -> Tuple[str, Dict[str, Any]]:
        model = request.parameters.get("model", self.configuration.get("default_model", "gpt-4"))
        if request.parameters.get("image", False):
            return (
                f"{self.base_url}/images/generations",
                {"model": model, "prompt": request.input, **request.parameters},
            )
        return (
            f"{self.base_url}/chat/completions",
            {
                "model": model,
                "messages": _build_messages(request.input),
                **request.parameters,
                **({"stream": True} if request.stream else {}),
            },
        )


class AnthropicProvider(BaseProvider):
    """Anthropic provider implementation."""

    def __init__(
        self,
        provider_id: ProviderID = ProviderID.ANTHROPIC.value,
        settings: Optional[ProviderSettings] = None,
    ) -> None:
        headers = {}
        if settings and "api_key" in settings:
            headers["x-api-key"] = str(settings["api_key"])
        super().__init__(
            provider_id=provider_id,
            settings=settings,
            base_url=settings.get("base_url", "https://api.anthropic.com/v1") if settings else "https://api.anthropic.com/v1",
            headers=headers,
        )

    @property
    def capabilities(self) -> Dict[ProviderCapability, bool]:
        return {
            ProviderCapability.CHAT: True,
            ProviderCapability.STREAMING: True,
            ProviderCapability.REASONING: True,
            ProviderCapability.TOOL_CALLING: True,
        }

    def _build_payload(self, request: ProviderRequest) -> Tuple[str, Dict[str, Any]]:
        return (
            f"{self.base_url}/messages",
            {
                "model": request.parameters.get("model", "claude-3-sonnet-20240229"),
                "messages": _build_messages(request.input),
                **request.parameters,
                **({"stream": True} if request.stream else {}),
            },
        )


class GoogleProvider(BaseProvider):
    """Google Gemini provider implementation."""

    def __init__(
        self,
        provider_id: ProviderID = ProviderID.GOOGLE.value,
        settings: Optional[ProviderSettings] = None,
    ) -> None:
        headers = {}
        if settings and "api_key" in settings:
            headers["Authorization"] = f"Bearer {settings['api_key']}"
        super().__init__(
            provider_id=provider_id,
            settings=settings,
            base_url=settings.get("base_url", "https://gemini.googleapis.com/v1") if settings else "https://gemini.googleapis.com/v1",
            headers=headers,
        )

    @property
    def capabilities(self) -> Dict[ProviderCapability, bool]:
        return {
            ProviderCapability.CHAT: True,
            ProviderCapability.STREAMING: True,
            ProviderCapability.VISION: True,
            ProviderCapability.EMBEDDINGS: True,
        }

    def _build_payload(self, request: ProviderRequest) -> Tuple[str, Dict[str, Any]]:
        model = request.parameters.get("model", "gemini-1.5-pro")
        if isinstance(request.input, list):
            prompt = {"messages": request.input}
        else:
            prompt = {"text": str(request.input)}
        return (
            f"{self.base_url}/models/{model}:generateContent",
            {
                "model": model,
                "contents": [{"parts": [{"text": str(request.input)}]}],
                **request.parameters,
                **({"stream": True} if request.stream else {}),
            },
        )


class GroqProvider(BaseProvider):
    """Groq provider implementation."""

    def __init__(
        self,
        provider_id: ProviderID = ProviderID.GROQ.value,
        settings: Optional[ProviderSettings] = None,
    ) -> None:
        headers = {}
        if settings and "api_key" in settings:
            headers["Authorization"] = f"Bearer {settings['api_key']}"
        super().__init__(
            provider_id=provider_id,
            settings=settings,
            base_url=settings.get("base_url", "https://api.groq.com/v1") if settings else "https://api.groq.com/v1",
            headers=headers,
        )

    @property
    def capabilities(self) -> Dict[ProviderCapability, bool]:
        return {
            ProviderCapability.CHAT: True,
            ProviderCapability.STREAMING: True,
        }

    def _build_payload(self, request: ProviderRequest) -> Tuple[str, Dict[str, Any]]:
        return (
            f"{self.base_url}/chat/completions",
            {
                "model": request.parameters.get("model", "llama3-70b-8096"),
                "messages": _build_messages(request.input),
                **request.parameters,
                **({"stream": True} if request.stream else {}),
            },
        )


class DeepSeekProvider(BaseProvider):
    """DeepSeek provider implementation."""

    def __init__(
        self,
        provider_id: ProviderID = ProviderID.DEEPSEEK.value,
        settings: Optional[ProviderSettings] = None,
    ) -> None:
        headers = {}
        if settings and "api_key" in settings:
            headers["Authorization"] = f"Bearer {settings['api_key']}"
        super().__init__(
            provider_id=provider_id,
            settings=settings,
            base_url=settings.get("base_url", "https://api.deepseek.ai/v1") if settings else "https://api.deepseek.ai/v1",
            headers=headers,
        )

    @property
    def capabilities(self) -> Dict[ProviderCapability, bool]:
        return {
            ProviderCapability.CHAT: True,
            ProviderCapability.REASONING: True,
        }

    def _build_payload(self, request: ProviderRequest) -> Tuple[str, Dict[str, Any]]:
        payload = {
            "model": request.parameters.get("model", "deepseek-chat"),
            "messages": _build_messages(request.input),
            **request.parameters,
        }
        if request.parameters.get("image", False):
            payload["type"] = "image"
        return (f"{self.base_url}/chat/completions", payload)


class MistralProvider(BaseProvider):
    """Mistral provider implementation."""

    def __init__(
        self,
        provider_id: ProviderID = ProviderID.MISTRAL.value,
        settings: Optional[ProviderSettings] = None,
    ) -> None:
        headers = {}
        if settings and "api_key" in settings:
            headers["Authorization"] = f"Bearer {settings['api_key']}"
        super().__init__(
            provider_id=provider_id,
            settings=settings,
            base_url=settings.get("base_url", "https://api.mistral.ai/v1") if settings else "https://api.mistral.ai/v1",
            headers=headers,
        )

    @property
    def capabilities(self) -> Dict[ProviderCapability, bool]:
        return {
            ProviderCapability.CHAT: True,
            ProviderCapability.STREAMING: True,
            ProviderCapability.FUNCTION_CALLING: True,
        }

    def _build_payload(self, request: ProviderRequest) -> Tuple[str, Dict[str, Any]]:
        return (
            f"{self.base_url}/chat/completions",
            {
                "model": request.parameters.get("model", "mistral-large"),
                "messages": _build_messages(request.input),
                **request.parameters,
                **({"stream": True} if request.stream else {}),
            },
        )


class CohereProvider(BaseProvider):
    """Cohere provider implementation."""

    def __init__(
        self,
        provider_id: ProviderID = ProviderID.COHERE.value,
        settings: Optional[ProviderSettings] = None,
    ) -> None:
        headers = {}
        if settings and "api_key" in settings:
            headers["Authorization"] = f"Bearer {settings['api_key']}"
        super().__init__(
            provider_id=provider_id,
            settings=settings,
            base_url=settings.get("base_url", "https://api.cohere.ai/v1") if settings else "https://api.cohere.ai/v1",
            headers=headers,
        )

    @property
    def capabilities(self) -> Dict[ProviderCapability, bool]:
        return {
            ProviderCapability.CHAT: True,
            ProviderCapability.EMBEDDINGS: True,
        }

    def _build_payload(self, request: ProviderRequest) -> Tuple[str, Dict[str, Any]]:
        return (
            f"{self.base_url}/chat",
            {
                "model": request.parameters.get("model", "command-r"),
                "message": str(request.input),
                **request.parameters,
                **({"stream": True} if request.stream else {}),
            },
        )


class TogetherAIProvider(BaseProvider):
    """Together AI provider implementation."""

    def __init__(
        self,
        provider_id: ProviderID = ProviderID.TOGETHER.value,
        settings: Optional[ProviderSettings] = None,
    ) -> None:
        headers = {}
        if settings and "api_key" in settings:
            headers["Authorization"] = f"Bearer {settings['api_key']}"
        super().__init__(
            provider_id=provider_id,
            settings=settings,
            base_url=settings.get("base_url", "https://api.together.xyz/v1") if settings else "https://api.together.xyz/v1",
            headers=headers,
        )

    @property
    def capabilities(self) -> Dict[ProviderCapability, bool]:
        return {
            ProviderCapability.CHAT: True,
            ProviderCapability.STREAMING: True,
        }

    def _build_payload(self, request: ProviderRequest) -> Tuple[str, Dict[str, Any]]:
        return (
            f"{self.base_url}/chat/completions",
            {
                "model": request.parameters.get("model", "meta-llama/Llama-3-70b-chat-hf"),
                "messages": _build_messages(request.input),
                **request.parameters,
                **({"stream": True} if request.stream else {}),
            },
        )


class FireworksAIProvider(BaseProvider):
    """Fireworks AI provider implementation."""

    def __init__(
        self,
        provider_id: ProviderID = ProviderID.FIREWORKS.value,
        settings: Optional[ProviderSettings] = None,
    ) -> None:
        headers = {}
        if settings and "api_key" in settings:
            headers["Authorization"] = f"Bearer {settings['api_key']}"
        super().__init__(
            provider_id=provider_id,
            settings=settings,
            base_url=settings.get("base_url", "https://api.fireworks.ai/v1") if settings else "https://api.fireworks.ai/v1",
            headers=headers,
        )

    @property
    def capabilities(self) -> Dict[ProviderCapability, bool]:
        return {
            ProviderCapability.CHAT: True,
            ProviderCapability.STREAMING: True,
        }

    def _build_payload(self, request: ProviderRequest) -> Tuple[str, Dict[str, Any]]:
        return (
            f"{self.base_url}/chat/completions",
            {
                "model": request.parameters.get("model", "accounts/fireworks/models/llama-v3p1-70b"),
                "messages": _build_messages(request.input),
                **request.parameters,
                **({"stream": True} if request.stream else {}),
            },
        )


class AzureOpenAIProvider(BaseProvider):
    """Azure OpenAI provider implementation."""

    def __init__(
        self,
        provider_id: ProviderID = ProviderID.AZURE_OPENAI.value,
        settings: Optional[ProviderSettings] = None,
    ) -> None:
        headers = {}
        if settings and "api_key" in settings:
            headers["Authorization"] = f"Bearer {settings['api_key']}"
        super().__init__(
            provider_id=provider_id,
            settings=settings,
            base_url=settings.get("base_url", "https://{resource}.openai.azure.com/openai/deployments/{deployment}") if settings else "",
            headers=headers,
        )

    @property
    def capabilities(self) -> Dict[ProviderCapability, bool]:
        return {
            ProviderCapability.CHAT: True,
            ProviderCapability.STREAMING: True,
            ProviderCapability.FUNCTION_CALLING: True,
            ProviderCapability.EMBEDDINGS: True,
        }

    def _build_payload(self, request: ProviderRequest) -> Tuple[str, Dict[str, Any]]:
        return (
            f"{self.base_url}/chat/completions",
            {
                "model": request.parameters.get("model", "gpt-4"),
                "messages": _build_messages(request.input),
                **request.parameters,
                **({"stream": True} if request.stream else {}),
            },
        )


class OpenRouterProvider(BaseProvider):
    """OpenRouter provider implementation."""

    def __init__(
        self,
        provider_id: ProviderID = ProviderID.OPENROUTER.value,
        settings: Optional[ProviderSettings] = None,
    ) -> None:
        headers = {}
        if settings and "api_key" in settings:
            headers["Authorization"] = f"Bearer {settings['api_key']}"
        super().__init__(
            provider_id=provider_id,
            settings=settings,
            base_url=settings.get("base_url", "https://openrouter.ai/api/v1") if settings else "https://openrouter.ai/api/v1",
            headers=headers,
        )

    @property
    def capabilities(self) -> Dict[ProviderCapability, bool]:
        return {
            ProviderCapability.CHAT: True,
            ProviderCapability.STREAMING: True,
            ProviderCapability.FUNCTION_CALLING: True,
        }

    def _build_payload(self, request: ProviderRequest) -> Tuple[str, Dict[str, Any]]:
        return (
            f"{self.base_url}/chat/completions",
            {
                "model": request.parameters.get("model", "openai/gpt-4"),
                "messages": _build_messages(request.input),
                **request.parameters,
                **({"stream": True} if request.stream else {}),
            },
        )


class OllamaProvider(BaseProvider):
    """Ollama provider implementation."""

    def __init__(
        self,
        provider_id: ProviderID = ProviderID.OLLAMA.value,
        settings: Optional[ProviderSettings] = None,
    ) -> None:
        super().__init__(
            provider_id=provider_id,
            settings=settings,
            base_url=settings.get("base_url", "http://127.0.0.1:11434") if settings else "http://127.0.0.1:11434",
        )

    @property
    def capabilities(self) -> Dict[ProviderCapability, bool]:
        return {
            ProviderCapability.CHAT: True,
            ProviderCapability.STREAMING: True,
            ProviderCapability.EMBEDDINGS: True,
            ProviderCapability.OFFLINE: True,
        }

    def _build_payload(self, request: ProviderRequest) -> Tuple[str, Dict[str, Any]]:
        return (
            f"{self.base_url}/v1/chat/completions",
            {
                "model": request.parameters.get("model", "llama3"),
                "messages": _build_messages(request.input),
                **request.parameters,
                **({"stream": True} if request.stream else {}),
            },
        )


class LMStudioProvider(BaseProvider):
    """LM Studio provider implementation."""

    def __init__(
        self,
        provider_id: ProviderID = ProviderID.LMSTUDIO.value,
        settings: Optional[ProviderSettings] = None,
    ) -> None:
        super().__init__(
            provider_id=provider_id,
            settings=settings,
            base_url=settings.get("base_url", "http://127.0.0.1:1234") if settings else "http://127.0.0.1:1234",
        )

    @property
    def capabilities(self) -> Dict[ProviderCapability, bool]:
        return {
            ProviderCapability.CHAT: True,
            ProviderCapability.STREAMING: True,
            ProviderCapability.VISION: True,
            ProviderCapability.OFFLINE: True,
        }

    def _build_payload(self, request: ProviderRequest) -> Tuple[str, Dict[str, Any]]:
        return (
            f"{self.base_url}/v1/chat/completions",
            {
                "model": request.parameters.get("model", "llama3"),
                "messages": _build_messages(request.input),
                **request.parameters,
                **({"stream": True} if request.stream else {}),
            },
        )


class LocalModelProvider(BaseProvider):
    """Local model provider implementation (llama.cpp, vLLM, etc.)."""

    def __init__(
        self,
        provider_id: ProviderID = ProviderID.LOCAL.value,
        settings: Optional[ProviderSettings] = None,
    ) -> None:
        super().__init__(
            provider_id=provider_id,
            settings=settings,
            base_url=settings.get("base_url", "http://127.0.0.1:8000") if settings else "http://127.0.0.1:8000",
        )

    @property
    def capabilities(self) -> Dict[ProviderCapability, bool]:
        return {
            ProviderCapability.CHAT: True,
            ProviderCapability.STREAMING: True,
            ProviderCapability.OFFLINE: True,
        }

    def _build_payload(self, request: ProviderRequest) -> Tuple[str, Dict[str, Any]]:
        return (
            f"{self.base_url}/v1/chat/completions",
            {
                "model": request.parameters.get("model", "llama3"),
                "messages": _build_messages(request.input),
                **request.parameters,
                **({"stream": True} if request.stream else {}),
            },
        )


class CustomProvider(BaseProvider):
    """Custom provider implementation for unsupported providers."""

    def __init__(
        self,
        provider_id: ProviderID = ProviderID.CUSTOM.value,
        settings: Optional[ProviderSettings] = None,
    ) -> None:
        super().__init__(
            provider_id=provider_id,
            settings=settings,
            base_url=settings.get("base_url", "") if settings else "",
        )

    @property
    def capabilities(self) -> Dict[ProviderCapability, bool]:
        return {
            ProviderCapability.CHAT: True,
        }

    def _build_payload(self, request: ProviderRequest) -> Tuple[str, Dict[str, Any]]:
        return (
            f"{self.base_url}",
            {
                "model": request.parameters.get("model", "default"),
                "input": request.input,
                **request.parameters,
                **({"stream": True} if request.stream else {}),
            },
        )
