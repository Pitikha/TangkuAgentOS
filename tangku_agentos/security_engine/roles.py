from __future__ import annotations

from threading import RLock

from .interfaces import RoleManager
from .models import Role


class RoleManager(RoleManager):
    """Role manager architecture."""

    def __init__(self) -> None:
        self._roles: dict[str, Role] = {}
        self._assignments: dict[str, str] = {}
        self._lock = RLock()

    def create_role(self, role: Role) -> None:
        with self._lock:
            self._roles[role.role_id] = role

    def assign_role(self, identity_id: str, role_id: str) -> None:
        with self._lock:
            self._assignments[identity_id] = role_id

    def list_roles(self) -> list[Role]:
        with self._lock:
            return list(self._roles.values())

    def get_role_for_identity(self, identity_id: str) -> Role | None:
        with self._lock:
            role_id = self._assignments.get(identity_id)
            return self._roles.get(role_id) if role_id else None
