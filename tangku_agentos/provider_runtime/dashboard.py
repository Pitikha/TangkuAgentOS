"""Dashboard for the TangkuAgentOS Provider Runtime."""

from __future__ import annotations

from threading import RLock
from typing import Any, Dict, List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from .types import ProviderID

from .constants import ProviderCapability, ProviderStatus, ProviderType


class ProviderDashboard:
    """
    Provides provider statistics including:
    - Active providers
    - Health
    - Requests
    - Failures
    - Costs
    - Token usage
    - Average latency
    - Uptime
    """

    def __init__(self, hub: Any = None) -> None:
        self._hub = hub
        self._lock = RLock()

    def build_cards(self) -> List[Dict[str, Any]]:
        """Build dashboard cards for all providers."""
        providers = self._get_provider_details()
        cards: List[Dict[str, Any]] = []

        for provider in providers:
            card = self._build_provider_card(provider)
            cards.append(card)

        return cards

    def _get_provider_details(self) -> List[Dict[str, Any]]:
        """Get provider details from the hub."""
        if self._hub is not None:
            return self._hub.list_provider_details()
        return []

    def _build_provider_card(self, provider: Dict[str, Any]) -> Dict[str, Any]:
        """Build a dashboard card for a provider."""
        provider_id = provider.get("provider_id", "unknown")
        display_name = provider.get("display_name", provider_id)
        provider_type = provider.get("provider_type", ProviderType.CLOUD.value)
        status = provider.get("status", ProviderStatus.UNREGISTERED.value)
        connected = provider.get("connected", False)
        health = provider.get("health", "unknown")

        # Get models for this provider
        models = self._get_models_for_provider(provider_id)

        # Get capabilities
        capabilities = provider.get("capabilities", {})

        # Get usage stats
        usage = self._get_usage_stats(provider_id)

        # Get latency
        latency = self._get_latency(provider_id)

        return {
            "provider_id": provider_id,
            "display_name": display_name,
            "provider_type": provider_type,
            "status": "connected" if connected else "offline",
            "health": health,
            "latency_ms": latency,
            "models": models,
            "default_model": self._get_default_model(provider_id),
            "capabilities": self._format_capabilities(capabilities),
            "streaming": capabilities.get(ProviderCapability.STREAMING.value, False),
            "vision": capabilities.get(ProviderCapability.VISION.value, False),
            "function_calling": capabilities.get(ProviderCapability.FUNCTION_CALLING.value, False),
            "reasoning": capabilities.get(ProviderCapability.REASONING.value, False),
            "embeddings": capabilities.get(ProviderCapability.EMBEDDINGS.value, False),
            "image_generation": capabilities.get(ProviderCapability.IMAGE_GENERATION.value, False),
            "audio": capabilities.get(ProviderCapability.AUDIO.value, False),
            "pricing": {"currency": "USD", "cost": 0.0},
            "speed": "fast",
            "availability": "available" if connected else "unavailable",
            "connection_errors": [],
            "recommended_actions": self._get_recommended_actions(provider_id),
            "stats": usage,
        }

    def _get_models_for_provider(self, provider_id: str) -> List[str]:
        """Get models for a provider."""
        if self._hub is not None:
            models = self._hub.list_models()
            return [
                model.get("model_id", "")
                for model in models
                if model.get("provider_id") == provider_id
            ]
        return []

    def _get_default_model(self, provider_id: str) -> Optional[str]:
        """Get the default model for a provider."""
        if self._hub is not None:
            return self._hub._best_model_for_provider(provider_id, "chat")
        return None

    def _get_usage_stats(self, provider_id: str) -> Dict[str, Any]:
        """Get usage statistics for a provider."""
        if self._hub is not None:
            usage_manager = getattr(self._hub, "_usage_manager", None)
            if usage_manager is not None:
                return usage_manager.get_usage(provider_id)
        return {
            "total_requests": 0,
            "total_tokens": 0,
            "total_cost": 0.0,
        }

    def _get_latency(self, provider_id: str) -> float:
        """Get the average latency for a provider."""
        if self._hub is not None:
            health_monitor = getattr(self._hub, "_health_monitor", None)
            if health_monitor is not None:
                status = health_monitor.get_status(provider_id)
                if status is not None:
                    return status.latency_ms
        return 0.0

    def _format_capabilities(self, capabilities: Dict[str, bool]) -> Dict[str, bool]:
        """Format capabilities for display."""
        return {
            cap: capabilities.get(cap, False)
            for cap in [
                ProviderCapability.CHAT.value,
                ProviderCapability.STREAMING.value,
                ProviderCapability.EMBEDDINGS.value,
                ProviderCapability.VISION.value,
                ProviderCapability.AUDIO.value,
                ProviderCapability.IMAGE_GENERATION.value,
                ProviderCapability.TOOL_CALLING.value,
                ProviderCapability.FUNCTION_CALLING.value,
                ProviderCapability.REASONING.value,
            ]
        }

    def _get_recommended_actions(self, provider_id: str) -> List[str]:
        """Get recommended actions for a provider."""
        actions = []
        if self._hub is not None:
            health_monitor = getattr(self._hub, "_health_monitor", None)
            if health_monitor is not None:
                status = health_monitor.get_status(provider_id)
                if status is not None:
                    if status.disabled:
                        actions.append("re-enable")
                    if status.status.value == "degraded":
                        actions.append("check_health")
                    if not status.disabled and status.consecutive_failures > 0:
                        actions.append("investigate_failures")
        actions.append("refresh")
        return actions

    def get_summary(self) -> Dict[str, Any]:
        """Get a summary of all provider statistics."""
        providers = self._get_provider_details()
        total_providers = len(providers)
        connected_providers = sum(1 for p in providers if p.get("connected", False))
        healthy_providers = sum(
            1 for p in providers if p.get("health") == "healthy"
        )

        total_requests = 0
        total_tokens = 0
        total_cost = 0.0

        for provider in providers:
            provider_id = provider.get("provider_id", "")
            usage = self._get_usage_stats(provider_id)
            total_requests += usage.get("total_requests", 0)
            total_tokens += usage.get("total_tokens", 0)
            total_cost += usage.get("total_cost", 0.0)

        avg_latency = sum(
            self._get_latency(p.get("provider_id", "")) for p in providers
        ) / total_providers if total_providers > 0 else 0.0

        return {
            "total_providers": total_providers,
            "connected_providers": connected_providers,
            "healthy_providers": healthy_providers,
            "total_requests": total_requests,
            "total_tokens": total_tokens,
            "total_cost": total_cost,
            "avg_latency_ms": avg_latency,
            "uptime": self._calculate_uptime(),
        }

    def _calculate_uptime(self) -> float:
        """Calculate overall uptime percentage."""
        providers = self._get_provider_details()
        if not providers:
            return 0.0
        connected = sum(1 for p in providers if p.get("connected", False))
        return (connected / len(providers)) * 100

    def get_provider_stats(self, provider_id: str) -> Dict[str, Any]:
        """Get detailed statistics for a specific provider."""
        provider = next(
            (p for p in self._get_provider_details() if p.get("provider_id") == provider_id),
            None,
        )
        if provider is None:
            return {"error": "Provider not found"}

        return {
            "provider": provider,
            "usage": self._get_usage_stats(provider_id),
            "latency": self._get_latency(provider_id),
            "health": self._hub._health_monitor.get_status(provider_id) if self._hub else None,
        }
