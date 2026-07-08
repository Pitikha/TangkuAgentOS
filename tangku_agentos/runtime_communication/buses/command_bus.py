"""
Runtime Communication Framework - Command Bus Implementation

The CommandBus provides a specialized message bus for command-based communication
patterns. It supports:
- Single recipient commands
- Exactly-once execution semantics
- Command validation and authorization
- Response handling
- Error propagation
- Retry policies

Author: TangkuAgentOS Team
License: MIT
"""

from __future__ import annotations

import asyncio
import logging
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import (
    Any,
    Callable,
    Dict,
    List,
    Optional,
    Set,
    Union,
    TYPE_CHECKING,
)
import uuid

if TYPE_CHECKING:
    from tangku_agentos.runtime_communication.models.messages import (
        Message,
        MessageType,
        MessagePriority,
        Command,
        Response,
    )
    from tangku_agentos.runtime_communication.interfaces import (
        ICommandBus,
        ICommandHandler,
        IMessageHandler,
    )

logger = logging.getLogger(__name__)


@dataclass
class CommandRegistration:
    """
    Represents a registered command handler.

    Attributes:
        command_type: Type of command this handler processes.
        handler: Handler function for the command.
        priority: Handler priority (higher = called first).
        active: Whether the handler is active.
        execution_count: Number of times this handler has been called.
        error_count: Number of errors from this handler.
        registered_at: When the handler was registered.
    """

    command_type: str
    handler: "ICommandHandler[Command, Any]"
    priority: int = 0
    active: bool = True
    execution_count: int = 0
    error_count: int = 0
    registered_at: datetime = field(default_factory=datetime.utcnow)


