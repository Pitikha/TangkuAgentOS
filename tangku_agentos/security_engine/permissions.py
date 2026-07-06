from __future__ import annotations

from threading import RLock

from .interfaces import PermissionManager
from .models import Permission


class PermissionManager(PermissionManager):
    """Permission manager architecture with extensible resource support."""

    def __init__(self) -> None:
        self._permissions: dict[str, dict[str, Permission]] = {}
        self._lock = RLock()

    def grant(self, role_id: str, permission: Permission) -> None:
        with self._lock:
            self._permissions.setdefault(role_id, {})[permission.permission_id] = permission

    def revoke(self, role_id: str, permission_id: str) -> None:
        with self._lock:
            self._permissions.get(role_id, {}).pop(permission_id, None)

    def list_permissions(self, role_id: str) -> list[Permission]:
        with self._lock:
            return list(self._permissions.get(role_id, {}).values())

    def has_permission(self, role_id: str, permission_id: str) -> bool:
        with self._lock:
            return permission_id in self._permissions.get(role_id, {})
