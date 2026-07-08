"""
Runtime Communication Framework - Runtime Integration Template

This module provides a template for integrating existing TangkuAgentOS runtimes
with the Runtime Communication Framework.

To integrate an existing runtime:
1. Make it inherit from BaseRuntime (or use the mixin approach)
2. Implement the required methods
3. Replace direct communication with bus-based communication
4. Use standard events, commands, and queries

Example usage:
    from tangku_agentos.runtime_communication.integration.runtime_template import (
        IntegratedRuntime,
        RuntimeIntegrationMixin,
    )
    
    # Option 1: Inherit from IntegratedRuntime
    class MyRuntime(IntegratedRuntime):
        pass
    
    # Option 2: Use mixin
    class MyRuntime(RuntimeIntegrationMixin):
        pass
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any, Dict, List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from tangku_agentos.runtime_communication.integration.base import (
        BaseRuntime,
        RuntimeConfig,
        RuntimeCapabilities,
    )
    from tangku_agentos.runtime_communication.models.messages import (
        Message,
        Command,
        Query,
        Event,
    )

logger = logging.getLogger(__name__)


class RuntimeIntegrationMixin:
    """
    Mixin class that provides integration with the Runtime Communication Framework.

    This mixin can be added to existing runtime classes to provide
    communication capabilities without requiring inheritance from BaseRuntime.

    Example:
        >>> class MyExistingRuntime:
        ...     # Existing runtime code
        ...     pass
        >>> 
        >>> class IntegratedRuntime(RuntimeIntegrationMixin, MyExistingRuntime):
        ...     pass
        >>> 
        >>> runtime = IntegratedRuntime()
        >>> await runtime.initialize_communication()
        >>> await runtime.send_command("other_runtime", "DoSomething", {})
    """

    def __init__(self, runtime_id: str = "", name: str = "", version: str = "1.0.0"):
        """
        Initialize the integration mixin.

        Args:
            runtime_id: Unique ID for the runtime.
            name: Human-readable name.
            version: Runtime version.
        """
        self._runtime_id = runtime_id
        self._name = name
        self._version = version
        self._communication_initialized = False

        # Communication buses (will be set during initialization)
        self._message_bus = None
        self._event_bus = None
        self._command_bus = None
        self._query_bus = None
        self._broadcast_bus = None
        self._request_response_bus = None

        # Services
        self._registry = None
        self._health_service = None
        self._context_manager = None

    async def initialize_communication(
        self,
        message_bus: Any = None,
        event_bus: Any = None,
        command_bus: Any = None,
        query_bus: Any = None,
        broadcast_bus: Any = None,
        request_response_bus: Any = None,
        registry: Any = None,
        health_service: Any = None,
        context_manager: Any = None,
    ) -> None:
        """
        Initialize communication with the Runtime Communication Framework.

        Args:
            message_bus: Message bus instance.
            event_bus: Event bus instance.
            command_bus: Command bus instance.
            query_bus: Query bus instance.
            broadcast_bus: Broadcast bus instance.
            request_response_bus: Request/response bus instance.
            registry: Runtime registry instance.
            health_service: Health service instance.
            context_manager: Context manager instance.
        """
        if self._communication_initialized:
            return

        # Import here to avoid circular imports
        from tangku_agentos.runtime_communication import (
            MessageBus,
            EventBus,
            CommandBus,
            QueryBus,
            BroadcastBus,
            RequestResponseBus,
            RuntimeRegistry,
            RuntimeHealthService,
            RuntimeContextManager,
        )

        # Set buses
        self._message_bus = message_bus or MessageBus()
        self._event_bus = event_bus or EventBus()
        self._command_bus = command_bus or CommandBus()
        self._query_bus = query_bus or QueryBus()
        self._broadcast_bus = broadcast_bus or BroadcastBus()
        self._request_response_bus = request_response_bus or RequestResponseBus()

        # Set services
        self._registry = registry or RuntimeRegistry()
        self._health_service = health_service or RuntimeHealthService(self._registry)
        self._context_manager = context_manager or RuntimeContextManager()

        # Register with registry
        await self._registry.register(
            runtime_id=self._runtime_id or self.__class__.__name__.lower(),
            name=self._name or self.__class__.__name__,
            type=self._get_runtime_type(),
            version=self._version,
        )

        self._communication_initialized = True
        logger.info(f"Communication initialized for runtime: {self._runtime_id}")

    def _get_runtime_type(self) -> str:
        """Get the runtime type from the class name."""
        class_name = self.__class__.__name__
        if class_name.endswith("Runtime"):
            return class_name[:-7].lower()
        return class_name.lower()

    @property
    def runtime_id(self) -> str:
        """Get the runtime ID."""
        return self._runtime_id or self.__class__.__name__.lower()

    @property
    def message_bus(self) -> Any:
        """Get the message bus."""
        if self._message_bus is None:
            raise RuntimeError("Communication not initialized. Call initialize_communication() first.")
        return self._message_bus

    @property
    def event_bus(self) -> Any:
        """Get the event bus."""
        if self._event_bus is None:
            raise RuntimeError("Communication not initialized. Call initialize_communication() first.")
        return self._event_bus

    @property
    def command_bus(self) -> Any:
        """Get the command bus."""
        if self._command_bus is None:
            raise RuntimeError("Communication not initialized. Call initialize_communication() first.")
        return self._command_bus

    @property
    def query_bus(self) -> Any:
        """Get the query bus."""
        if self._query_bus is None:
            raise RuntimeError("Communication not initialized. Call initialize_communication() first.")
        return self._query_bus

    @property
    def broadcast_bus(self) -> Any:
        """Get the broadcast bus."""
        if self._broadcast_bus is None:
            raise RuntimeError("Communication not initialized. Call initialize_communication() first.")
        return self._broadcast_bus

    @property
    def request_response_bus(self) -> Any:
        """Get the request/response bus."""
        if self._request_response_bus is None:
            raise RuntimeError("Communication not initialized. Call initialize_communication() first.")
        return self._request_response_bus

    async def send_command(
        self,
        target_runtime_id: str,
        command_type: str,
        payload: Dict[str, Any] = None,
        timeout: float = 30.0,
        priority: str = "normal",
    ) -> Any:
        """
        Send a command to another runtime.

        Args:
            target_runtime_id: ID of the target runtime.
            command_type: Type of command.
            payload: Command payload.
            timeout: Timeout in seconds.
            priority: Command priority.

        Returns:
            Result of command execution.
        """
        from tangku_agentos.runtime_communication import Command, MessageType

        command = Command(
            message_type=MessageType.COMMAND,
            sender_id=self.runtime_id,
            recipient_id=target_runtime_id,
            command_type=command_type,
            payload=payload or {},
            timeout=timeout,
            priority=priority,
        )

        return await self.command_bus.send(command)

    async def send_query(
        self,
        target_runtime_id: str,
        query_type: str,
        payload: Dict[str, Any] = None,
        timeout: float = 30.0,
        priority: str = "normal",
    ) -> Any:
        """
        Send a query to another runtime.

        Args:
            target_runtime_id: ID of the target runtime.
            query_type: Type of query.
            payload: Query payload.
            timeout: Timeout in seconds.
            priority: Query priority.

        Returns:
            Result of query execution.
        """
        from tangku_agentos.runtime_communication import Query, MessageType

        query = Query(
            message_type=MessageType.QUERY,
            sender_id=self.runtime_id,
            recipient_id=target_runtime_id,
            query_type=query_type,
            payload=payload or {},
            timeout=timeout,
            priority=priority,
        )

        return await self.query_bus.ask(query)

    async def publish_event(
        self,
        event_type: str,
        payload: Dict[str, Any] = None,
        priority: str = "normal",
    ) -> None:
        """
        Publish an event.

        Args:
            event_type: Type of event.
            payload: Event payload.
            priority: Event priority.
        """
        from tangku_agentos.runtime_communication import Event, MessageType

        event = Event(
            message_type=MessageType.EVENT,
            sender_id=self.runtime_id,
            event_type=event_type,
            payload=payload or {},
            priority=priority,
        )

        await self.event_bus.publish(event)

    async def broadcast(
        self,
        broadcast_type: str,
        payload: Dict[str, Any] = None,
        channels: List[str] = None,
        priority: str = "normal",
    ) -> int:
        """
        Broadcast a message to all subscribers.

        Args:
            broadcast_type: Type of broadcast.
            payload: Broadcast payload.
            channels: Channels to broadcast to.
            priority: Broadcast priority.

        Returns:
            Number of subscribers notified.
        """
        from tangku_agentos.runtime_communication import Broadcast, MessageType

        broadcast = Broadcast(
            message_type=MessageType.BROADCAST,
            sender_id=self.runtime_id,
            broadcast_type=broadcast_type,
            payload=payload or {},
            channels=channels,
            priority=priority,
        )

        return await self.broadcast_bus.broadcast(broadcast)

    async def cleanup_communication(self) -> None:
        """Clean up communication resources."""
        if not self._communication_initialized:
            return

        # Unregister from registry
        if self._registry and self._runtime_id:
            self._registry.unregister(self._runtime_id)

        self._communication_initialized = False
        logger.info(f"Communication cleaned up for runtime: {self._runtime_id}")


class IntegratedRuntime(BaseRuntime):
    """
    Base class for integrated runtimes.

    This class extends BaseRuntime with additional convenience methods
    and templates for common runtime patterns.

    Example:
        >>> from tangku_agentos.runtime_communication.integration.runtime_template import IntegratedRuntime
        >>> 
        >>> class MemoryRuntime(IntegratedRuntime):
        ...     def __init__(self, config: RuntimeConfig):
        ...         super().__init__(config)
        ...     
        ...     async def _initialize(self) -> None:
        ...         # Initialize memory-specific components
        ...         self._memory_store = {}
        ...     
        ...     async def _start(self) -> None:
        ...         # Start memory-specific components
        ...         pass
        ...     
        ...     async def handle_command(self, command: Command) -> Any:
        ...         # Handle memory commands
        ...         if command.command_type == "save":
        ...             return await self._handle_save(command)
        ...         elif command.command_type == "load":
        ...             return await self._handle_load(command)
        ...         else:
        ...             raise ValueError(f"Unknown command: {command.command_type}")
        ...     
        ...     async def handle_query(self, query: Query) -> Any:
        ...         # Handle memory queries
        ...         if query.query_type == "get":
        ...             return await self._handle_get(query)
        ...         elif query.query_type == "search":
        ...             return await self._handle_search(query)
        ...         else:
        ...             raise ValueError(f"Unknown query: {query.query_type}")
    """

    def __init__(
        self,
        config: "RuntimeConfig",
        capabilities: Optional["RuntimeCapabilities"] = None,
    ):
        """
        Initialize the integrated runtime.

        Args:
            config: Runtime configuration.
            capabilities: Runtime capabilities.
        """
        super().__init__(config, capabilities)

        # Command handlers
        self._command_handlers: Dict[str, Any] = {}

        # Query handlers
        self._query_handlers: Dict[str, Any] = {}

        # Event handlers
        self._event_handlers: Dict[str, Any] = {}

    async def _initialize(self) -> None:
        """
        Initialize the runtime.

        Subclasses should override this method to perform runtime-specific
        initialization. The default implementation does nothing.
        """
        pass

    async def _start(self) -> None:
        """
        Start the runtime.

        Subclasses should override this method to perform runtime-specific
        startup. The default implementation does nothing.
        """
        pass

    async def _stop(self) -> None:
        """
        Stop the runtime.

        Subclasses should override this method to perform runtime-specific
        shutdown. The default implementation does nothing.
        """
        pass

    async def handle_command(self, command: "Command") -> Any:
        """
        Handle an incoming command.

        This implementation checks for registered command handlers
        and calls them if found. Subclasses can override this method
        for custom command handling.

        Args:
            command: The command to handle.

        Returns:
            Result of command execution.

        Raises:
            ValueError: If no handler is found for the command type.
        """
        command_type = command.command_type

        # Check for registered handler
        if command_type in self._command_handlers:
            handler = self._command_handlers[command_type]
            return await handler(command)

        # Check for standard command handling
        if hasattr(self, f"_handle_{command_type}"):
            method = getattr(self, f"_handle_{command_type}")
            return await method(command)

        # No handler found
        raise ValueError(f"No handler for command type: {command_type}")

    async def handle_query(self, query: "Query") -> Any:
        """
        Handle an incoming query.

        This implementation checks for registered query handlers
        and calls them if found. Subclasses can override this method
        for custom query handling.

        Args:
            query: The query to handle.

        Returns:
            Result of query execution.

        Raises:
            ValueError: If no handler is found for the query type.
        """
        query_type = query.query_type

        # Check for registered handler
        if query_type in self._query_handlers:
            handler = self._query_handlers[query_type]
            return await handler(query)

        # Check for standard query handling
        if hasattr(self, f"_handle_{query_type}"):
            method = getattr(self, f"_handle_{query_type}")
            return await method(query)

        # No handler found
        raise ValueError(f"No handler for query type: {query_type}")

    async def handle_event(self, event: "Event") -> None:
        """
        Handle an incoming event.

        This implementation checks for registered event handlers
        and calls them if found. Subclasses can override this method
        for custom event handling.

        Args:
            event: The event to handle.
        """
        event_type = event.event_type

        # Check for registered handler
        if event_type in self._event_handlers:
            for handler in self._event_handlers[event_type]:
                try:
                    await handler(event)
                except Exception as e:
                    logger.error(f"Error in event handler for {event_type}: {e}")

        # Check for standard event handling
        if hasattr(self, f"_handle_{event_type}"):
            method = getattr(self, f"_handle_{event_type}")
            await method(event)

    def register_command_handler(
        self,
        command_type: str,
        handler: Any,
    ) -> None:
        """
        Register a handler for a specific command type.

        Args:
            command_type: Type of command to handle.
            handler: Handler function or method.
        """
        self._command_handlers[command_type] = handler

    def register_query_handler(
        self,
        query_type: str,
        handler: Any,
    ) -> None:
        """
        Register a handler for a specific query type.

        Args:
            query_type: Type of query to handle.
            handler: Handler function or method.
        """
        self._query_handlers[query_type] = handler

    def register_event_handler(
        self,
        event_type: str,
        handler: Any,
    ) -> None:
        """
        Register a handler for a specific event type.

        Args:
            event_type: Type of event to handle.
            handler: Handler function or method.
        """
        if event_type not in self._event_handlers:
            self._event_handlers[event_type] = []
        self._event_handlers[event_type].append(handler)

    def unregister_command_handler(self, command_type: str) -> bool:
        """
        Unregister a command handler.

        Args:
            command_type: Type of command.

        Returns:
            True if handler was found and removed, False otherwise.
        """
        if command_type in self._command_handlers:
            del self._command_handlers[command_type]
            return True
        return False

    def unregister_query_handler(self, query_type: str) -> bool:
        """
        Unregister a query handler.

        Args:
            query_type: Type of query.

        Returns:
            True if handler was found and removed, False otherwise.
        """
        if query_type in self._query_handlers:
            del self._query_handlers[query_type]
            return True
        return False

    def unregister_event_handler(self, event_type: str, handler: Any = None) -> bool:
        """
        Unregister an event handler.

        Args:
            event_type: Type of event.
            handler: Specific handler to remove (removes all if None).

        Returns:
            True if handler was found and removed, False otherwise.
        """
        if event_type in self._event_handlers:
            if handler is None:
                del self._event_handlers[event_type]
                return True
            elif handler in self._event_handlers[event_type]:
                self._event_handlers[event_type].remove(handler)
                return True
        return False


# Convenience function for creating runtime configurations

def create_runtime_config(
    runtime_id: str = "",
    name: str = "",
    version: str = "1.0.0",
    description: str = "",
    capabilities: Set[str] = None,
    dependencies: List[str] = None,
    auto_start: bool = True,
    timeout: float = 30.0,
    max_retries: int = 3,
    metadata: Dict[str, Any] = None,
) -> "RuntimeConfig":
    """
    Create a runtime configuration.

    Args:
        runtime_id: Unique ID for the runtime.
        name: Human-readable name.
        version: Runtime version.
        description: Runtime description.
        capabilities: Set of runtime capabilities.
        dependencies: List of runtime dependencies.
        auto_start: Whether to auto-start on registration.
        timeout: Default timeout for operations.
        max_retries: Maximum retry attempts.
        metadata: Additional runtime metadata.

    Returns:
        RuntimeConfig instance.
    """
    from tangku_agentos.runtime_communication.integration.base import RuntimeConfig

    return RuntimeConfig(
        runtime_id=runtime_id,
        name=name,
        version=version,
        description=description,
        capabilities=capabilities or set(),
        dependencies=dependencies or [],
        auto_start=auto_start,
        timeout=timeout,
        max_retries=max_retries,
        metadata=metadata or {},
    )


# Convenience function for creating runtime capabilities

def create_runtime_capabilities(
    can_handle_commands: bool = True,
    can_handle_queries: bool = True,
    can_publish_events: bool = True,
    can_subscribe_events: bool = True,
    can_broadcast: bool = True,
    can_stream: bool = False,
    can_execute_tasks: bool = True,
    supports_health_checks: bool = True,
    supports_metrics: bool = True,
    supports_tracing: bool = True,
) -> "RuntimeCapabilities":
    """
    Create runtime capabilities.

    Args:
        can_handle_commands: Whether runtime can handle commands.
        can_handle_queries: Whether runtime can handle queries.
        can_publish_events: Whether runtime can publish events.
        can_subscribe_events: Whether runtime can subscribe to events.
        can_broadcast: Whether runtime can broadcast messages.
        can_stream: Whether runtime can handle streams.
        can_execute_tasks: Whether runtime can execute async tasks.
        supports_health_checks: Whether runtime supports health checks.
        supports_metrics: Whether runtime supports metrics collection.
        supports_tracing: Whether runtime supports distributed tracing.

    Returns:
        RuntimeCapabilities instance.
    """
    from tangku_agentos.runtime_communication.integration.base import RuntimeCapabilities

    return RuntimeCapabilities(
        can_handle_commands=can_handle_commands,
        can_handle_queries=can_handle_queries,
        can_publish_events=can_publish_events,
        can_subscribe_events=can_subscribe_events,
        can_broadcast=can_broadcast,
        can_stream=can_stream,
        can_execute_tasks=can_execute_tasks,
        supports_health_checks=supports_health_checks,
        supports_metrics=supports_metrics,
        supports_tracing=supports_tracing,
    )
