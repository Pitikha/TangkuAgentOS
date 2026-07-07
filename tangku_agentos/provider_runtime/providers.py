from __future__ import annotations

from typing import Any

from .integration import HTTPProviderAdapter


def _build_messages(input_value: str | list[dict[str, Any]]) -> list[dict[str, Any]]:
    if isinstance(input_value, list):
        return input_value
    return [{"role": "user", "content": str(input_value)}]


def _build_text(input_value: str | list[dict[str, Any]]) -> str:
    if isinstance(input_value, list):
        pieces: list[str] = []
        for item in input_value:
            if isinstance(item, dict):
                pieces.append(str(item.get("content", "")))
            else:
                pieces.append(str(item))
        return "\n".join(filter(None, pieces))
    return str(input_value)


def _build_anthropic_prompt(input_value: str | list[dict[str, Any]]) -> str:
    if isinstance(input_value, list):
        sections: list[str] = []
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


class OpenAIProvider(HTTPProviderAdapter):
    def __init__(self, provider_id: str, configuration: dict[str, Any] | None = None) -> None:
        settings = configuration or {}
        headers = {"Authorization": f"Bearer {settings.get('api_key', '')}"}
        if settings.get("organization"):
            headers["OpenAI-Organization"] = str(settings["organization"])
        headers.update(settings.get("headers", {}) or {})
        super().__init__(provider_id, settings, base_url=settings.get("base_url", "https://api.openai.com/v1"), headers=headers, timeout_seconds=settings.get("timeout", 30.0), max_retries=settings.get("max_retries", 3))

    def _build_payload(self, request: dict[str, Any]) -> tuple[str, dict[str, Any]]:
        model = request["model"]
        if request["image"]:
            return (
                f"{self.base_url}/images/generations",
                {"model": model, "prompt": request["input"], **request["parameters"]},
            )

        return (
            f"{self.base_url}/chat/completions",
            {
                "model": model,
                "messages": _build_messages(request["input"]),
                **request["parameters"],
                **({"stream": True} if request["stream"] else {}),
            },
        )


class AnthropicProvider(HTTPProviderAdapter):
    def __init__(self, provider_id: str, configuration: dict[str, Any] | None = None) -> None:
        settings = configuration or {}
        headers = {"x-api-key": str(settings.get("api_key", ""))}
        headers.update(settings.get("headers", {}) or {})
        super().__init__(provider_id, settings, base_url=settings.get("base_url", "https://api.anthropic.com/v1"), headers=headers, timeout_seconds=settings.get("timeout", 30.0), max_retries=settings.get("max_retries", 3))

    def _build_payload(self, request: dict[str, Any]) -> tuple[str, dict[str, Any]]:
        return (
            f"{self.base_url}/complete",
            {
                "model": request["model"],
                "prompt": _build_anthropic_prompt(request["input"]),
                **request["parameters"],
                **({"stream": True} if request["stream"] else {}),
            },
        )


class GoogleProvider(HTTPProviderAdapter):
    def __init__(self, provider_id: str, configuration: dict[str, Any] | None = None) -> None:
        settings = configuration or {}
        headers = {"Authorization": f"Bearer {settings.get('api_key', '')}"}
        headers.update(settings.get("headers", {}) or {})
        super().__init__(provider_id, settings, base_url=settings.get("base_url", "https://gemini.googleapis.com/v1"), headers=headers, timeout_seconds=settings.get("timeout", 30.0), max_retries=settings.get("max_retries", 3))

    def _build_payload(self, request: dict[str, Any]) -> tuple[str, dict[str, Any]]:
        if isinstance(request["input"], list):
            prompt = {"messages": request["input"]}
        else:
            prompt = {"text": str(request["input"])}

        return (
            f"{self.base_url}/models/{request['model']}:generate",
            {
                "model": request["model"],
                "prompt": prompt,
                **request["parameters"],
                **({"streaming": True} if request["stream"] else {}),
            },
        )


class GroqProvider(HTTPProviderAdapter):
    def __init__(self, provider_id: str, configuration: dict[str, Any] | None = None) -> None:
        settings = configuration or {}
        headers = {"Authorization": f"Bearer {settings.get('api_key', '')}"}
        headers.update(settings.get("headers", {}) or {})
        super().__init__(provider_id, settings, base_url=settings.get("base_url", "https://api.groq.com/v1"), headers=headers, timeout_seconds=settings.get("timeout", 30.0), max_retries=settings.get("max_retries", 3))

    def _build_payload(self, request: dict[str, Any]) -> tuple[str, dict[str, Any]]:
        return (
            f"{self.base_url}/completions",
            {
                "model": request["model"],
                "prompt": _build_text(request["input"]),
                **request["parameters"],
                **({"stream": True} if request["stream"] else {}),
            },
        )


