from __future__ import annotations

from .interfaces import ToolConfigurationManager
from .models import ToolConfiguration


class ToolConfigurationManager(ToolConfigurationManager):
    """Store tool configurations by tool id."""

    def __init__(self) -> None:
        self._configurations: dict[str, ToolConfiguration] = {}

    def get_configuration(self, tool_id: str) -> ToolConfiguration:
        return self._configurations.get(tool_id, ToolConfiguration(tool_id=tool_id, settings={}))

    def set_configuration(self, tool_id: str, configuration: ToolConfiguration) -> None:
        self._configurations[tool_id] = configuration
