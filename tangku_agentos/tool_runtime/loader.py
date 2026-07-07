from __future__ import annotations

from .interfaces import ToolLoader
from .models import Tool, ToolConfiguration, ToolDefinition, ToolMetadata, ToolStatus


class ToolLoader(ToolLoader):
    """Load a tool from a simple definition string."""

    def load(self, tool_definition: str) -> Tool:
        metadata = ToolMetadata(tool_id=tool_definition, name=tool_definition)
        definition = ToolDefinition(tool_id=tool_definition, metadata=metadata)
        return Tool(tool_id=tool_definition, definition=definition, metadata=metadata, status=ToolStatus.AVAILABLE, configuration=ToolConfiguration(tool_id=tool_definition, settings={}))
