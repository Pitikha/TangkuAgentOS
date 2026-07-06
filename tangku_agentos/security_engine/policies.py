from __future__ import annotations

from threading import RLock

from .interfaces import PolicyManager
from .models import Policy


class PolicyManager(PolicyManager):
    """Policy manager with allow/deny and conditional rule support."""

    def __init__(self) -> None:
        self._policies: dict[str, Policy] = {}
        self._lock = RLock()

    def create_policy(self, policy: Policy) -> None:
        with self._lock:
            self._policies[policy.policy_id] = policy

    def evaluate_policy(self, policy_id: str, context: dict[str, str]) -> bool:
        with self._lock:
            policy = self._policies.get(policy_id)
            if policy is None:
                return False
            rules = policy.rules
            if rules.get("deny"):
                return False
            if rules.get("allow"):
                return True
            if rules.get("condition"):
                return any(context.get(k) == v for k, v in rules["condition"].items())
            return True
