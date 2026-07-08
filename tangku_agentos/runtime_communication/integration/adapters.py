"""
Runtime Communication Framework - Backward Compatibility Adapters

This module provides adapters for backward compatibility with existing
TangkuAgentOS runtime communication patterns.

The adapters allow older runtimes to continue working while internally
routing through the new Runtime Communication Framework.

Key Components:
- LegacyRuntimeAdapter: Adapts legacy runtime communication to the new framework
- RuntimeCompatibilityLayer: Provides compatibility layer for old APIs
- MessageAdapter: Adapts old message formats to new message models
- CommandAdapter: Adapts old command formats to new command models
- QueryAdapter: Adapts old query formats to new query models

Author: TangkuAgentOS Team
License: MIT
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Set, TYPE_CHECKING, Union

if TYPE_CHECKING:
    from tangku_agentos.runtime_communication.models.messages import (
        Message,
        MessageType,
        Command,
        Query,
        Event,
    )
    from tangku_agentos.runtime_communication.buses import (
        MessageBus,
        EventBus,
        CommandBus,
        QueryBus,
    )
    from tangku_agentos.runtime_communication.integration.base import BaseRuntime

logger = logging.getLogger(__name__)


@dataclass
class LegacyMessage:
    """
    Represents a legacy message format.

    This is used to adapt old message formats to the new framework.

    Attributes:
        message_type: Type of the message.
        sender: Sender of the message.
        recipient: Recipient of the message.
        payload: Message payload.
        metadata: Additional metadata.
    """

    message_type: str
    sender: str
    recipient: Optional[str] = None
    payload: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class LegacyCommand:
    """
    Represents a legacy command format.

    Attributes:
        command: Command name.
        args: Command arguments.
        kwargs: Command keyword arguments.
        sender: Sender of the command.
        recipient: Recipient of the command.
    """

    command: str
    args: List[Any] = field(default_factory=list)
    kwargs: Dict[str, Any] = field(default_factory=dict)
    sender: str = ""
    recipient: Optional[str] = None


@dataclass
class LegacyQuery:
    """
    Represents a legacy query format.

    Attributes:
        query: Query name.
        args: Query arguments.
        kwargs: Query keyword arguments.
        sender: Sender of the query.
        recipient: Recipient of the query.
    """

    query: str
    args: List[Any] = field(default_factory=list)
    kwargs: Dict[str, Any] = field(default_factory=dict)
    sender: str = ""
    recipient: Optional[str] = None


class MessageAdapter:
    """
    Adapter for converting between legacy message formats and new message models.

    This adapter provides methods to convert legacy message formats to the
    new Runtime Communication Framework message models.

    Example:
        >>> from tangku_agentos.runtime_communication.integration.adapters import MessageAdapter
        >>> 
        >>> adapter = MessageAdapter()
        >>> 
        >>> # Convert legacy message to new format
        >>> legacy_msg = LegacyMessage(
        ...     message_type="command",
        ...     sender="runtime_a",
        ...     recipient="runtime_b",
        ...     payload={"command": "do_something", "param": "value"}
        ... )
        >>> new_msg = adapter.to_new_message(legacy_msg)
    """

    def __init__(self):
        """Initialize the message adapter."""
        self._type_mapping = {
            "command": "COMMAND",
            "query": "QUERY",
            "event": "EVENT",
            "broadcast": "BROADCAST",
            "notification": "NOTIFICATION",
            "response": "RESPONSE",
            "message": "MESSAGE",
        }

    def to_new_message(self, legacy_message: LegacyMessage) -> "Message":
        """
        Convert a legacy message to a new Message model.

        Args:
            legacy_message: Legacy message to convert.

        Returns:
            New Message model.
        """
        from tangku_agentos.runtime_communication import Message, MessageType

        message_type = self._map_message_type(legacy_message.message_type)

        return Message(
            message_type=message_type,
            sender_id=legacy_message.sender,
            recipient_id=legacy_message.recipient,
            payload=legacy_message.payload,
            metadata=legacy_message.metadata,
        )

    def from_new_message(self, message: "Message") -> LegacyMessage:
        """
        Convert a new Message model to a legacy message format.

        Args:
            message: New message to convert.

        Returns:
            Legacy message format.
        """
        message_type = self._reverse_map_message_type(message.message_type)

        return LegacyMessage(
            message_type=message_type,
            sender=message.sender_id,
            recipient=message.recipient_id,
            payload=message.payload,
            metadata=message.metadata,
        )

    def _map_message_type(self, message_type: str) -> MessageType:
        """
        Map legacy message type to new MessageType.

        Args:
            message_type: Legacy message type.

        Returns:
            New MessageType.
        """
        from tangku_agentos.runtime_communication import MessageType

        return MessageType[self._type_mapping.get(message_type.lower(), "MESSAGE")]

    def _reverse_map_message_type(self, message_type: MessageType) -> str:
        """
        Map new MessageType to legacy message type.

        Args:
            message_type: New MessageType.

        Returns:
            Legacy message type.
        """
        reverse_mapping = {v: k for k, v in self._type_mapping.items()}
        return reverse_mapping.get(message_type.value, "message")


class CommandAdapter:
    """
    Adapter for converting between legacy command formats and new command models.

    Example:
        >>> from tangku_agentos.runtime_communication.integration.adapters import CommandAdapter
        >>> 
        >>> adapter = CommandAdapter()
        >>> 
        >>> # Convert legacy command to new format
        >>> legacy_cmd = LegacyCommand(
        ...     command="do_something",
        ...     args=["param1", "param2"],
        ...     kwargs={"option": "value"},
        ...     sender="runtime_a",
        ...     recipient="runtime_b"
        ... )
        >>> new_cmd = adapter.to_new_command(legacy_cmd)
    """

    def to_new_command(self, legacy_command: LegacyCommand) -> "Command":
        """
        Convert a legacy command to a new Command model.

        Args:
            legacy_command: Legacy command to convert.

        Returns:
            New Command model.
        """
        from tangku_agentos.runtime_communication import Command, MessageType

        # Combine args and kwargs into payload
        payload = {
            "command": legacy_command.command,
            "args": legacy_command.args,
            **legacy_command.kwargs,
        }

        return Command(
            message_type=MessageType.COMMAND,
            sender_id=legacy_command.sender,
            recipient_id=legacy_command.recipient,
            command_type=legacy_command.command,
            payload=payload,
        )

    def from_new_command(self, command: "Command") -> LegacyCommand:
        """
        Convert a new Command model to a legacy command format.

        Args:
            command: New command to convert.

        Returns:
            Legacy command format.
        """
        payload = command.payload or {}
        args = payload.get("args", [])
        kwargs = {k: v for k, v in payload.items() if k != "args" and k != "command"}

        return LegacyCommand(
            command=command.command_type,
            args=args,
            kwargs=kwargs,
            sender=command.sender_id,
            recipient=command.recipient_id,
        )


class QueryAdapter:
    """
    Adapter for converting between legacy query formats and new query models.

    Example:
        >>> from tangku_agentos.runtime_communication.integration.adapters import QueryAdapter
        >>> 
        >>> adapter = QueryAdapter()
        >>> 
        >>> # Convert legacy query to new format
        >>> legacy_query = LegacyQuery(
        ...     query="get_info",
        ...     args=["param1"],
        ...     kwargs={"option": "value"},
        ...     sender="runtime_a",
        ...     recipient="runtime_b"
        ... )
        >>> new_query = adapter.to_new_query(legacy_query)
    """

    def to_new_query(self, legacy_query: LegacyQuery) -> "Query":
        """
        Convert a legacy query to a new Query model.

        Args:
            legacy_query: Legacy query to convert.

        Returns:
            New Query model.
        """
        from tangku_agentos.runtime_communication import Query, MessageType

        # Combine args and kwargs into payload
        payload = {
            "query": legacy_query.query,
            "args": legacy_query.args,
            **legacy_query.kwargs,
        }

        return Query(
            message_type=MessageType.QUERY,
            sender_id=legacy_query.sender,
            recipient_id=legacy_query.recipient,
            query_type=legacy_query.query,
            payload=payload,
        )

    def from_new_query(self, query: "Query") -> LegacyQuery:
        """
        Convert a new Query model to a legacy query format.

        Args:
            query: New query to convert.

        Returns:
            Legacy query format.
        """
        payload = query.payload or {}
        args = payload.get("args", [])
        kwargs = {k: v for k, v in payload.items() if k != "args" and k != "query"}

        return LegacyQuery(
            query=query.query_type,
            args=args,
            kwargs=kwargs,
            sender=query.sender_id,
            recipient=query.recipient_id,
        )


class LegacyRuntimeAdapter:
    """
    Adapter for legacy runtimes to work with the new Runtime Communication Framework.

    This adapter wraps a legacy runtime and provides the necessary interfaces
    to integrate with the new communication framework.

    The adapter:
    - Intercepts legacy method calls
    - Converts them to new message formats
    - Routes them through the appropriate bus
    - Converts responses back to legacy format

    Example:
        >>> from tangku_agentos.runtime_communication.integration.adapters import LegacyRuntimeAdapter
        >>> 
        >>> # Create a legacy runtime (simplified example)
        >>> class LegacyMemoryRuntime:
        ...     def save(self, data):
        ...         return "saved"
        ...     def load(self, id):
        ...         return {"id": id, "data": "loaded"}
        >>> 
        >>> # Wrap it with the adapter
        >>> adapter = LegacyRuntimeAdapter(
        ...     legacy_runtime=LegacyMemoryRuntime(),
        ...     runtime_id="memory_runtime",
        ...     command_bus=command_bus,
        ...     query_bus=query_bus
        ... )
        >>> 
        >>> # Now the legacy runtime can receive commands and queries
        >>> await adapter.start()
    """

    def __init__(
        self,
        legacy_runtime: Any,
        runtime_id: str,
        name: str = "",
        version: str = "1.0.0",
        capabilities: Optional[Set[str]] = None,
        command_bus: Optional["CommandBus"] = None,
        query_bus: Optional["QueryBus"] = None,
        event_bus: Optional["EventBus"] = None,
        message_bus: Optional["MessageBus"] = None,
    ):
        """
        Initialize the legacy runtime adapter.

        Args:
            legacy_runtime: The legacy runtime instance to adapt.
            runtime_id: Unique ID for the runtime.
            name: Human-readable name.
            version: Runtime version.
            capabilities: Set of runtime capabilities.
            command_bus: Command bus instance.
            query_bus: Query bus instance.
            event_bus: Event bus instance.
            message_bus: Message bus instance.
        """
        self._legacy_runtime = legacy_runtime
        self._runtime_id = runtime_id
        self._name = name or runtime_id
        self._version = version
        self._capabilities = capabilities or set()

        # Buses
        self._command_bus = command_bus
        self._query_bus = query_bus
        self._event_bus = event_bus
        self._message_bus = message_bus

        # Command and query handlers
        self._command_handlers: Dict[str, Callable] = {}
        self._query_handlers: Dict[str, Callable] = {}

        # Running state
        self._running = False

        # Register default handlers
        self._register_default_handlers()

    @property
    def runtime_id(self) -> str:
        """Get the runtime ID."""
        return self._runtime_id

    @property
    def legacy_runtime(self) -> Any:
        """Get the legacy runtime instance."""
        return self._legacy_runtime

    def _register_default_handlers(self) -> None:
        """Register default command and query handlers."""
        # Register handlers for common legacy methods
        # These will be mapped to the legacy runtime's methods

        # Common command patterns
        command_methods = [
            "save", "load", "delete", "update", "create",
            "start", "stop", "pause", "resume", "restart",
            "execute", "run", "process", "handle",
            "connect", "disconnect", "sync", "index",
            "send", "publish", "broadcast",
        ]

        for method in command_methods:
            if hasattr(self._legacy_runtime, method):
                self._command_handlers[method] = self._create_command_handler(method)

        # Common query patterns
        query_methods = [
            "get", "list", "search", "find", "query",
            "info", "status", "state", "health",
            "check", "validate", "exists",
        ]

        for method in query_methods:
            if hasattr(self._legacy_runtime, method):
                self._query_handlers[method] = self._create_query_handler(method)

    def _create_command_handler(self, method_name: str) -> Callable:
        """
        Create a command handler for a legacy method.

        Args:
            method_name: Name of the method to handle.

        Returns:
            Command handler function.
        """

        def handler(command: "Command") -> Any:
            method = getattr(self._legacy_runtime, method_name)
            payload = command.payload or {}

            # Extract args and kwargs from payload
            args = payload.get("args", [])
            kwargs = {k: v for k, v in payload.items() if k != "args"}

            # Call the legacy method
            try:
                result = method(*args, **kwargs)
                return result
            except Exception as e:
                logger.error(f"Error handling command {method_name}: {e}")
                raise

        return handler

    def _create_query_handler(self, method_name: str) -> Callable:
        """
        Create a query handler for a legacy method.

        Args:
            method_name: Name of the method to handle.

        Returns:
            Query handler function.
        """

        def handler(query: "Query") -> Any:
            method = getattr(self._legacy_runtime, method_name)
            payload = query.payload or {}

            # Extract args and kwargs from payload
            args = payload.get("args", [])
            kwargs = {k: v for k, v in payload.items() if k != "args"}

            # Call the legacy method
            try:
                result = method(*args, **kwargs)
                return result
            except Exception as e:
                logger.error(f"Error handling query {method_name}: {e}")
                raise

        return handler

    async def start(self) -> None:
        """
        Start the adapter and register with the buses.
        """
        if self._running:
            return

        self._running = True

        # Register command handlers
        if self._command_bus:
            for command_type, handler in self._command_handlers.items():
                self._command_bus.register_handler(
                    command_type, handler, self._runtime_id
                )

        # Register query handlers
        if self._query_bus:
            for query_type, handler in self._query_handlers.items():
                self._query_bus.register_handler(
                    query_type, handler, self._runtime_id
                )

        logger.info(f"Legacy runtime adapter started: {self._runtime_id}")

    async def stop(self) -> None:
        """
        Stop the adapter and unregister from the buses.
        """
        if not self._running:
            return

        self._running = False

        # Unregister command handlers
        if self._command_bus:
            for command_type in self._command_handlers:
                self._command_bus.unregister_handler(command_type, self._runtime_id)

        # Unregister query handlers
        if self._query_bus:
            for query_type in self._query_handlers:
                self._query_bus.unregister_handler(query_type, self._runtime_id)

        logger.info(f"Legacy runtime adapter stopped: {self._runtime_id}")

    def register_command_handler(
        self,
        command_type: str,
        handler: Callable[["Command"], Any],
    ) -> None:
        """
        Register a custom command handler.

        Args:
            command_type: Type of command to handle.
            handler: Handler function.
        """
        self._command_handlers[command_type] = handler
        if self._running and self._command_bus:
            self._command_bus.register_handler(
                command_type, handler, self._runtime_id
            )

    def register_query_handler(
        self,
        query_type: str,
        handler: Callable[["Query"], Any],
    ) -> None:
        """
        Register a custom query handler.

        Args:
            query_type: Type of query to handle.
            handler: Handler function.
        """
        self._query_handlers[query_type] = handler
        if self._running and self._query_bus:
            self._query_bus.register_handler(
                query_type, handler, self._runtime_id
            )

    async def send_command(
        self,
        target_runtime_id: str,
        command_type: str,
        *args,
        **kwargs,
    ) -> Any:
        """
        Send a command to another runtime.

        Args:
            target_runtime_id: ID of the target runtime.
            command_type: Type of command.
            *args: Command arguments.
            **kwargs: Command keyword arguments.

        Returns:
            Result of the command.
        """
        if not self._command_bus:
            raise RuntimeError("Command bus not configured")

        from tangku_agentos.runtime_communication import Command, MessageType

        command = Command(
            message_type=MessageType.COMMAND,
            sender_id=self._runtime_id,
            recipient_id=target_runtime_id,
            command_type=command_type,
            payload={"args": list(args), **kwargs},
        )

        return await self._command_bus.send(command)

    async def send_query(
        self,
        target_runtime_id: str,
        query_type: str,
        *args,
        **kwargs,
    ) -> Any:
        """
        Send a query to another runtime.

        Args:
            target_runtime_id: ID of the target runtime.
            query_type: Type of query.
            *args: Query arguments.
            **kwargs: Query keyword arguments.

        Returns:
            Result of the query.
        """
        if not self._query_bus:
            raise RuntimeError("Query bus not configured")

        from tangku_agentos.runtime_communication import Query, MessageType

        query = Query(
            message_type=MessageType.QUERY,
            sender_id=self._runtime_id,
            recipient_id=target_runtime_id,
            query_type=query_type,
            payload={"args": list(args), **kwargs},
        )

        return await self._query_bus.ask(query)

    async def publish_event(
        self,
        event_type: str,
        payload: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Publish an event.

        Args:
            event_type: Type of event.
            payload: Event payload.
        """
        if not self._event_bus:
            raise RuntimeError("Event bus not configured")

        from tangku_agentos.runtime_communication import Event, MessageType

        event = Event(
            message_type=MessageType.EVENT,
            sender_id=self._runtime_id,
            event_type=event_type,
            payload=payload or {},
        )

        await self._event_bus.publish(event)

    def __getattr__(self, name: str) -> Any:
        """
        Delegate attribute access to the legacy runtime.

        This allows the adapter to be used as a drop-in replacement
        for the legacy runtime in many cases.

        Args:
            name: Attribute name.

        Returns:
            Attribute from the legacy runtime.

        Raises:
            AttributeError: If attribute not found.
        """
        return getattr(self._legacy_runtime, name)


