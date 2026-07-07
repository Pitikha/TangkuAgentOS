from __future__ import annotations

from typing import Any

from .hub import ProviderHub


class SmartModelRouter:
    """Route models to providers based on task and policy."""

    def __init__(self, hub: ProviderHub) -> None:
        self._hub = hub

    def route_for_task(self, task: str, policy: dict[str, Any] | None = None) -> dict[str, Any]:
        policy = policy or {}
        providers = self._hub.list_provider_details()
        if not providers:
            return {"provider_id": None, "model_id": None}
        for rule in self._hub.list_routing_rules():
            if rule.get("task") == task and rule.get("provider"):
                return {"provider_id": rule["provider"], "model_id": self._hub._best_model_for_provider(rule["provider"], task), "task": task, "policy": policy}
        selection = self._hub.select_best_provider(task, policy)
        if selection.get("provider_id") is None:
            selection = {"provider_id": "ollama", "model_id": "llama3"}
        return {"provider_id": selection["provider_id"], "model_id": selection["model_id"], "task": task, "policy": policy}
