from __future__ import annotations

from typing import Any

from .interfaces import AuthorizationManager
from .models import Permission


class AuthorizationManager(AuthorizationManager):
    """Authorization manager architecture."""

    def __init__(self) -> None:
        self._rules: dict[str, list[Permission]] = {}

    def authorize(self, identity_id: str, permission: Permission) -> bool:
        return any(p.permission_id == permission.permission_id for p in self._rules.get(identity_id, []))

    def register_rule(self, identity_id: str, permission: Permission) -> None:
        self._rules.setdefault(identity_id, []).append(permission)