class DeepSeekProvider(HTTPProviderAdapter):
    def __init__(self, provider_id: str, configuration: dict[str, Any] | None = None) -> None:
        settings = configuration or {}
        headers = {"Authorization": f"Bearer {settings.get('api_key', '')}"}
        headers.update(settings.get("headers", {}) or {})
        super().__init__(provider_id, settings, base_url=settings.get("base_url", "https://api.deepseek.ai/v1"), headers=headers, timeout_seconds=settings.get("timeout", 30.0), max_retries=settings.get("max_retries", 3))

    def _build_payload(self, request: dict[str, Any]) -> tuple[str, dict[str, Any]]:
        payload = {
            "model": request["model"],
            "input": request["input"],
            **request["parameters"],
            **({"stream": True} if request["stream"] else {}),
        }
        if request["image"]:
            payload["type"] = "image"
        return (f"{self.base_url}/generate", payload)


class OpenRouterProvider(HTTPProviderAdapter):
    def __init__(self, provider_id: str, configuration: dict[str, Any] | None = None) -> None:
        settings = configuration or {}
        headers = {"Authorization": f"Bearer {settings.get('api_key', '')}"}
        headers.update(settings.get("headers", {}) or {})
        super().__init__(provider_id, settings, base_url=settings.get("base_url", "https://api.openrouter.ai/v1"), headers=headers, timeout_seconds=settings.get("timeout", 30.0), max_retries=settings.get("max_retries", 3))

    def _build_payload(self, request: dict[str, Any]) -> tuple[str, dict[str, Any]]:
        return (
            f"{self.base_url}/chat/completions",
            {
                "model": request["model"],
                "messages": _build_messages(request["input"]),
                **request["parameters"],
                **({"stream": True} if request["stream"] else {}),
            },
        )


class OllamaProvider(HTTPProviderAdapter):
    def __init__(self, provider_id: str, configuration: dict[str, Any] | None = None) -> None:
        settings = configuration or {}
        headers = {"Authorization": f"Bearer {settings.get('api_key', '')}"}
        headers.update(settings.get("headers", {}) or {})
        super().__init__(provider_id, settings, base_url=settings.get("base_url", "http://127.0.0.1:11434"), headers=headers, timeout_seconds=settings.get("timeout", 30.0), max_retries=settings.get("max_retries", 3))

    def _build_payload(self, request: dict[str, Any]) -> tuple[str, dict[str, Any]]:
        return (
            f"{self.base_url}/v1/models/{request['model']}/chat/completions",
            {
                "model": request["model"],
                "messages": _build_messages(request["input"]),
                **request["parameters"],
                **({"stream": True} if request["stream"] else {}),
            },
        )


class LMStudioProvider(HTTPProviderAdapter):
    def __init__(self, provider_id: str, configuration: dict[str, Any] | None = None) -> None:
        settings = configuration or {}
        headers = {"Authorization": f"Bearer {settings.get('api_key', '')}"}
        headers.update(settings.get("headers", {}) or {})
        super().__init__(provider_id, settings, base_url=settings.get("base_url", "http://127.0.0.1:8080"), headers=headers, timeout_seconds=settings.get("timeout", 30.0), max_retries=settings.get("max_retries", 3))

    def _build_payload(self, request: dict[str, Any]) -> tuple[str, dict[str, Any]]:
        return (
            f"{self.base_url}/api/v1/generate",
            {
                "model": request["model"],
                "prompt": request["input"],
                **request["parameters"],
                **({"stream": True} if request["stream"] else {}),
            },
        )


class LocalModelProvider(HTTPProviderAdapter):
    def __init__(self, provider_id: str, configuration: dict[str, Any] | None = None) -> None:
        settings = configuration or {}
        headers = {"Authorization": f"Bearer {settings.get('api_key', '')}"}
        headers.update(settings.get("headers", {}) or {})
        super().__init__(provider_id, settings, base_url=settings.get("base_url", "http://127.0.0.1:8080"), headers=headers, timeout_seconds=settings.get("timeout", 30.0), max_retries=settings.get("max_retries", 3))

    def _build_payload(self, request: dict[str, Any]) -> tuple[str, dict[str, Any]]:
        return (
            f"{self.base_url}/api/v1/generate",
            {
                "model": request["model"],
                "prompt": request["input"],
                **request["parameters"],
                **({"stream": True} if request["stream"] else {}),
            },
        )


class CustomProvider(HTTPProviderAdapter):
    def __init__(self, provider_id: str, configuration: dict[str, Any] | None = None) -> None:
        settings = configuration or {}
        headers = settings.get("headers", {}) or {}
        super().__init__(provider_id, settings, base_url=settings.get("base_url", ""), headers=headers, timeout_seconds=settings.get("timeout", 30.0), max_retries=settings.get("max_retries", 3))

    def _build_payload(self, request: dict[str, Any]) -> tuple[str, dict[str, Any]]:
        return (
            f"{self.base_url}",
            {
                "model": request["model"],
                "input": request["input"],
                **request["parameters"],
                **({"stream": True} if request["stream"] else {}),
            },
        )
