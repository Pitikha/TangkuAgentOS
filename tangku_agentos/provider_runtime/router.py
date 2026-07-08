"""Routing for the TangkuAgentOS Provider Runtime."""

from __future__ import annotations

import random
import time
from dataclasses import dataclass, field
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
        routing_policy = policy.get("policy", RoutingPolicy.CAPABILITY.value)
        if routing_policy == RoutingPolicy.COST.value:
            selected = self._select_by_cost(filtered_providers)
        elif routing_policy == RoutingPolicy.LATENCY.value:
            selected = self._select_by_latency(filtered_providers)
        elif routing_policy == RoutingPolicy.AVAILABILITY.value:
            selected = self._select_by_availability(filtered_providers)
        elif routing_policy == RoutingPolicy.CAPABILITY.value:
            selected = self._select_by_capability(filtered_providers, required_capabilities)
        elif routing_policy == RoutingPolicy.RANDOM.value:
            selected = random.choice(filtered_providers)
        elif routing_policy == RoutingPolicy.ROUND_ROBIN.value:
            selected = self._select_round_robin(filtered_providers)
        elif routing_policy == RoutingPolicy.WEIGHTED.value:
            weights = policy.get("weights", {})
            selected = self._select_weighted(filtered_providers, weights)
        elif routing_policy == RoutingPolicy.PRIORITY.value:
            priorities = policy.get("priorities", {})
            selected = self._select_priority(filtered_providers, priorities)
        elif routing_policy == RoutingPolicy.CONSENSUS.value:
            return self._route_consensus(task, filtered_providers, policy)
        elif routing_policy == RoutingPolicy.ENSEMBLE.value:
            return self._route_ensemble(task, filtered_providers, policy)
        elif routing_policy == RoutingPolicy.HYBRID.value:
            return self._route_hybrid(task, filtered_providers, policy)
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

    def _select_round_robin(self, providers: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Select a provider using round-robin."""
        with self._lock:
            if "round_robin_index" not in self._routing_table:
                self._routing_table["round_robin_index"] = 0
            index = self._routing_table["round_robin_index"] % len(providers)
            self._routing_table["round_robin_index"] += 1
            return providers[index]

    def _select_weighted(
        self, providers: List[Dict[str, Any]], weights: Dict[str, float]
    ) -> Dict[str, Any]:
        """Select a provider using weighted random selection."""
        total = sum(weights.get(p["provider_id"], 1.0) for p in providers)
        r = random.uniform(0, total)
        upto = 0
        for p in providers:
            upto += weights.get(p["provider_id"], 1.0)
            if upto >= r:
                return p
        return providers[0]

    def _select_priority(
        self, providers: List[Dict[str, Any]], priorities: Dict[str, int]
    ) -> Dict[str, Any]:
        """Select a provider based on priority."""
        return max(
            providers,
            key=lambda p: priorities.get(p["provider_id"], 0),
        )

    def _route_consensus(
        self, task: str, providers: List[Dict[str, Any]], policy: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Route a request using consensus from multiple providers."""
        if self._hub is None:
            raise NoProviderAvailableError("Hub is required for consensus routing")
        num_providers = min(policy.get("num_providers", 3), len(providers))
        selected_providers = providers[:num_providers]
        return {
            "provider_ids": [p["provider_id"] for p in selected_providers],
            "task": task,
            "policy": {"type": "consensus", **policy},
            "model_ids": [
                self._get_best_model_for_provider(p["provider_id"], task)
                for p in selected_providers
            ],
        }

    def _route_ensemble(
        self, task: str, providers: List[Dict[str, Any]], policy: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Route a request using ensemble reasoning from multiple providers."""
        if self._hub is None:
            raise NoProviderAvailableError("Hub is required for ensemble routing")
        num_providers = min(policy.get("num_providers", 3), len(providers))
        selected_providers = providers[:num_providers]
        return {
            "provider_ids": [p["provider_id"] for p in selected_providers],
            "task": task,
            "policy": {"type": "ensemble", **policy},
            "model_ids": [
                self._get_best_model_for_provider(p["provider_id"], task)
                for p in selected_providers
            ],
        }

    def _route_hybrid(
        self, task: str, providers: List[Dict[str, Any]], policy: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Route a request using hybrid routing (cost + latency + capability)."""
        weights = policy.get("weights", {"cost": 0.4, "latency": 0.3, "capability": 0.3})
        scored_providers = []
        for p in providers:
            cost_score = 1.0 / (p.get("pricing", {}).get("cost", 1.0) + 0.0001)
            latency_score = 1.0 / (p.get("latency_ms", 1000.0) + 0.0001)
            capability_score = sum(
                1 for cap in self._get_required_capabilities(task)
                if p.get("capabilities", {}).get(cap.value, False)
            )
            total_score = (
                weights.get("cost", 0.4) * cost_score
                + weights.get("latency", 0.3) * latency_score
                + weights.get("capability", 0.3) * capability_score
            )
            scored_providers.append((p, total_score))
        scored_providers.sort(key=lambda x: x[1], reverse=True)
        selected = scored_providers[0][0]
        model_id = self._get_best_model_for_provider(selected["provider_id"], task)
        return {
            "provider_id": selected["provider_id"],
            "model_id": model_id,
            "task": task,
            "policy": {"type": "hybrid", **policy},
        }

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


# --- New Routers for Phase 8 ---


class WeightedRouter:
    """Routes requests to providers based on weights."""

    def __init__(self, weights: Optional[Dict[str, float]] = None) -> None:
        self.weights = weights or {}
        self._lock = RLock()

    def select_provider(self, providers: List[str]) -> str:
        """Select a provider using weighted random selection."""
        total = sum(self.weights.get(p, 1.0) for p in providers)
        if total <= 0:
            return providers[0]
        r = random.uniform(0, total)
        upto = 0
        for p in providers:
            upto += self.weights.get(p, 1.0)
            if upto >= r:
                return p
        return providers[0]

    def update_weights(self, weights: Dict[str, float]) -> None:
        """Update the weights for providers."""
        with self._lock:
            self.weights.update(weights)


class CircuitBreaker:
    """
    Circuit breaker pattern for provider failover.
    Prevents requests to failing providers after a threshold of failures.
    """

    def __init__(
        self, max_failures: int = 3, reset_timeout: float = 30.0
    ) -> None:
        self.max_failures = max_failures
        self.reset_timeout = reset_timeout
        self.failures: Dict[str, int] = {}
        self.last_failure: Dict[str, float] = {}
        self._lock = RLock()

    def is_open(self, provider_id: str) -> bool:
        """Check if the circuit breaker is open for a provider."""
        with self._lock:
            if self.failures.get(provider_id, 0) >= self.max_failures:
                if time.time() - self.last_failure.get(provider_id, 0) < self.reset_timeout:
                    return True
                self.failures[provider_id] = 0
            return False

    def record_failure(self, provider_id: str) -> None:
        """Record a failure for a provider."""
        with self._lock:
            self.failures[provider_id] = self.failures.get(provider_id, 0) + 1
            self.last_failure[provider_id] = time.time()

    def reset(self, provider_id: str) -> None:
        """Reset the circuit breaker for a provider."""
        with self._lock:
            self.failures[provider_id] = 0

    def get_state(self, provider_id: str) -> Dict[str, Any]:
        """Get the current state of the circuit breaker for a provider."""
        with self._lock:
            return {
                "provider_id": provider_id,
                "failures": self.failures.get(provider_id, 0),
                "last_failure": self.last_failure.get(provider_id, 0),
                "is_open": self.is_open(provider_id),
            }


class ConsensusRouter:
    """Routes requests to multiple providers and aggregates responses for consensus."""

    def __init__(self, hub: Any = None) -> None:
        self._hub = hub
        self._lock = RLock()

    def route_consensus(
        self, request: Dict[str, Any], num_providers: int = 3
    ) -> Dict[str, Any]:
        """Route a request to multiple providers and return a consensus response."""
        if self._hub is None:
            raise NoProviderAvailableError("Hub is required for consensus routing")
        providers = self._hub.list_providers()[:num_providers]
        if not providers:
            raise NoProviderAvailableError("No providers available")
        return {
            "type": "consensus",
            "provider_ids": providers,
            "request": request,
        }

    def aggregate_responses(self, responses: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Aggregate responses from multiple providers for consensus."""
        if not responses:
            return {"error": "No responses to aggregate"}
        # Simple majority vote for text responses
        texts = [r.get("output", {}).get("text", "") for r in responses if r.get("success", False)]
        if not texts:
            return {"error": "No successful responses"}
        # Return the most common response (simplified consensus)
        from collections import Counter
        most_common = Counter(texts).most_common(1)[0][0]
        return {
            "consensus": most_common,
            "responses": responses,
        }


class EnsembleRouter:
    """Routes requests to multiple providers and combines responses for ensemble reasoning."""

    def __init__(self, hub: Any = None) -> None:
        self._hub = hub
        self._lock = RLock()

    def route_ensemble(
        self, request: Dict[str, Any], num_providers: int = 3
    ) -> Dict[str, Any]:
        """Route a request to multiple providers and return an ensemble response."""
        if self._hub is None:
            raise NoProviderAvailableError("Hub is required for ensemble routing")
        providers = self._hub.list_providers()[:num_providers]
        if not providers:
            raise NoProviderAvailableError("No providers available")
        return {
            "type": "ensemble",
            "provider_ids": providers,
            "request": request,
        }

    def aggregate_responses(self, responses: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Aggregate responses from multiple providers for ensemble reasoning."""
        if not responses:
            return {"error": "No responses to aggregate"}
        # Combine all text responses (simplified ensemble)
        texts = [r.get("output", {}).get("text", "") for r in responses if r.get("success", False)]
        if not texts:
            return {"error": "No successful responses"}
        combined = "\n\n".join(texts)
        return {
            "ensemble": combined,
            "responses": responses,
        }


class HybridRouter:
    """Combines multiple routing strategies (cost, latency, capability)."""

    def __init__(self, hub: Any = None) -> None:
        self._hub = hub
        self._lock = RLock()

    def route(
        self,
        task: str,
        policy: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Route a request using a hybrid of cost, latency, and capability."""
        policy = policy or {}
        providers = self._get_provider_details()
        if not providers:
            raise NoProviderAvailableError("No providers available")

        weights = policy.get("weights", {"cost": 0.4, "latency": 0.3, "capability": 0.3})
        scored_providers = []
        required_capabilities = self._get_required_capabilities(task)

        for p in providers:
            cost_score = 1.0 / (p.get("pricing", {}).get("cost", 1.0) + 0.0001)
            latency_score = 1.0 / (p.get("latency_ms", 1000.0) + 0.0001)
            capability_score = sum(
                1 for cap in required_capabilities if p.get("capabilities", {}).get(cap.value, False)
            )
            total_score = (
                weights.get("cost", 0.4) * cost_score
                + weights.get("latency", 0.3) * latency_score
                + weights.get("capability", 0.3) * capability_score
            )
            scored_providers.append((p, total_score))

        scored_providers.sort(key=lambda x: x[1], reverse=True)
        selected = scored_providers[0][0]
        model_id = self._get_best_model_for_provider(selected["provider_id"], task)
        return {
            "provider_id": selected["provider_id"],
            "model_id": model_id,
            "task": task,
            "policy": {"type": "hybrid", **policy},
        }

    def _get_provider_details(self) -> List[Dict[str, Any]]:
        """Get provider details from the hub."""
        if self._hub is not None:
            return self._hub.list_provider_details()
        return []

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

    def _get_best_model_for_provider(self, provider_id: str, task: str) -> str:
        """Get the best model for a provider and task."""
        if self._hub is not None:
            return self._hub._best_model_for_provider(provider_id, task)
        return "default"
