from __future__ import annotations

from .interfaces import MCPPermissionManager
from .models import MCPTool


class MCPPermissionManager(MCPPermissionManager):
    """MCP permission manager abstraction."""

    def authorize(self, tool: MCPTool, action: str) -> bool:
        return action in {"read", "execute"}
