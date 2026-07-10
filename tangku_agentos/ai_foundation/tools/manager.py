"""
AI Foundation Framework - Tool Manager

This module provides the ToolManager class for managing AI tools.
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Set, TYPE_CHECKING

if TYPE_CHECKING:
    from tangku_agentos.ai_foundation.tools.registry import ToolRegistry, Tool
    from tangku_agentos.ai_foundation.core.config import AIConfig
    from tangku_agentos.ai_foundation.core.foundation import AIFoundation

logger = logging.getLogger(__name__)


@dataclass
class ToolExecutionResult:
    """
    Result from a tool execution.
    
    Attributes:
        tool_id: ID of the tool that was executed.
        success: Whether the execution was successful.
        result: Result of the execution.
        error: Error message if execution failed.
        duration: Duration of the execution in seconds.
        timestamp: When the execution was performed.
        metadata: Additional metadata.
    """

    tool_id: str
    success: bool = False
    result: Any = None
    error: Optional[str] = None
    duration: float = 0.0
    timestamp: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "tool_id": self.tool_id,
            "success": self.success,
            "result": self.result,
            "error": self.error,
            "duration": self.duration,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata,
        }


@dataclass
class ToolManagerMetrics:
    """Metrics for the tool manager."""
    executions: int = 0
    successful_executions: int = 0
    failed_executions: int = 0
    tools_used: Dict[str, int] = field(default_factory=dict)
    total_duration: float = 0.0
    errors: int = 0
    last_error: Optional[str] = None
    last_error_time: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "executions": self.executions,
            "successful_executions": self.successful_executions,
            "failed_executions": self.failed_executions,
            "tools_used": self.tools_used.copy(),
            "total_duration": self.total_duration,
            "errors": self.errors,
            "last_error": self.last_error,
            "last_error_time": self.last_error_time.isoformat() if self.last_error_time else None,
        }


class ToolManager:
    """
    Manager for AI tools.
    
    This class provides a high-level interface for managing and executing
    AI tools. It integrates with the ToolRegistry and provides additional
    functionality like tool execution, permissions, and monitoring.
    
    Thread Safety:
        This class is thread-safe for concurrent access.
    
    Example:
        >>> from tangku_agentos.ai_foundation import ToolManager
        >>> 
        >>> # Create manager
        >>> manager = ToolManager()
        >>> 
        >>> # Execute a tool
        >>> result = await manager.execute("greet", {"name": "Alice"})
        >>> 
        >>> # List available tools
        >>> tools = await manager.list_tools()
        >>> 
        >>> # Check permissions
        >>> has_permission = await manager.check_permission("greet", ["user"])
    """

    def __init__(self, config: "AIConfig", foundation: "AIFoundation"):
        """
        Initialize the tool manager.
        
        Args:
            config: AI Foundation configuration.
            foundation: AI Foundation instance.
        """
        self._config = config
        self._foundation = foundation
        self._registry: Optional["ToolRegistry"] = None
        self._metrics = ToolManagerMetrics()
        self._lock = asyncio.Lock()
        self._initialized = False
        self._started = False
        
        logger.info("ToolManager initialized")

    @property
    def config(self) -> "AIConfig":
        """Get the configuration."""
        return self._config

    @property
    def foundation(self) -> "AIFoundation":
        """Get the AI Foundation instance."""
        return self._foundation

    @property
    def registry(self) -> "ToolRegistry":
        """Get the tool registry."""
        if self._registry is None:
            from tangku_agentos.ai_foundation.tools.registry import ToolRegistry
            self._registry = ToolRegistry(self._config, self._foundation)
        return self._registry

    @property
    def metrics(self) -> ToolManagerMetrics:
        """Get the tool manager metrics."""
        return self._metrics

    @property
    def is_initialized(self) -> bool:
        """Check if the manager is initialized."""
        return self._initialized

    @property
    def is_started(self) -> bool:
        """Check if the manager is started."""
        return self._started

    async def initialize(self) -> None:
        """
        Initialize the tool manager.
        """
        if self._initialized:
            logger.warning("ToolManager already initialized")
            return
        
        logger.info("Initializing ToolManager...")
        
        await self.registry.initialize()
        
        self._initialized = True
        logger.info("ToolManager initialized successfully")

    async def start(self) -> None:
        """
        Start the tool manager.
        """
        if self._started:
            logger.warning("ToolManager already started")
            return
        
        if not self._initialized:
            await self.initialize()
        
        logger.info("Starting ToolManager...")
        
        await self.registry.start()
        
        self._started = True
        logger.info("ToolManager started successfully")

    async def stop(self) -> None:
        """
        Stop the tool manager.
        """
        if not self._started:
            logger.warning("ToolManager not started")
            return
        
        logger.info("Stopping ToolManager...")
        
        await self.registry.stop()
        
        self._started = False
        logger.info("ToolManager stopped successfully")

    async def execute(
        self,
        tool_name: str,
        arguments: Dict[str, Any],
        session_id: Optional[str] = None,
        user_permissions: Optional[List[str]] = None,
        timeout: Optional[float] = None,
        max_retries: Optional[int] = None,
    ) -> ToolExecutionResult:
        """
        Execute a tool.
        
        Args:
            tool_name: Name or ID of the tool to execute.
            arguments: Arguments for the tool.
            session_id: Optional session ID for context.
            user_permissions: Optional list of user permissions.
            timeout: Optional timeout for execution.
            max_retries: Optional maximum number of retries.
        
        Returns:
            ToolExecutionResult with the execution result.
        
        Raises:
            ValueError: If tool not found or permission denied.
        """
        import time
        
        async with self._lock:
            start_time = time.time()
            
            self._metrics.executions += 1
            
            try:
                # Get the tool
                tool = await self.registry.get_tool_by_name(tool_name)
                if not tool:
                    tool = await self.registry.get_tool(tool_name)
                
                if not tool:
                    raise ValueError(f"Tool not found: {tool_name}")
                
                # Check permissions
                if user_permissions and not await self.registry.check_permission(tool.tool_id, user_permissions):
                    raise ValueError(f"Permission denied for tool: {tool_name}")
                
                # Use tool-specific timeout and retries if not provided
                actual_timeout = timeout or tool.timeout
                actual_retries = max_retries or tool.max_retries
                
                # Execute the tool based on its type
                result = await self._execute_tool(tool, arguments, session_id, actual_timeout, actual_retries)
                
                # Update metrics
                self._metrics.successful_executions += 1
                self._metrics.tools_used[tool.tool_id] = self._metrics.tools_used.get(tool.tool_id, 0) + 1
                duration = time.time() - start_time
                self._metrics.total_duration += duration
                
                return ToolExecutionResult(
                    tool_id=tool.tool_id,
                    success=True,
                    result=result,
                    duration=duration,
                    metadata={"tool_name": tool.name, "tool_type": tool.tool_type.value},
                )
                
            except Exception as e:
                self._metrics.failed_executions += 1
                self._metrics.errors += 1
                self._metrics.last_error = str(e)
                self._metrics.last_error_time = datetime.utcnow()
                
                duration = time.time() - start_time
                
                return ToolExecutionResult(
                    tool_id=tool.tool_id if 'tool' in locals() else tool_name,
                    success=False,
                    error=str(e),
                    duration=duration,
                )

    async def _execute_tool(
        self,
        tool: "Tool",
        arguments: Dict[str, Any],
        session_id: Optional[str],
        timeout: float,
        max_retries: int,
    ) -> Any:
        """
        Execute a tool based on its type.
        
        Args:
            tool: Tool to execute.
            arguments: Arguments for the tool.
            session_id: Optional session ID for context.
            timeout: Timeout for execution.
            max_retries: Maximum number of retries.
        
        Returns:
            Result of the tool execution.
        """
        # Execute based on tool type
        if tool.is_function:
            return await self._execute_function_tool(tool, arguments, timeout, max_retries)
        elif tool.is_command:
            return await self._execute_command_tool(tool, arguments, timeout, max_retries)
        elif tool.is_api:
            return await self._execute_api_tool(tool, arguments, timeout, max_retries)
        else:
            # For other tool types, try to execute as function
            return await self._execute_function_tool(tool, arguments, timeout, max_retries)

    async def _execute_function_tool(
        self,
        tool: "Tool",
        arguments: Dict[str, Any],
        timeout: float,
        max_retries: int,
    ) -> Any:
        """
        Execute a function tool.
        
        Args:
            tool: Function tool to execute.
            arguments: Arguments for the function.
            timeout: Timeout for execution.
            max_retries: Maximum number of retries.
        
        Returns:
            Result of the function execution.
        """
        if not tool.function:
            raise ValueError(f"Tool {tool.name} has no function")
        
        # Execute the function
        try:
            # Call the function with arguments
            return tool.function(**arguments)
        except Exception as e:
            # Retry if configured
            for attempt in range(max_retries):
                try:
                    return tool.function(**arguments)
                except Exception:
                    if attempt == max_retries - 1:
                        raise
            raise

    async def _execute_command_tool(
        self,
        tool: "Tool",
        arguments: Dict[str, Any],
        timeout: float,
        max_retries: int,
    ) -> Any:
        """
        Execute a command tool.
        
        Args:
            tool: Command tool to execute.
            arguments: Arguments for the command.
            timeout: Timeout for execution.
            max_retries: Maximum number of retries.
        
        Returns:
            Result of the command execution.
        """
        if not tool.command:
            raise ValueError(f"Tool {tool.name} has no command")
        
        # In a real implementation, this would execute the command
        # For now, return a mock result
        return {
            "command": tool.command,
            "arguments": arguments,
            "status": "success",
            "output": f"Command {tool.command} executed successfully",
        }

    async def _execute_api_tool(
        self,
        tool: "Tool",
        arguments: Dict[str, Any],
        timeout: float,
        max_retries: int,
    ) -> Any:
        """
        Execute an API tool.
        
        Args:
            tool: API tool to execute.
            arguments: Arguments for the API.
            timeout: Timeout for execution.
            max_retries: Maximum number of retries.
        
        Returns:
            Result of the API execution.
        """
        if not tool.url:
            raise ValueError(f"Tool {tool.name} has no URL")
        
        # In a real implementation, this would call the API
        # For now, return a mock result
        return {
            "url": tool.url,
            "arguments": arguments,
            "status": "success",
            "response": f"API {tool.url} called successfully",
        }

    async def list_tools(
        self,
        tags: Optional[List[str]] = None,
        permissions: Optional[List[str]] = None,
        tool_type: Optional[str] = None,
        status: Optional[str] = None,
    ) -> List["Tool"]:
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
        from tangku_agentos.ai_foundation.tools.registry import ToolType, ToolStatus
        
        tool_type_enum = None
        if tool_type:
            try:
                tool_type_enum = ToolType[tool_type.upper()]
            except (KeyError, ValueError):
                pass
        
        status_enum = None
        if status:
            try:
                status_enum = ToolStatus[status.upper()]
            except (KeyError, ValueError):
                pass
        
        return await self.registry.list_tools(
            tags=tags,
            permissions=permissions,
            tool_type=tool_type_enum,
            status=status_enum,
        )

    async def get_tool(self, tool_id: str) -> Optional["Tool"]:
        """
        Get a tool by ID.
        
        Args:
            tool_id: ID of the tool to get.
        
        Returns:
            Tool or None if not found.
        """
        return await self.registry.get_tool(tool_id)

    async def get_tool_by_name(self, name: str) -> Optional["Tool"]:
        """
        Get a tool by name.
        
        Args:
            name: Name of the tool to get.
        
        Returns:
            Tool or None if not found.
        """
        return await self.registry.get_tool_by_name(name)

    async def register_tool(self, tool: "Tool") -> str:
        """
        Register a tool.
        
        Args:
            tool: Tool to register.
        
        Returns:
            Tool ID.
        """
        return await self.registry.register(tool)

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
        return await self.registry.register_function(
            name=name,
            description=description,
            function=function,
            parameters=parameters,
            permissions=permissions,
            tags=tags,
            timeout=timeout,
            max_retries=max_retries,
            metadata=metadata,
        )

    async def unregister_tool(self, tool_id: str) -> bool:
        """
        Unregister a tool.
        
        Args:
            tool_id: ID of the tool to unregister.
        
        Returns:
            True if tool was unregistered, False if not found.
        """
        return await self.registry.unregister(tool_id)

    async def check_permission(self, tool_id: str, user_permissions: List[str]) -> bool:
        """
        Check if a user has permission to use a tool.
        
        Args:
            tool_id: ID of the tool.
            user_permissions: List of permissions the user has.
        
        Returns:
            True if user has permission, False otherwise.
        """
        return await self.registry.check_permission(tool_id, user_permissions)

    async def discover_tools(self, query: str, limit: int = 10) -> List["Tool"]:
        """
        Discover tools matching a query.
        
        Args:
            query: Search query.
            limit: Maximum number of results to return.
        
        Returns:
            List of Tool instances.
        """
        return await self.registry.discover_tools(query, limit)

    async def get_info(self) -> Dict[str, Any]:
        """
        Get information about the tool manager.
        
        Returns:
            Dictionary with tool manager information.
        """
        return {
            "tools": len(self.registry._tools) if self._registry else 0,
            "registry": await self.registry.get_info() if self._registry else {},
            "metrics": self._metrics.to_dict(),
        }

    async def reset(self) -> None:
        """
        Reset the tool manager.
        
        This method clears all state and metrics.
        """
        logger.info("Resetting ToolManager...")
        
        await self.registry.reset()
        self._metrics = ToolManagerMetrics()
        self._initialized = False
        self._started = False
        
        logger.info("ToolManager reset successfully")

    def __repr__(self) -> str:
        """Return string representation."""
        return (
            f"ToolManager("
            f"tools={len(self.registry._tools) if self._registry else 0}, "
            f"executions={self._metrics.executions})"
        )