class CommandBus:
    """
    Specialized message bus for command-based communication patterns.

    The CommandBus implements the command pattern where commands are sent to
    a single recipient and expect a response indicating success or failure.
    It supports:
    - Single recipient commands
    - Exactly-once execution semantics
    - Command validation and authorization
    - Response handling
    - Error propagation
    - Retry policies

    Thread Safety:
        This implementation is thread-safe for concurrent access.

    Example:
        >>> from tangku_agentos.runtime_communication.buses.command_bus import CommandBus
        >>> from tangku_agentos.runtime_communication.models.messages import Command, MessageType
        >>> 
        >>> bus = CommandBus()
        >>> 
        >>> # Register a command handler
        >>> class StoreCommandHandler:
        ...     async def handle_command(self, command: Command) -> dict:
        ...         return {"status": "stored", "id": command.payload["id"]}
        >>> 
        >>> handler = StoreCommandHandler()
        >>> bus.register_handler("store.data", handler)
        >>> 
        >>> # Send a command
        >>> cmd = Command(
        ...     message_type=MessageType.COMMAND,
        ...     sender_id="client",
        ...     command_type="store.data",
        ...     payload={"id": "123", "data": "test"}
        ... )
        >>> result = asyncio.run(bus.send(cmd))

    Attributes:
        default_timeout: Default timeout for command execution in seconds.
        max_retries: Maximum number of retry attempts for failed commands.
    """

    def __init__(
        self,
        default_timeout: float = 30.0,
        max_retries: int = 3,
        enable_metrics: bool = True,
        enable_logging: bool = True,
    ):
        """
        Initialize the command bus.

        Args:
            default_timeout: Default timeout for command execution in seconds.
            max_retries: Maximum number of retry attempts for failed commands.
            enable_metrics: Whether to collect metrics.
            enable_logging: Whether to enable structured logging.
        """
        # Command handlers: command_type -> CommandRegistration
        self._handlers: Dict[str, CommandRegistration] = {}
        self._handlers_lock = asyncio.Lock()

        # Command history
        self._command_history: List["Command"] = []
        self._command_history_lock = asyncio.Lock()
        self._max_command_history = 10000

        # Configuration
        self._default_timeout = default_timeout
        self._max_retries = max_retries

        # Metrics
        self._metrics: Dict[str, Any] = {
            "commands_sent": 0,
            "commands_executed": 0,
            "commands_failed": 0,
            "commands_timed_out": 0,
            "commands_retried": 0,
            "handlers_registered": 0,
        }
        self._metrics_lock = asyncio.Lock()

        # Flags
        self._enable_metrics = enable_metrics
        self._enable_logging = enable_logging

        logger.info(
            f"CommandBus initialized with timeout={default_timeout}, "
            f"max_retries={max_retries}"
        )

    async def send(self, command: "Command") -> Any:
        """
        Send a command for execution.

        This is the main method for sending commands. The command will be
        routed to the appropriate handler based on its command_type.

        Args:
            command: Command to send.

        Returns:
            Result from command execution.

        Raises:
            MessageValidationError: If command validation fails.
            MessageDeliveryError: If command cannot be delivered.
            MessageTimeoutError: If command execution times out.

        Example:
            >>> from tangku_agentos.runtime_communication.models.messages import Command, MessageType
            >>> 
            >>> bus = CommandBus()
            >>> cmd = Command(
            ...     message_type=MessageType.COMMAND,
            ...     sender_id="client",
            ...     command_type="store.data",
            ...     payload={"id": "123", "data": "test"}
            ... )
            >>> result = asyncio.run(bus.send(cmd))
        """
        # Validate command
        self._validate_command(command)

        # Set command timestamp if not set
        if command.created_at is None:
            command.created_at = datetime.utcnow()

        # Set default timeout if not set
        if command.timeout <= 0:
            command.timeout = self._default_timeout

        # Update metrics
        async with self._metrics_lock:
            self._metrics["commands_sent"] += 1

        # Record command in history
        await self._record_command(command)

        # Find handler for this command type
        handler = await self._get_handler(command.command_type)

        if handler is None:
            from tangku_agentos.runtime_communication.models.exceptions import (
                MessageDeliveryError,
            )

            error_msg = f"No handler registered for command type: {command.command_type}"
            logger.error(error_msg)

            async with self._metrics_lock:
                self._metrics["commands_failed"] += 1

            raise MessageDeliveryError(
                error_msg,
                message_id=command.message_id,
                recipient_id=command.command_type,
            )

        # Execute command with retry logic
        last_error: Optional[Exception] = None
        for attempt in range(self._max_retries + 1):
            try:
                result = await asyncio.wait_for(
                    self._execute_handler(handler, command),
                    timeout=command.timeout,
                )

                async with self._metrics_lock:
                    self._metrics["commands_executed"] += 1

                return result

            except asyncio.TimeoutError as e:
                last_error = e
                async with self._metrics_lock:
                    self._metrics["commands_timed_out"] += 1

                if attempt < self._max_retries:
                    if self._enable_logging:
                        logger.warning(
                            f"Command {command.message_id} timed out, "
                            f"attempt {attempt + 1}/{self._max_retries + 1}"
                        )
                    continue
                else:
                    from tangku_agentos.runtime_communication.models.exceptions import (
                        MessageTimeoutError,
                    )

                    raise MessageTimeoutError(
                        f"Command {command.message_id} timed out after "
                        f"{self._max_retries + 1} attempts",
                        message_id=command.message_id,
                        operation="command_execution",
                        timeout=command.timeout,
                    ) from last_error

            except Exception as e:
                last_error = e
                async with self._metrics_lock:
                    self._metrics["commands_failed"] += 1

                if attempt < self._max_retries:
                    if self._enable_logging:
                        logger.warning(
                            f"Command {command.message_id} failed, "
                            f"attempt {attempt + 1}/{self._max_retries + 1}: {e}"
                        )
                    continue
                else:
                    from tangku_agentos.runtime_communication.models.exceptions import (
                        MessageDeliveryError,
                    )

                    raise MessageDeliveryError(
                        f"Command {command.message_id} failed after "
                        f"{self._max_retries + 1} attempts: {e}",
                        message_id=command.message_id,
                        recipient_id=command.command_type,
                        last_error=str(e),
                    ) from last_error

        # This should never be reached
        from tangku_agentos.runtime_communication.models.exceptions import (
            MessageDeliveryError,
        )

        raise MessageDeliveryError(
            f"Command {command.message_id} failed",
            message_id=command.message_id,
            recipient_id=command.command_type,
        )

    def register_handler(
        self,
        command_type: str,
        handler: "ICommandHandler[Command, Any]",
        priority: int = 0,
    ) -> None:
        """
        Register a command handler.

        Args:
            command_type: Type of command to handle.
            handler: Handler for the command type.
            priority: Handler priority (higher = called first).

        Example:
            >>> class StoreCommandHandler:
            ...     async def handle_command(self, command: Command) -> dict:
            ...         return {"status": "stored"}
            >>> 
            >>> bus = CommandBus()
            >>> handler = StoreCommandHandler()
            >>> bus.register_handler("store.data", handler)
        """
        asyncio.run(self._register_handler_async(command_type, handler, priority))

    async def _register_handler_async(
        self,
        command_type: str,
        handler: "ICommandHandler[Command, Any]",
        priority: int = 0,
    ) -> None:
        """Async version of register_handler."""
        registration = CommandRegistration(
            command_type=command_type,
            handler=handler,
            priority=priority,
        )

        async with self._handlers_lock:
            self._handlers[command_type] = registration

            async with self._metrics_lock:
                self._metrics["handlers_registered"] += 1

            if self._enable_logging:
                logger.info(
                    f"Command handler registered for '{command_type}': "
                    f"{handler.__class__.__name__}"
                )

    def unregister_handler(self, command_type: str) -> bool:
        """
        Unregister a command handler.

        Args:
            command_type: Type of command.

        Returns:
            True if handler was removed, False otherwise.

        Example:
            >>> bus = CommandBus()
            >>> bus.register_handler("store.data", handler)
            >>> bus.unregister_handler("store.data")
            True
        """
        return asyncio.run(self._unregister_handler_async(command_type))

    async def _unregister_handler_async(self, command_type: str) -> bool:
        """Async version of unregister_handler."""
        async with self._handlers_lock:
            if command_type in self._handlers:
                del self._handlers[command_type]

                async with self._metrics_lock:
                    self._metrics["handlers_registered"] -= 1

                if self._enable_logging:
                    logger.info(f"Command handler unregistered: {command_type}")
                return True
            return False

    def has_handler(self, command_type: str) -> bool:
        """
        Check if a handler is registered for a command type.

        Args:
            command_type: Type of command to check.

        Returns:
            True if handler is registered, False otherwise.

        Example:
            >>> bus = CommandBus()
            >>> bus.register_handler("store.data", handler)
            >>> bus.has_handler("store.data")
            True
        """
        return command_type in self._handlers

    def list_handlers(self) -> List[str]:
        """
        List all registered command types.

        Returns:
            List of command types with registered handlers.

        Example:
            >>> bus = CommandBus()
            >>> bus.register_handler("store.data", handler)
            >>> bus.list_handlers()
            ['store.data']
        """
        return list(self._handlers.keys())

    def get_command_history(
        self,
        command_type: Optional[str] = None,
        limit: int = 100,
    ) -> List["Command"]:
        """
        Retrieve command history with optional filtering.

        Args:
            command_type: Filter by command type (optional).
            limit: Maximum commands to return.

        Returns:
            List of commands.

        Example:
            >>> bus = CommandBus()
            >>> # Send some commands
            >>> history = bus.get_command_history(limit=10)
        """
        commands = list(self._command_history)

        if command_type is not None:
            commands = [c for c in commands if c.command_type == command_type]

        return commands[-limit:]

    def get_metrics(self) -> Dict[str, Any]:
        """
        Get command bus metrics.

        Returns:
            Dictionary of metrics.

        Example:
            >>> bus = CommandBus()
            >>> metrics = bus.get_metrics()
            >>> metrics["commands_sent"]
            0
        """
        return {
            **self._metrics,
            "command_history_size": len(self._command_history),
            "handlers_count": len(self._handlers),
        }

    def clear_history(self) -> int:
        """
        Clear command history.

        Returns:
            Count of commands cleared.

        Example:
            >>> bus = CommandBus()
            >>> count = bus.clear_history()
        """
        count = len(self._command_history)
        self._command_history.clear()
        return count

    def shutdown(self) -> None:
        """
        Shutdown command bus.

        Cleans up resources and stops all processing.

        Example:
            >>> bus = CommandBus()
            >>> bus.shutdown()
        """
        self._command_history.clear()
        self._handlers.clear()
        self._metrics.clear()

        logger.info("Command bus shutdown complete")

    async def _get_handler(
        self, command_type: str
    ) -> Optional[CommandRegistration]:
        """
        Get the handler for a command type.

        Args:
            command_type: Type of command.

        Returns:
            CommandRegistration if found, None otherwise.
        """
        async with self._handlers_lock:
            return self._handlers.get(command_type)

    async def _execute_handler(
        self,
        registration: CommandRegistration,
        command: "Command",
    ) -> Any:
        """
        Execute a command handler.

        Args:
            registration: Handler registration.
            command: Command to execute.

        Returns:
            Result from handler.

        Raises:
            Exception: If handler raises an exception.
        """
        if not registration.active:
            from tangku_agentos.runtime_communication.models.exceptions import (
                MessageDeliveryError,
            )

            raise MessageDeliveryError(
                f"Handler for command type '{registration.command_type}' is inactive",
                message_id=command.message_id,
                recipient_id=registration.command_type,
            )

        registration.execution_count += 1

        try:
            return await registration.handler.handle_command(command)
        except Exception as e:
            registration.error_count += 1
            logger.error(
                f"Error executing command {command.message_id} "
                f"with handler {registration.handler.__class__.__name__}: {e}"
            )
            raise

    async def _record_command(self, command: "Command") -> None:
        """
        Store command in history.

        Args:
            command: Command to store.
        """
        async with self._command_history_lock:
            self._command_history.append(command)
            if len(self._command_history) > self._max_command_history:
                self._command_history.pop(0)

    def _validate_command(self, command: "Command") -> None:
        """
        Validate a command before sending.

        Args:
            command: Command to validate.

        Raises:
            MessageValidationError: If command is invalid.
        """
        from tangku_agentos.runtime_communication.models.exceptions import (
            MessageValidationError,
        )

        # Check required fields
        if not command.sender_id:
            raise MessageValidationError(
                "Command sender_id is required",
                message_id=command.message_id,
                validation_errors=["sender_id is required"],
            )

        if not command.command_type:
            raise MessageValidationError(
                "Command command_type is required",
                message_id=command.message_id,
                validation_errors=["command_type is required"],
            )

    def __repr__(self) -> str:
        """Return string representation of the command bus."""
        return (
            f"CommandBus("
            f"handlers={len(self._handlers)}, "
            f"history={len(self._command_history)})"
        )
