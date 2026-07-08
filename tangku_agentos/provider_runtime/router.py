"""Routing for the TangkuAgentOS Provider Runtime."""

from __future__ import annotations

from threading import RLock
from typing import Any, Dict, List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from .types import ProviderCapability, ProviderID, RoutingPolicy

from .constants import ProviderCapability, RoutingPolicy
from .exceptions import NoProviderAvailableError


class SmartModelRouter:
    """
    Routes requests to providers based on:
    - Model capabilities
    - Cost
    - Speed
    - Latency
    - Availability
    - Context length
    - Streaming support
    - Vision support
    - Tool calling
    - Function calling
    - Embeddings
    - Audio
    - Image generation
    """

    def __init__(self, hub: Any = None) -> None:
        self._hub = hub
        self._lock = RLock()
        self._routing_table: Dict[str, Dict[str, Any]] = {}

    def route_for_task(
        self,
        task: str,
        policy: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Route a request for a task based on the policy.
        Supports routing by:
        - Capability
        - Cost
        - Latency
        - Availability
        - Context length
        - Streaming support
        - Vision support
        - Tool calling
        - Function calling
        - Embeddings
        - Audio
        - Image generation
        """
        policy = policy or {}
        providers = self._get_provider_details()

        if not providers:
            raise NoProviderAvailableError("No providers available")

        # Check for explicit routing rules
        for rule in self._get_routing_rules():
            if rule.get("task") == task and rule.get("provider"):
                provider_id = rule["provider"]
                model_id = self._get_best_model_for_provider(provider_id, task)
                return {
                    "provider_id": provider_id,
                    "model_id": model_id,
                    "task": task,
                    "policy": policy,
                }

        # Filter by capability
        required_capabilities = self._get_required_capabilities(task)
        filtered_providers = [
            p for p in providers if self._has_capabilities(p, required_capabilities)
        ]

        if not filtered_providers:
            raise NoProviderAvailableError(f"No providers support {task}")

        # Apply policy-based routing
        if policy.get("policy") == RoutingPolicy.COST:
            selected = self._select_by_cost(filtered_providers)
        elif policy.get("policy") == RoutingPolicy.LATENCY:
            selected = self._select_by_latency(filtered_providers)
        elif policy.get("policy") == RoutingPolicy.AVAILABILITY:
            selected = self._select_by_availability(filtered_providers)
        elif policy.get("policy") == RoutingPolicy.CAPABILITY:
            selected = self._select_by_capability(filtered_providers, required_capabilities)
        else:
            selected = filtered_providers[0]

        model_id = self._get_best_model_for_provider(selected["provider_id"], task)
        return {
            "provider_id": selected["provider_id"],
            "model_id": model_id,
            "task": task,
            "policy": policy,
        }

    def _get_provider_details(self) -> List[Dict[str, Any]]:
        """Get provider details from the hub."""
        if self._hub is not None:
            return self._hub.list_provider_details()
        return []

    def _get_routing_rules(self) -> List[Dict[str, Any]]:
        """Get routing rules from the hub."""
        if self._hub is not None:
            return self._hub.list_routing_rules()
        return []

    def _get_best_model_for_provider(self, provider_id: str, task: str) -> str:
        """Get the best model for a provider and task."""
        if self._hub is not None:
            return self._hub._best_model_for_provider(provider_id, task)
        return "default"

    def _get_required_capabilities(self, task: str) -> Dict[ProviderCapability, bool]:
        """Get required capabilities for a task."""
        capability_map = {
            "chat": {ProviderCapability.CHAT: True},
            "embedding": {ProviderCapability.EMBEDDINGS: True},
            "vision": {ProviderCapability.VISION: True},
            "audio": {ProviderCapability.AUDIO: True},
            "image_generation": {ProviderCapability.IMAGE_GENERATION: True},
            "tool_calling": {ProviderCapability.TOOL_CALLING: True},
            "function_calling": {ProviderCapability.FUNCTION_CALLING: True},
            "reasoning": {ProviderCapability.REASONING: True},
        }
        return capability_map.get(task, {})

    def _has_capabilities(
        self, provider: Dict[str, Any], required: Dict[ProviderCapability, bool]
    ) -> bool:
        """Check if a provider has the required capabilities."""
        capabilities = provider.get("capabilities", {})
        return all(capabilities.get(cap.value, False) for cap in required)

    def _select_by_cost(self, providers: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Select the provider with the lowest cost."""
        return min(
            providers,
            key=lambda p: p.get("pricing", {}).get("cost", float("inf")),
        )

    def _select_by_latency(self, providers: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Select the provider with the lowest latency."""
        return min(
            providers,
            key=lambda p: p.get("latency_ms", float("inf")),
        )

    def _select_by_availability(self, providers: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Select the most available provider."""
        return max(
            providers,
            key=lambda p: 1 if p.get("connected", False) else 0,
        )

    def _select_by_capability(
        self, providers: List[Dict[str, Any]], required: Dict[ProviderCapability, bool]
    ) -> Dict[str, Any]:
        """Select the provider with the most matching capabilities."""
        return max(
            providers,
            key=lambda p: sum(
                1 for cap in required if p.get("capabilities", {}).get(cap.value, False)
            ),
        )

    def add_routing_rule(self, rule: Dict[str, Any]) -> None:
        """Add a routing rule."""
        with self._lock:
            self._routing_table[rule.get("task", "")] = rule

    def remove_routing_rule(self, task: str) -> None:
        """Remove a routing rule."""
        with self._lock:
            self._routing_table.pop(task, None)

    def list_routing_rules(self) -> List[Dict[str, Any]]:
        """List all routing rules."""
        return list(self._routing_table.values())
