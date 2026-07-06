from __future__ import annotations

from .interfaces import MCPConfigurationManager


class MCPConfigurationManager(MCPConfigurationManager):
    """MCP configuration manager abstraction."""

    def __init__(self) -> None:
        self._configurations: dict[str, dict[str, str]] = {}

    def get_configuration(self, server_id: str) -> dict[str, str]:
        return dict(self._configurations.get(server_id, {}))

    def set_configuration(self, server_id: str, configuration: dict[str, str]) -> None:
        self._configurations[server_id] = dict(configuration)
