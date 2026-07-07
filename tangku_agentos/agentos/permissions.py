from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from .constants import PermissionLevel
from .exceptions import AgentPermissionError
from .types import AgentId, AgentMetadata


@dataclass(frozen=True)
class AgentPermission:
    agent_id: AgentId
    level: PermissionLevel
    resources: List[str] = field(default_factory=list)
    metadata: AgentMetadata = field(default_factory=dict)


class AgentPermissionManager:
    """Model for agent permission checks and enforcement."""

    def __init__(self) -> None:
        self._permissions: Dict[AgentId, AgentPermission] = {}

    def grant(self, permission: AgentPermission) -> None:
        self._permissions[permission.agent_id] = permission

    def revoke(self, agent_id: AgentId) -> None:
        self._permissions.pop(agent_id, None)

    def get(self, agent_id: AgentId) -> AgentPermission:
        permission = self._permissions.get(agent_id)
        if permission is None:
            raise AgentPermissionError(f"Permission not found for agent: {agent_id}")
        return permission

    def authorize(self, agent_id: AgentId, resource: str, required: PermissionLevel) -> bool:
        permission = self.get(agent_id)
        if permission.level == PermissionLevel.ADMIN:
            return True
        if permission.level == required:
            return resource in permission.resources
        return False
