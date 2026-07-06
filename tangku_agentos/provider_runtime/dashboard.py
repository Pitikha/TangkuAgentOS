from __future__ import annotations

from typing import Any

from .hub import ProviderHub


class ProviderDashboard:
    """Backend for provider dashboard cards."""

    def __init__(self, hub: ProviderHub) -> None:
        self._hub = hub

    def build_cards(self) -> list[dict[str, Any]]:
        cards: list[dict[str, Any]] = []
        providers = sorted(self._hub.list_provider_details(), key=lambda provider: (provider.get("provider_id") != "ollama", provider.get("provider_id", "")))
        for provider in providers:
            cards.append(
                {
                    "provider_id": provider["provider_id"],
                    "display_name": provider["display_name"],
                    "provider_type": provider["provider_type"],
                    "status": "connected" if provider.get("connected") else "offline",
                    "health": "healthy" if provider.get("connected") else "degraded",
                    "latency_ms": 12,
                    "models": [model["model_id"] for model in self._hub.list_models() if model.get("provider_id") == provider["provider_id"]],
                    "default_model": self._hub._best_model_for_provider(provider["provider_id"], "chat") if hasattr(self._hub, "_best_model_for_provider") else None,
                    "capabilities": provider["capabilities"],
                    "streaming": provider["capabilities"].get("streaming", False),
                    "vision": provider["capabilities"].get("vision", False),
                    "function_calling": provider["capabilities"].get("function_calling", False),
                    "reasoning": provider["capabilities"].get("reasoning", False),
                    "embeddings": provider["capabilities"].get("embeddings", False),
                    "image_generation": provider["capabilities"].get("image_generation", False),
                    "audio": provider["capabilities"].get("audio", False),
                    "pricing": {"currency": "USD", "cost": 0.0},
                    "speed": "fast",
                    "availability": "available",
                    "connection_errors": [],
                    "recommended_actions": ["refresh"],
                }
            )
        return cards
