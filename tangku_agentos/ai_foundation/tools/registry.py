"""
AI Foundation Framework - Tool Registry

This module provides the ToolRegistry class for managing AI tools.
"""

from __future__ import annotations

import asyncio
import hashlib
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from typing import Any, Callable, Dict, List, Optional, Set, TYPE_CHECKING

if TYPE_CHECKING:
    from tangku_agentos.ai_foundation.core.config import AIConfig
    from tangku_agentos.ai_foundation.core.foundation import AIFoundation

logger = logging.getLogger(__name__)


class ToolStatus(Enum):
    """Status of a tool."""
    AVAILABLE = auto()
    UNAVAILABLE = auto()
    DISABLED = auto()
    ERROR = auto()


class ToolType(Enum):
    """Type of a tool."""
    FUNCTION = auto()
    SCRIPT = auto()
    COMMAND = auto()
    API = auto()
    WEBHOOK = auto()
    PLUGIN = auto()
    CUSTOM = auto()


@dataclass
class Tool:
    """
    Represents an AI tool.
    
    Attributes:
        tool_id: Unique identifier for the tool.
        name: Human-readable name for the tool.
        description: Description of what the tool does.
        tool_type: Type of the tool.
        function: Function to call (for function tools).
        command: Command to execute (for command tools).
        url: URL for API tools.
        parameters: Parameter schema for the tool.
        permissions: Required permissions to use the tool.
        tags: Tags for categorizing the tool.
        status: Current status of the tool.
        timeout: Timeout for tool execution in seconds.
        max_retries: Maximum number of retries for tool execution.
        created_at: When the tool was registered.
        updated_at: When the tool was last updated.
        metadata: Additional metadata.
    """

    tool_id: str
    name: str
    description: str = ""
    tool_type: ToolType = ToolType.CUSTOM
    function: Optional[Callable] = None
    command: Optional[str] = None
    url: Optional[str] = None
    parameters: Dict[str, Any] = field(default_factory=dict)
    permissions: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    status: ToolStatus = ToolStatus.AVAILABLE
    timeout: float = 30.0
    max_retries: int = 3
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Post-initialization processing."""
        if not self.tool_id:
            self.tool_id = self._generate_id()

    def _generate_id(self) -> str:
        """Generate a unique tool ID."""
        unique_str = f"{self.name}:{self.description[:50]}"
        return f"tool_{hashlib.sha256(unique_str.encode()).hexdigest()[:16]}"

    @property
    def is_available(self) -> bool:
        """Check if the tool is available."""
        return self.status == ToolStatus.AVAILABLE

    @property
    def is_function(self) -> bool:
        """Check if this is a function tool."""
        return self.tool_type == ToolType.FUNCTION and self.function is not None

    @property
    def is_command(self) -> bool:
        """Check if this is a command tool."""
        return self.tool_type == ToolType.COMMAND and self.command is not None

    @property
    def is_api(self) -> bool:
        """Check if this is an API tool."""
        return self.tool_type == ToolType.API and self.url is not None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "tool_id": self.tool_id,
            "name": self.name,
            "description": self.description,
            "tool_type": self.tool_type.value,
            "parameters": self.parameters,
            "permissions": self.permissions,
            "tags": self.tags,
            "status": self.status.value,
            "timeout": self.timeout,
            "max_retries": self.max_retries,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Tool":
        """Create from dictionary."""
        tool_type = ToolType.CUSTOM
        if "tool_type" in data and data["tool_type"]:
            try:
                tool_type = ToolType(data["tool_type"])
            except ValueError:
                pass

        status = ToolStatus.AVAILABLE
        if "status" in data and data["status"]:
            try:
                status = ToolStatus(data["status"])
            except ValueError:
                pass

        return cls(
            tool_id=data.get("tool_id", ""),
            name=data.get("name", ""),
            description=data.get("description", ""),
            tool_type=tool_type,
            parameters=data.get("parameters", {}),
            permissions=data.get("permissions", []),
            tags=data.get("tags", []),
            status=status,
            timeout=data.get("timeout", 30.0),
            max_retries=data.get("max_retries", 3),
            metadata=data.get("metadata", {}),
        )

    def __repr__(self) -> str:
        """Return string representation."""
        return (
            f"Tool("
            f"id={self.tool_id}, "
            f"name={self.name}, "
            f"type={self.tool_type.value}, "
            f"status={self.status.value})"
        )


@dataclass
class ToolRegistryMetrics:
    """Metrics for the tool registry."""
    tools_registered: int = 0
    tools_available: int = 0
    tools_used: int = 0
    executions: int = 0
    errors: int = 0
    last_error: Optional[str] = None
    last_error_time: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "tools_registered": self.tools_registered,
            "tools_available": self.tools_available,
            "tools_used": self.tools_used,
            "executions": self.executions,
            "errors": self.errors,
            "last_error": self.last_error,
            "last_error_time": self.last_error_time.isoformat() if self.last_error_time else None,
        }


class ToolRegistry:
    """
    Registry for managing AI tools.
    
    This class provides a centralized way to register, manage, and discover
    AI tools. It supports tool discovery, permissions, and execution.
    
    Thread Safety:
        This class is thread-safe for concurrent access.
    
    Example:
        >>> from tangku_agentos.ai_foundation import ToolRegistry
        >>> 
        >>> # Create registry
        >>> registry = ToolRegistry()
        >>> 
        >>> # Register a function tool
        >>> def greet(name: str) -> str:
        ...     return f"Hello, {name}!"
        >>> 
        >>> await registry.register_function(
        ...     name="greet",
        ...     description="Greet someone by name",
        ...     function=greet,
        ...     parameters={"name": {"type": "string", "required": True}}
        ... )
        >>> 
        >>> # List tools
        >>> tools = registry.list_tools()
        >>> 
        >>> # Get a tool
        >>> tool = registry.get_tool("greet")
    """

    def __init__(self, config: "AIConfig", foundation: "AIFoundation"):
        """
        Initialize the tool registry.
        
        Args:
            config: AI Foundation configuration.
            foundation: AI Foundation instance.
        """
        self._config = config
        self._foundation = foundation
        self._tools: Dict[str, Tool] = {}
        self._name_index: Dict[str, str] = {}  # name -> tool_id
        self._tag_index: Dict[str, Set[str]] = {}  # tag -> set of tool_ids
        self._permission_index: Dict[str, Set[str]] = {}  # permission -> set of tool_ids
        self._metrics = ToolRegistryMetrics()
        self._lock = asyncio.Lock()
        self._initialized = False
        self._started = False
        
        logger.info("ToolRegistry initialized")

    @property
    def config(self) -> "AIConfig":
        """Get the configuration."""
        return self._config

    @property
    def foundation(self) -> "AIFoundation":
        """Get the AI Foundation instance."""
        return self._foundation

    @property
    def metrics(self) -> ToolRegistryMetrics:
        """Get the tool registry metrics."""
        return self._metrics

    @property
    def is_initialized(self) -> bool:
        """Check if the registry is initialized."""
        return self._initialized

    @property
    def is_started(self) -> bool:
        """Check if the registry is started."""
        return self._started

    async def initialize(self) -> None:
        """
        Initialize the tool registry.
        """
        if self._initialized:
            logger.warning("ToolRegistry already initialized")
            return
        
        logger.info("Initializing ToolRegistry...")
        
        # Load default tools
        await self._load_default_tools()
        
        self._initialized = True
        logger.info("ToolRegistry initialized successfully")

    async def start(self) -> None:
        """
        Start the tool registry.
        """
        if self._started:
            logger.warning("ToolRegistry already started")
            return
        
        if not self._initialized:
            await self.initialize()
        
        logger.info("Starting ToolRegistry...")
        
        self._started = True
        logger.info("ToolRegistry started successfully")

    async def stop(self) -> None:
        """
        Stop the tool registry.
        """
        if not self._started:
            logger.warning("ToolRegistry not started")
            return
        
        logger.info("Stopping ToolRegistry...")
        
        self._started = False
        logger.info("ToolRegistry stopped successfully")

    async def _load_default_tools(self) -> None:
        """Load default tools."""
        # In a real implementation, this would load built-in tools
        # For now, just log
        logger.debug("Loading default tools...")

    async def register(self, tool: Tool) -> str:
        """
        Register a tool.
        
        Args:
            tool: Tool to register.
        
        Returns:
            Tool ID.
        
        Raises:
            ValueError: If tool with same ID or name already exists.
        """
        async with self._lock:
            # Check if tool with same ID already exists
            if tool.tool_id in self._tools:
                raise ValueError(f"Tool with ID {tool.tool_id} already exists")
            
            # Check if tool with same name already exists
            if tool.name in self._name_index:
                raise ValueError(f"Tool with name {tool.name} already exists")
            
            # Register tool
            self._tools[tool.tool_id] = tool
            self._name_index[tool.name] = tool.tool_id
            
            # Index by tags
            for tag in tool.tags:
                if tag not in self._tag_index:
                    self._tag_index[tag] = set()
                self._tag_index[tag].add(tool.tool_id)
            
            # Index by permissions
            for permission in tool.permissions:
                if permission not in self._permission_index:
                    self._permission_index[permission] = set()
                self._permission_index[permission].add(tool.tool_id)
            
            self._metrics.tools_registered += 1
            if tool.is_available:
                self._metrics.tools_available += 1
            
            logger.debug(f"Tool registered: {tool.tool_id}")
            return tool.tool_id

    async def register_function(
        self,
        name: str,
        description: str = "",
        function: Optional[Callable] = None,
        parameters: Optional[Dict[str, Any]] = None,
        permissions: Optional[List[str]] = None,
        tags: Optional[List[str]] = None,
        timeout: float = 30.0,
        max_retries: int = 3,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Register a function tool.
        
        Args:
            name: Name of the tool.
            description: Description of what the tool does.
            function: Function to call.
            parameters: Parameter schema for the tool.
            permissions: Required permissions to use the tool.
            tags: Tags for categorizing the tool.
            timeout: Timeout for tool execution in seconds.
            max_retries: Maximum number of retries for tool execution.
            metadata: Additional metadata.
        
        Returns:
            Tool ID.
        """
        tool = Tool(
            tool_id="",
            name=name,
            description=description,
            tool_type=ToolType.FUNCTION,
            function=function,
            parameters=parameters or {},
            permissions=permissions or [],
            tags=tags or [],
            timeout=timeout,
            max_retries=max_retries,
            metadata=metadata or {},
        )
        
        return await self.register(tool)

    async def register_command(
        self,
        name: str,
        description: str = "",
        command: str = "",
        parameters: Optional[Dict[str, Any]] = None,
        permissions: Optional[List[str]] = None,
        tags: Optional[List[str]] = None,
        timeout: float = 30.0,
        max_retries: int = 3,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Register a command tool.
        
        Args:
            name: Name of the tool.
            description: Description of what the tool does.
            command: Command to execute.
            parameters: Parameter schema for the tool.
            permissions: Required permissions to use the tool.
            tags: Tags for categorizing the tool.
            timeout: Timeout for tool execution in seconds.
            max_retries: Maximum number of retries for tool execution.
            metadata: Additional metadata.
        
        Returns:
            Tool ID.
        """
        tool = Tool(
            tool_id="",
            name=name,
            description=description,
            tool_type=ToolType.COMMAND,
            command=command,
            parameters=parameters or {},
            permissions=permissions or [],
            tags=tags or [],
            timeout=timeout,
            max_retries=max_retries,
            metadata=metadata or {},
        )
        
        return await self.register(tool)

    async def register_api(
        self,
        name: str,
        description: str = "",
        url: str = "",
        parameters: Optional[Dict[str, Any]] = None,
        permissions: Optional[List[str]] = None,
        tags: Optional[List[str]] = None,
        timeout: float = 30.0,
        max_retries: int = 3,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Register an API tool.
        
        Args:
            name: Name of the tool.
            description: Description of what the tool does.
            url: URL for the API.
            parameters: Parameter schema for the tool.
            permissions: Required permissions to use the tool.
            tags: Tags for categorizing the tool.
            timeout: Timeout for tool execution in seconds.
            max_retries: Maximum number of retries for tool execution.
            metadata: Additional metadata.
        
        Returns:
            Tool ID.
        """
        tool = Tool(
            tool_id="",
            name=name,
            description=description,
            tool_type=ToolType.API,
            url=url,
            parameters=parameters or {},
            permissions=permissions or [],
            tags=tags or [],
            timeout=timeout,
            max_retries=max_retries,
            metadata=metadata or {},
        )
        
        return await self.register(tool)

    async def unregister(self, tool_id: str) -> bool:
        """
        Unregister a tool.
        
        Args:
            tool_id: ID of the tool to unregister.
        
        Returns:
            True if tool was unregistered, False if not found.
        """
        async with self._lock:
            if tool_id not in self._tools:
                return False
            
            tool = self._tools[tool_id]
            
            # Remove from name index
            if tool.name in self._name_index:
                del self._name_index[tool.name]
            
            # Remove from tag index
            for tag in tool.tags:
                if tag in self._tag_index:
                    self._tag_index[tag].discard(tool_id)
                    if not self._tag_index[tag]:
                        del self._tag_index[tag]
            
            # Remove from permission index
            for permission in tool.permissions:
                if permission in self._permission_index:
                    self._permission_index[permission].discard(tool_id)
                    if not self._permission_index[permission]:
                        del self._permission_index[permission]
            
            # Remove from tools
            del self._tools[tool_id]
            
            self._metrics.tools_registered -= 1
            if tool.is_available:
                self._metrics.tools_available -= 1
            
            logger.debug(f"Tool unregistered: {tool_id}")
            return True

    async def get_tool(self, tool_id: str) -> Optional[Tool]:
        """
        Get a tool by ID.
        
        Args:
            tool_id: ID of the tool to get.
        
        Returns:
            Tool or None if not found.
        """
        return self._tools.get(tool_id)

    async def get_tool_by_name(self, name: str) -> Optional[Tool]:
        """
        Get a tool by name.
        
        Args:
            name: Name of the tool to get.
        
        Returns:
            Tool or None if not found.
        """
        tool_id = self._name_index.get(name)
        if tool_id:
            return self._tools.get(tool_id)
        return None

    async def list_tools(
        self,
        tags: Optional[List[str]] = None,
        permissions: Optional[List[str]] = None,
        tool_type: Optional[ToolType] = None,
        status: Optional[ToolStatus] = None,
    ) -> List[Tool]:
        """
        List all tools, optionally filtered.
        
        Args:
            tags: Optional list of tags to filter by.
            permissions: Optional list of permissions to filter by.
            tool_type: Optional tool type to filter by.
            status: Optional tool status to filter by.
        
        Returns:
            List of Tool instances.
        """
        tools = []
        
        for tool in self._tools.values():
            # Filter by tags
            if tags:
                if not any(tag in tool.tags for tag in tags):
                    continue
            
            # Filter by permissions
            if permissions:
                if not any(perm in tool.permissions for perm in permissions):
                    continue
            
            # Filter by tool type
            if tool_type and tool.tool_type != tool_type:
                continue
            
            # Filter by status
            if status and tool.status != status:
                continue
            
            tools.append(tool)
        
        return tools

    async def get_tools_by_tag(self, tag: str) -> List[Tool]:
        """
        Get tools by tag.
        
        Args:
            tag: Tag to filter by.
        
        Returns:
            List of Tool instances.
        """
        tool_ids = self._tag_index.get(tag, set())
        return [self._tools[tid] for tid in tool_ids if tid in self._tools]

    async def get_tools_by_permission(self, permission: str) -> List[Tool]:
        """
        Get tools by required permission.
        
        Args:
            permission: Permission to filter by.
        
        Returns:
            List of Tool instances.
        """
        tool_ids = self._permission_index.get(permission, set())
        return [self._tools[tid] for tid in tool_ids if tid in self._tools]

    async def discover_tools(self, query: str, limit: int = 10) -> List[Tool]:
        """
        Discover tools matching a query.
        
        Args:
            query: Search query.
            limit: Maximum number of results to return.
        
        Returns:
            List of Tool instances.
        """
        # In a real implementation, this would use semantic search
        # For now, return all tools limited by the query
        all_tools = await self.list_tools()
        
        # Filter by query in name or description
        query_lower = query.lower()
        matched_tools = [
            tool for tool in all_tools
            if query_lower in tool.name.lower() or query_lower in tool.description.lower()
        ]
        
        return matched_tools[:limit]

    async def check_permission(self, tool_id: str, user_permissions: List[str]) -> bool:
        """
        Check if a user has permission to use a tool.
        
        Args:
            tool_id: ID of the tool.
            user_permissions: List of permissions the user has.
        
        Returns:
            True if user has permission, False otherwise.
        """
        tool = self._tools.get(tool_id)
        if not tool:
            return False
        
        # If tool has no permissions, it's public
        if not tool.permissions:
            return True
        
        # Check if user has any of the required permissions
        return any(perm in user_permissions for perm in tool.permissions)

    async def get_info(self) -> Dict[str, Any]:
        """
        Get information about the tool registry.
        
        Returns:
            Dictionary with tool registry information.
        """
        return {
            "tools": len(self._tools),
            "available_tools": self._metrics.tools_available,
            "tags": list(self._tag_index.keys()),
            "permissions": list(self._permission_index.keys()),
            "metrics": self._metrics.to_dict(),
        }

    async def reset(self) -> None:
        """
        Reset the tool registry.
        
        This method clears all tools and resets all state.
        """
        logger.info("Resetting ToolRegistry...")
        
        async with self._lock:
            self._tools.clear()
            self._name_index.clear()
            self._tag_index.clear()
            self._permission_index.clear()
            self._metrics = ToolRegistryMetrics()
            self._initialized = False
            self._started = False
        
        logger.info("ToolRegistry reset successfully")

    def __repr__(self) -> str:
        """Return string representation."""
        return (
            f"ToolRegistry("
            f"tools={len(self._tools)}, "
            f"available={self._metrics.tools_available})"
        )
