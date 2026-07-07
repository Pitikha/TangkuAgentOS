from __future__ import annotations

from threading import RLock

from .models import Permission, Policy, Role


class SecurityRegistry:
    """Security registry architecture."""

    def __init__(self) -> None:
        self._policies: dict[str, Policy] = {}
        self._roles: dict[str, Role] = {}
        self._permissions: dict[str, Permission] = {}
        self._lock = RLock()

    def register_policy(self, policy: Policy) -> None:
        with self._lock:
            self._policies[policy.policy_id] = policy

    def get_policy(self, policy_id: str) -> Policy:
        with self._lock:
            return self._policies[policy_id]

    def register_role(self, role: Role) -> None:
        with self._lock:
            self._roles[role.role_id] = role

    def get_role(self, role_id: str) -> Role:
        with self._lock:
            return self._roles[role_id]

    def register_permission(self, permission: Permission) -> None:
        with self._lock:
            self._permissions[permission.permission_id] = permission

    def get_permission(self, permission_id: str) -> Permission:
        with self._lock:
            return self._permissions[permission_id]
