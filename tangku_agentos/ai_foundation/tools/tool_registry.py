"""
Tool Registry for TangkuAgentOS AI Foundation Framework.

Manages tools for AI agents to use.
"""
from typing import Any, Optional, Dict, List, Callable, Awaitable
from dataclasses import dataclass, field
import logging
from enum import Enum

logger = logging.getLogger(__name__)


class ToolType(Enum):
    """Types of tools."""
    PYTHON = "python"
    SHELL = "shell"
    DOCKER = "docker"
    API = "api"
    WEB_AUTOMATION = "web_automation"
    BROWSER_AUTOMATION = "browser_automation"
    PLUGIN = "plugin"


@dataclass
class Tool:
    """Represents a tool for AI agents."""
    name: str
    description: str
    tool_type: ToolType
    function: Callable[..., Awaitable[Any]]
    permissions: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


class ToolRegistry:
    """Manages tools for TangkuAgentOS.

    This class provides a registry for tools that AI agents can use,
    including Python functions, shell commands, APIs, and plugins.
    """

    def __init__(self):
        """Initialize the ToolRegistry."""
        self._tools: Dict[str, Tool] = {}
        logger.info("ToolRegistry initialized.")

    def register_tool(
        self,
        name: str,
        description: str,
        tool_type: ToolType,
        function: Callable[..., Awaitable[Any]],
        permissions: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Register a new tool.

        Args:
            name: The name of the tool.
            description: The description of the tool.
            tool_type: The type of the tool.
            function: The function to call when the tool is executed.
            permissions: Optional list of permissions required to use the tool.
            metadata: Optional metadata for the tool.
        """
        self._tools[name] = Tool(
            name=name,
            description=description,
            tool_type=tool_type,
            function=function,
            permissions=permissions or [],
            metadata=metadata or {},
        )
        logger.info(f"Registered tool: {name}")

    def get_tool(self, name: str) -> Optional[Tool]:
        """Retrieve a tool by name.

        Args:
            name: The name of the tool.

        Returns:
            The Tool if found, otherwise None.
        """
        return self._tools.get(name)

    def list_tools(self) -> List[str]:
        """List all registered tools.

        Returns:
            List of tool names.
        """
        return list(self._tools.keys())

    def list_tools_by_type(self, tool_type: ToolType) -> List[str]:
        """List all tools of a specific type.

        Args:
            tool_type: The type of tools to list.

        Returns:
            List of tool names of the specified type.
        """
        return [
            name for name, tool in self._tools.items()
            if tool.tool_type == tool_type
        ]

    async def execute_tool(
        self,
        name: str,
        *args: Any,
        **kwargs: Any,
    ) -> Any:
        """Execute a tool by name.

        Args:
            name: The name of the tool to execute.
            *args: Positional arguments for the tool.
            **kwargs: Keyword arguments for the tool.

        Returns:
            The result of the tool execution.

        Raises:
            ValueError: If the tool is not found.
        """
        tool = self._tools.get(name)
        if not tool:
            raise ValueError(f"Tool '{name}' not found.")
        logger.info(f"Executing tool: {name}")
        return await tool.function(*args, **kwargs)

    def unregister_tool(self, name: str) -> bool:
        """Unregister a tool.

        Args:
            name: The name of the tool to unregister.

        Returns:
            True if the tool was unregistered, False otherwise.
        """
        if name in self._tools:
            del self._tools[name]
            logger.info(f"Unregistered tool: {name}")
            return True
        return False

    def get_tool_metadata(self, name: str) -> Optional[Dict[str, Any]]:
        """Get metadata for a tool.

        Args:
            name: The name of the tool.

        Returns:
            The tool's metadata if found, otherwise None.
        """
        tool = self._tools.get(name)
        return tool.metadata if tool else None

    def update_tool_metadata(
        self,
        name: str,
        metadata: Dict[str, Any],
    ) -> bool:
        """Update metadata for a tool.

        Args:
            name: The name of the tool.
            metadata: The new metadata for the tool.

        Returns:
            True if the tool was updated, False otherwise.
        """
        tool = self._tools.get(name)
        if tool:
            tool.metadata.update(metadata)
            logger.info(f"Updated metadata for tool: {name}")
            return True
        return False