class RuntimeCompatibilityLayer:
    """
    Compatibility layer for old TangkuAgentOS runtime APIs.

    This layer provides a unified interface that old runtimes can use,
    which internally routes through the new Runtime Communication Framework.

    The compatibility layer:
    - Provides old-style method signatures
    - Converts calls to new message formats
    - Routes through appropriate buses
    - Converts responses back to old format

    Example:
        >>> from tangku_agentos.runtime_communication.integration.adapters import RuntimeCompatibilityLayer
        >>> 
        >>> # Create compatibility layer
        >>> compat = RuntimeCompatibilityLayer(
        ...     runtime_id="my_runtime",
        ...     command_bus=command_bus,
        ...     query_bus=query_bus,
        ...     event_bus=event_bus
        ... )
        >>> 
        >>> # Use old-style API
        >>> result = await compat.call_method("other_runtime", "do_something", arg1, arg2)
    """

    def __init__(
        self,
        runtime_id: str,
        name: str = "",
        version: str = "1.0.0",
        command_bus: Optional["CommandBus"] = None,
        query_bus: Optional["QueryBus"] = None,
        event_bus: Optional["EventBus"] = None,
        message_bus: Optional["MessageBus"] = None,
    ):
        """
        Initialize the compatibility layer.

        Args:
            runtime_id: Unique ID for the runtime.
            name: Human-readable name.
            version: Runtime version.
            command_bus: Command bus instance.
            query_bus: Query bus instance.
            event_bus: Event bus instance.
            message_bus: Message bus instance.
        """
        self._runtime_id = runtime_id
        self._name = name or runtime_id
        self._version = version

        # Buses
        self._command_bus = command_bus
        self._query_bus = query_bus
        self._event_bus = event_bus
        self._message_bus = message_bus

        # Adapters
        self._command_adapter = CommandAdapter()
        self._query_adapter = QueryAdapter()

    @property
    def runtime_id(self) -> str:
        """Get the runtime ID."""
        return self._runtime_id

    async def call_method(
        self,
        target_runtime_id: str,
        method_name: str,
        *args,
        **kwargs,
    ) -> Any:
        """
        Call a method on another runtime (old-style API).

        This method converts the old-style method call to a command
        and sends it through the command bus.

        Args:
            target_runtime_id: ID of the target runtime.
            method_name: Name of the method to call.
            *args: Method arguments.
            **kwargs: Method keyword arguments.

        Returns:
            Result of the method call.
        """
        if not self._command_bus:
            raise RuntimeError("Command bus not configured")

        from tangku_agentos.runtime_communication import Command, MessageType

        command = Command(
            message_type=MessageType.COMMAND,
            sender_id=self._runtime_id,
            recipient_id=target_runtime_id,
            command_type=method_name,
            payload={"args": list(args), **kwargs},
        )

        return await self._command_bus.send(command)

    async def query_method(
        self,
        target_runtime_id: str,
        method_name: str,
        *args,
        **kwargs,
    ) -> Any:
        """
        Query a method on another runtime (old-style API).

        This method converts the old-style method query to a query
        and sends it through the query bus.

        Args:
            target_runtime_id: ID of the target runtime.
            method_name: Name of the method to query.
            *args: Method arguments.
            **kwargs: Method keyword arguments.

        Returns:
            Result of the method query.
        """
        if not self._query_bus:
            raise RuntimeError("Query bus not configured")

        from tangku_agentos.runtime_communication import Query, MessageType

        query = Query(
            message_type=MessageType.QUERY,
            sender_id=self._runtime_id,
            recipient_id=target_runtime_id,
            query_type=method_name,
            payload={"args": list(args), **kwargs},
        )

        return await self._query_bus.ask(query)

    async def send_event(
        self,
        target_runtime_id: str,
        event_name: str,
        payload: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Send an event to another runtime (old-style API).

        Args:
            target_runtime_id: ID of the target runtime.
            event_name: Name of the event.
            payload: Event payload.
        """
        if not self._event_bus:
            raise RuntimeError("Event bus not configured")

        from tangku_agentos.runtime_communication import Event, MessageType

        event = Event(
            message_type=MessageType.EVENT,
            sender_id=self._runtime_id,
            recipient_id=target_runtime_id,
            event_type=event_name,
            payload=payload or {},
        )

        await self._event_bus.publish(event)

    async def broadcast(
        self,
        event_name: str,
        payload: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Broadcast an event to all runtimes (old-style API).

        Args:
            event_name: Name of the event.
            payload: Event payload.
        """
        if not self._event_bus:
            raise RuntimeError("Event bus not configured")

        from tangku_agentos.runtime_communication import Event, MessageType

        event = Event(
            message_type=MessageType.EVENT,
            sender_id=self._runtime_id,
            event_type=event_name,
            payload=payload or {},
        )

        await self._event_bus.publish(event)

    async def send_message(
        self,
        target_runtime_id: str,
        message_type: str,
        payload: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Send a message to another runtime (old-style API).

        Args:
            target_runtime_id: ID of the target runtime.
            message_type: Type of the message.
            payload: Message payload.
        """
        if not self._message_bus:
            raise RuntimeError("Message bus not configured")

        from tangku_agentos.runtime_communication import Message, MessageType

        # Map old message type to new MessageType
        type_mapping = {
            "command": MessageType.COMMAND,
            "query": MessageType.QUERY,
            "event": MessageType.EVENT,
            "broadcast": MessageType.BROADCAST,
            "notification": MessageType.NOTIFICATION,
        }

        msg_type = type_mapping.get(message_type.lower(), MessageType.MESSAGE)

        message = Message(
            message_type=msg_type,
            sender_id=self._runtime_id,
            recipient_id=target_runtime_id,
            payload=payload or {},
        )

        await self._message_bus.send(message)

    def register_command_handler(
        self,
        command_name: str,
        handler: Callable[[List[Any], Dict[str, Any]], Any],
    ) -> None:
        """
        Register a command handler (old-style API).

        Args:
            command_name: Name of the command to handle.
            handler: Handler function that takes (args, kwargs).
        """
        if not self._command_bus:
            raise RuntimeError("Command bus not configured")

        async def command_handler(command: "Command") -> Any:
            payload = command.payload or {}
            args = payload.get("args", [])
            kwargs = {k: v for k, v in payload.items() if k != "args"}
            return handler(args, kwargs)

        self._command_bus.register_handler(
            command_name, command_handler, self._runtime_id
        )

    def register_query_handler(
        self,
        query_name: str,
        handler: Callable[[List[Any], Dict[str, Any]], Any],
    ) -> None:
        """
        Register a query handler (old-style API).

        Args:
            query_name: Name of the query to handle.
            handler: Handler function that takes (args, kwargs).
        """
        if not self._query_bus:
            raise RuntimeError("Query bus not configured")

        async def query_handler(query: "Query") -> Any:
            payload = query.payload or {}
            args = payload.get("args", [])
            kwargs = {k: v for k, v in payload.items() if k != "args"}
            return handler(args, kwargs)

        self._query_bus.register_handler(
            query_name, query_handler, self._runtime_id
        )

    def register_event_handler(
        self,
        event_name: str,
        handler: Callable[[Dict[str, Any]], None],
    ) -> None:
        """
        Register an event handler (old-style API).

        Args:
            event_name: Name of the event to handle.
            handler: Handler function that takes payload.
        """
        if not self._event_bus:
            raise RuntimeError("Event bus not configured")

        async def event_handler(event: "Event") -> None:
            handler(event.payload or {})

        self._event_bus.subscribe(
            event_name, event_handler, runtime_id=self._runtime_id
        )
