"""
Runtime Communication Framework - Base Runtime Classes

This module provides the base classes that all TangkuAgentOS runtimes
must inherit from to integrate with the Runtime Communication Framework.

Key Classes:
- BaseRuntime: Abstract base class for all runtimes
- RuntimeCommunicator: Communication mixin for runtimes
- RuntimeLifecycleManager: Lifecycle management for runtimes

Author: TangkuAgentOS Team
License: MIT
"""

from __future__ import annotations

import asyncio
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from typing import (
    Any,
    Callable,
    Dict,
    List,
    Optional,
    Set,
    Type,
    Union,
    TYPE_CHECKING,
)
import uuid

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
        BroadcastBus,
        RequestResponseBus,
    )
    from tangku_agentos.runtime_communication.services.registry import RuntimeRegistry
    from tangku_agentos.runtime_communication.services.health import RuntimeHealthService
    from tangku_agentos.runtime_communication.services.context import RuntimeContextManager

logger = logging.getLogger(__name__)


class RuntimeState(Enum):
    """
    Lifecycle states for a runtime.

    Attributes:
        UNINITIALIZED: Runtime has not been initialized.
        INITIALIZING: Runtime is initializing.
        INITIALIZED: Runtime is initialized but not started.
        STARTING: Runtime is starting.
        RUNNING: Runtime is running normally.
        PAUSED: Runtime is paused.
        STOPPING: Runtime is stopping.
        STOPPED: Runtime has been stopped.
        FAILED: Runtime has failed.
        DEGRADED: Runtime is running but with issues.
        RESTARTING: Runtime is restarting.
    """

    UNINITIALIZED = auto()
    INITIALIZING = auto()
    INITIALIZED = auto()
    STARTING = auto()
    RUNNING = auto()
    PAUSED = auto()
    STOPPING = auto()
    STOPPED = auto()
    FAILED = auto()
    DEGRADED = auto()
    RESTARTING = auto()


@dataclass
class RuntimeConfig:
    """
    Configuration for a runtime.

    Attributes:
        runtime_id: Unique identifier for the runtime.
        name: Human-readable name.
        version: Runtime version.
        description: Runtime description.
        capabilities: Set of capabilities provided.
        dependencies: List of runtime IDs this runtime depends on.
        auto_start: Whether to auto-start on registration.
        timeout: Default timeout for operations.
        max_retries: Maximum retry attempts.
        metadata: Additional runtime metadata.
    """

    runtime_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    version: str = "1.0.0"
    description: str = ""
    capabilities: Set[str] = field(default_factory=set)
    dependencies: List[str] = field(default_factory=list)
    auto_start: bool = True
    timeout: float = 30.0
    max_retries: int = 3
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RuntimeCapabilities:
    """
    Capabilities of a runtime.

    Attributes:
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
    """

    can_handle_commands: bool = True
    can_handle_queries: bool = True
    can_publish_events: bool = True
    can_subscribe_events: bool = True
    can_broadcast: bool = True
    can_stream: bool = False
    can_execute_tasks: bool = True
    supports_health_checks: bool = True
    supports_metrics: bool = True
    supports_tracing: bool = True


class BaseRuntime(ABC):
    """
    Abstract base class for all TangkuAgentOS runtimes.

    Every runtime in TangkuAgentOS MUST inherit from this class (directly
    or indirectly) to ensure proper integration with the Runtime Communication
    Framework.

    This class provides:
    - Runtime identification and metadata
    - Lifecycle management
    - Communication bus access
    - Health monitoring
    - Context management
    - Automatic registration with the runtime registry

    Thread Safety:
        This class is thread-safe for concurrent access.

    Example:
        >>> from tangku_agentos.runtime_communication.integration.base import BaseRuntime
        >>> 
        >>> class MyRuntime(BaseRuntime):
        ...     def __init__(self, config: RuntimeConfig):
        ...         super().__init__(config)
        ...     
        ...     async def initialize(self) -> None:
        ...         # Initialize runtime-specific components
        ...         pass
        ...     
        ...     async def start(self) -> None:
        ...         # Start runtime-specific components
        ...         pass
        ...     
        ...     async def stop(self) -> None:
        ...         # Stop runtime-specific components
        ...         pass
        ...     
        ...     async def handle_command(self, command: Command) -> Any:
        ...         # Handle incoming commands
        ...         pass
        ...     
        ...     async def handle_query(self, query: Query) -> Any:
        ...         # Handle incoming queries
        ...         pass

    Attributes:
        runtime_id: Unique identifier for the runtime.
        config: Runtime configuration.
        state: Current runtime state.
        capabilities: Runtime capabilities.
    """

    def __init__(
        self,
        config: RuntimeConfig,
        capabilities: Optional[RuntimeCapabilities] = None,
    ):
        """
        Initialize the base runtime.

        Args:
            config: Runtime configuration.
            capabilities: Runtime capabilities (defaults to all enabled).
        """
        self._runtime_id = config.runtime_id or str(uuid.uuid4())
        self._config = config
        self._state = RuntimeState.UNINITIALIZED
        self._capabilities = capabilities or RuntimeCapabilities()

        # Communication buses (lazy initialized)
        self._message_bus: Optional["MessageBus"] = None
        self._event_bus: Optional["EventBus"] = None
        self._command_bus: Optional["CommandBus"] = None
        self._query_bus: Optional["QueryBus"] = None
        self._broadcast_bus: Optional["BroadcastBus"] = None
        self._request_response_bus: Optional["RequestResponseBus"] = None

        # Service references (injected or lazy initialized)
        self._registry: Optional["RuntimeRegistry"] = None
        self._health_service: Optional["RuntimeHealthService"] = None
        self._context_manager: Optional["RuntimeContextManager"] = None

        # Lifecycle callbacks
        self._on_initialize: List[Callable[[], None]] = []
        self._on_start: List[Callable[[], None]] = []
        self._on_stop: List[Callable[[], None]] = []
        self._on_pause: List[Callable[[], None]] = []
        self._on_resume: List[Callable[[], None]] = []
        self._on_fail: List[Callable[[Exception], None]] = []

        # Created at timestamp
        self._created_at = datetime.utcnow()

        # Last state change
        self._last_state_change = self._created_at

        logger.debug(f"BaseRuntime initialized: {self._runtime_id}")

    @property
    def runtime_id(self) -> str:
        """Get the runtime ID."""
        return self._runtime_id

    @property
    def config(self) -> RuntimeConfig:
        """Get the runtime configuration."""
        return self._config

    @property
    def state(self) -> RuntimeState:
        """Get the current runtime state."""
        return self._state

    @property
    def capabilities(self) -> RuntimeCapabilities:
        """Get the runtime capabilities."""
        return self._capabilities

    @property
    def is_running(self) -> bool:
        """Check if the runtime is running."""
        return self._state == RuntimeState.RUNNING

    @property
    def is_available(self) -> bool:
        """Check if the runtime is available (running or initialized)."""
        return self._state in (
            RuntimeState.RUNNING,
            RuntimeState.INITIALIZED,
        )

    @property
    def is_stopped(self) -> bool:
        """Check if the runtime is stopped."""
        return self._state in (
            RuntimeState.STOPPED,
            RuntimeState.UNINITIALIZED,
        )

    @property
    def message_bus(self) -> "MessageBus":
        """Get the message bus."""
        if self._message_bus is None:
            from tangku_agentos.runtime_communication import MessageBus

            self._message_bus = MessageBus()
        return self._message_bus

    @message_bus.setter
    def message_bus(self, bus: "MessageBus") -> None:
        """Set the message bus."""
        self._message_bus = bus

    @property
    def event_bus(self) -> "EventBus":
        """Get the event bus."""
        if self._event_bus is None:
            from tangku_agentos.runtime_communication import EventBus

            self._event_bus = EventBus()
        return self._event_bus

    @event_bus.setter
    def event_bus(self, bus: "EventBus") -> None:
        """Set the event bus."""
        self._event_bus = bus

    @property
    def command_bus(self) -> "CommandBus":
        """Get the command bus."""
        if self._command_bus is None:
            from tangku_agentos.runtime_communication import CommandBus

            self._command_bus = CommandBus()
        return self._command_bus

    @command_bus.setter
    def command_bus(self, bus: "CommandBus") -> None:
        """Set the command bus."""
        self._command_bus = bus

    @property
    def query_bus(self) -> "QueryBus":
        """Get the query bus."""
        if self._query_bus is None:
            from tangku_agentos.runtime_communication import QueryBus

            self._query_bus = QueryBus()
        return self._query_bus

    @query_bus.setter
    def query_bus(self, bus: "QueryBus") -> None:
        """Set the query bus."""
        self._query_bus = bus

    @property
    def broadcast_bus(self) -> "BroadcastBus":
        """Get the broadcast bus."""
        if self._broadcast_bus is None:
            from tangku_agentos.runtime_communication import BroadcastBus

            self._broadcast_bus = BroadcastBus()
        return self._broadcast_bus

    @broadcast_bus.setter
    def broadcast_bus(self, bus: "BroadcastBus") -> None:
        """Set the broadcast bus."""
        self._broadcast_bus = bus

    @property
    def request_response_bus(self) -> "RequestResponseBus":
        """Get the request/response bus."""
        if self._request_response_bus is None:
            from tangku_agentos.runtime_communication import RequestResponseBus

            self._request_response_bus = RequestResponseBus()
        return self._request_response_bus

    @request_response_bus.setter
    def request_response_bus(self, bus: "RequestResponseBus") -> None:
        """Set the request/response bus."""
        self._request_response_bus = bus

    @property
    def registry(self) -> "RuntimeRegistry":
        """Get the runtime registry."""
        if self._registry is None:
            from tangku_agentos.runtime_communication import RuntimeRegistry

            self._registry = RuntimeRegistry()
        return self._registry

    @registry.setter
    def registry(self, registry: "RuntimeRegistry") -> None:
        """Set the runtime registry."""
        self._registry = registry

    @property
    def health_service(self) -> "RuntimeHealthService":
        """Get the health service."""
        if self._health_service is None:
            from tangku_agentos.runtime_communication import RuntimeHealthService

            self._health_service = RuntimeHealthService(self.registry)
        return self._health_service

    @health_service.setter
    def health_service(self, service: "RuntimeHealthService") -> None:
        """Set the health service."""
        self._health_service = service

    @property
    def context_manager(self) -> "RuntimeContextManager":
        """Get the context manager."""
        if self._context_manager is None:
            from tangku_agentos.runtime_communication import RuntimeContextManager

            self._context_manager = RuntimeContextManager()
        return self._context_manager

    @context_manager.setter
    def context_manager(self, manager: "RuntimeContextManager") -> None:
        """Set the context manager."""
        self._context_manager = manager

    def set_buses(
        self,
        message_bus: Optional["MessageBus"] = None,
        event_bus: Optional["EventBus"] = None,
        command_bus: Optional["CommandBus"] = None,
        query_bus: Optional["QueryBus"] = None,
        broadcast_bus: Optional["BroadcastBus"] = None,
        request_response_bus: Optional["RequestResponseBus"] = None,
    ) -> None:
        """
        Set all communication buses.

        Args:
            message_bus: Message bus instance.
            event_bus: Event bus instance.
            command_bus: Command bus instance.
            query_bus: Query bus instance.
            broadcast_bus: Broadcast bus instance.
            request_response_bus: Request/response bus instance.
        """
        if message_bus is not None:
            self._message_bus = message_bus
        if event_bus is not None:
            self._event_bus = event_bus
        if command_bus is not None:
            self._command_bus = command_bus
        if query_bus is not None:
            self._query_bus = query_bus
        if broadcast_bus is not None:
            self._broadcast_bus = broadcast_bus
        if request_response_bus is not None:
            self._request_response_bus = request_response_bus

    def set_services(
        self,
        registry: Optional["RuntimeRegistry"] = None,
        health_service: Optional["RuntimeHealthService"] = None,
        context_manager: Optional["RuntimeContextManager"] = None,
    ) -> None:
        """
        Set all services.

        Args:
            registry: Runtime registry instance.
            health_service: Health service instance.
            context_manager: Context manager instance.
        """
        if registry is not None:
            self._registry = registry
        if health_service is not None:
            self._health_service = health_service
        if context_manager is not None:
            self._context_manager = context_manager

    def on_initialize(self, callback: Callable[[], None]) -> None:
        """
        Register a callback for initialization.

        Args:
            callback: Callback to call when runtime is initialized.
        """
        self._on_initialize.append(callback)

    def on_start(self, callback: Callable[[], None]) -> None:
        """
        Register a callback for start.

        Args:
            callback: Callback to call when runtime is started.
        """
        self._on_start.append(callback)

    def on_stop(self, callback: Callable[[], None]) -> None:
        """
        Register a callback for stop.

        Args:
            callback: Callback to call when runtime is stopped.
        """
        self._on_stop.append(callback)

    def on_pause(self, callback: Callable[[], None]) -> None:
        """
        Register a callback for pause.

        Args:
            callback: Callback to call when runtime is paused.
        """
        self._on_pause.append(callback)

    def on_resume(self, callback: Callable[[], None]) -> None:
        """
        Register a callback for resume.

        Args:
            callback: Callback to call when runtime is resumed.
        """
        self._on_resume.append(callback)

    def on_fail(self, callback: Callable[[Exception], None]) -> None:
        """
        Register a callback for failure.

        Args:
            callback: Callback to call when runtime fails.
        """
        self._on_fail.append(callback)

    async def initialize(self) -> None:
        """
        Initialize the runtime.

        This method should be overridden by subclasses to perform runtime-specific
        initialization. It is called automatically during startup.

        The base implementation:
        1. Sets state to INITIALIZING
        2. Calls the subclass implementation
        3. Registers the runtime with the registry
        4. Sets up health checks
        5. Sets state to INITIALIZED
        6. Calls initialization callbacks

        Raises:
            Exception: If initialization fails.
        """
        old_state = self._state
        self._set_state(RuntimeState.INITIALIZING)

        try:
            # Call subclass implementation
            await self._initialize()

            # Register with runtime registry
            await self._register()

            # Set up health checks if supported
            if self._capabilities.supports_health_checks:
                await self._setup_health_checks()

            # Set state to initialized
            self._set_state(RuntimeState.INITIALIZED)

            # Call initialization callbacks
            for callback in self._on_initialize:
                try:
                    callback()
                except Exception as e:
                    logger.error(f"Error in initialization callback: {e}")

            logger.info(f"Runtime initialized: {self._runtime_id}")

        except Exception as e:
            self._set_state(RuntimeState.FAILED)
            logger.error(f"Runtime initialization failed: {self._runtime_id}: {e}")
            raise RuntimeInitializationError(
                f"Initialization failed: {e}",
                runtime_id=self._runtime_id,
            ) from e

    async def _initialize(self) -> None:
        """
        Runtime-specific initialization.

        Subclasses should override this method to perform runtime-specific
        initialization tasks.

        Example:
            >>> class MyRuntime(BaseRuntime):
            ...     async def _initialize(self) -> None:
            ...         # Initialize runtime-specific components
            ...         self._some_component = SomeComponent()
        """
        pass  # To be overridden by subclasses

    async def start(self) -> None:
        """
        Start the runtime.

        This method should be overridden by subclasses to perform runtime-specific
        startup. It is called automatically after initialization.

        The base implementation:
        1. Sets state to STARTING
        2. Calls the subclass implementation
        3. Starts health monitoring if supported
        4. Sets state to RUNNING
        5. Publishes runtime.started event
        6. Calls start callbacks

        Raises:
            Exception: If startup fails.
        """
        old_state = self._state
        self._set_state(RuntimeState.STARTING)

        try:
            # Call subclass implementation
            await self._start()

            # Start health monitoring if supported
            if self._capabilities.supports_health_checks:
                await self._health_service.start()

            # Set state to running
            self._set_state(RuntimeState.RUNNING)

            # Publish started event
            await self._publish_started()

            # Call start callbacks
            for callback in self._on_start:
                try:
                    callback()
                except Exception as e:
                    logger.error(f"Error in start callback: {e}")

            logger.info(f"Runtime started: {self._runtime_id}")

        except Exception as e:
            self._set_state(RuntimeState.FAILED)
            logger.error(f"Runtime startup failed: {self._runtime_id}: {e}")
            raise RuntimeStartupError(
                f"Startup failed: {e}",
                runtime_id=self._runtime_id,
            ) from e

    async def _start(self) -> None:
        """
        Runtime-specific startup.

        Subclasses should override this method to perform runtime-specific
        startup tasks.

        Example:
            >>> class MyRuntime(BaseRuntime):
            ...     async def _start(self) -> None:
            ...         # Start runtime-specific components
            ...         await self._some_component.start()
        """
        pass  # To be overridden by subclasses

    async def stop(self, force: bool = False) -> None:
        """
        Stop the runtime.

        This method should be overridden by subclasses to perform runtime-specific
        shutdown. It is called automatically during shutdown.

        Args:
            force: Whether to force stop (skip graceful shutdown).

        The base implementation:
        1. Sets state to STOPPING
        2. Calls the subclass implementation
        3. Stops health monitoring if supported
        4. Unregisters the runtime
        5. Sets state to STOPPED
        6. Publishes runtime.stopped event
        7. Calls stop callbacks
        """
        old_state = self._state
        self._set_state(RuntimeState.STOPPING)

        try:
            # Call subclass implementation
            if not force:
                await self._stop()

            # Stop health monitoring if supported
            if self._capabilities.supports_health_checks:
                await self._health_service.stop()

            # Unregister from runtime registry
            await self._unregister()

            # Set state to stopped
            self._set_state(RuntimeState.STOPPED)

            # Publish stopped event
            await self._publish_stopped()

            # Call stop callbacks
            for callback in self._on_stop:
                try:
                    callback()
                except Exception as e:
                    logger.error(f"Error in stop callback: {e}")

            logger.info(f"Runtime stopped: {self._runtime_id}")

        except Exception as e:
            self._set_state(RuntimeState.FAILED)
            logger.error(f"Runtime shutdown failed: {self._runtime_id}: {e}")
            raise RuntimeShutdownError(
                f"Shutdown failed: {e}",
                runtime_id=self._runtime_id,
            ) from e

    async def _stop(self) -> None:
        """
        Runtime-specific shutdown.

        Subclasses should override this method to perform runtime-specific
        shutdown tasks.

        Example:
            >>> class MyRuntime(BaseRuntime):
            ...     async def _stop(self) -> None:
            ...         # Stop runtime-specific components
            ...         await self._some_component.stop()
        """
        pass  # To be overridden by subclasses

    async def pause(self) -> None:
        """
        Pause the runtime.

        This method should be overridden by subclasses to perform runtime-specific
        pause operations.

        The base implementation:
        1. Sets state to PAUSED
        2. Calls the subclass implementation
        3. Publishes runtime.paused event
        4. Calls pause callbacks
        """
        old_state = self._state
        self._set_state(RuntimeState.PAUSED)

        try:
            # Call subclass implementation
            await self._pause()

            # Publish paused event
            await self._publish_paused()

            # Call pause callbacks
            for callback in self._on_pause:
                try:
                    callback()
                except Exception as e:
                    logger.error(f"Error in pause callback: {e}")

            logger.info(f"Runtime paused: {self._runtime_id}")

        except Exception as e:
            # Try to restore previous state
            self._set_state(old_state)
            logger.error(f"Runtime pause failed: {self._runtime_id}: {e}")
            raise RuntimePauseError(
                f"Pause failed: {e}",
                runtime_id=self._runtime_id,
            ) from e

    async def _pause(self) -> None:
        """
        Runtime-specific pause.

        Subclasses should override this method to perform runtime-specific
        pause tasks.
        """
        pass  # To be overridden by subclasses

    async def resume(self) -> None:
        """
        Resume the runtime.

        This method should be overridden by subclasses to perform runtime-specific
        resume operations.

        The base implementation:
        1. Sets state to RUNNING
        2. Calls the subclass implementation
        3. Publishes runtime.resumed event
        4. Calls resume callbacks
        """
        old_state = self._state
        self._set_state(RuntimeState.RUNNING)

        try:
            # Call subclass implementation
            await self._resume()

            # Publish resumed event
            await self._publish_resumed()

            # Call resume callbacks
            for callback in self._on_resume:
                try:
                    callback()
                except Exception as e:
                    logger.error(f"Error in resume callback: {e}")

            logger.info(f"Runtime resumed: {self._runtime_id}")

        except Exception as e:
            # Try to restore previous state
            self._set_state(old_state)
            logger.error(f"Runtime resume failed: {self._runtime_id}: {e}")
            raise RuntimeResumeError(
                f"Resume failed: {e}",
                runtime_id=self._runtime_id,
            ) from e

    async def _resume(self) -> None:
        """
        Runtime-specific resume.

        Subclasses should override this method to perform runtime-specific
        resume tasks.
        """
        pass  # To be overridden by subclasses

    async def restart(self) -> None:
        """
        Restart the runtime.

        This performs a graceful stop followed by a start.
        """
        self._set_state(RuntimeState.RESTARTING)

        try:
            # Stop the runtime
            await self.stop()

            # Start the runtime
            await self.initialize()
            await self.start()

            logger.info(f"Runtime restarted: {self._runtime_id}")

        except Exception as e:
            self._set_state(RuntimeState.FAILED)
            logger.error(f"Runtime restart failed: {self._runtime_id}: {e}")
            raise RuntimeRestartError(
                f"Restart failed: {e}",
                runtime_id=self._runtime_id,
            ) from e

    def _set_state(self, new_state: RuntimeState) -> None:
        """
        Set the runtime state.

        Args:
            new_state: New state to set.
        """
        old_state = self._state
        self._state = new_state
        self._last_state_change = datetime.utcnow()

        # Log state change
        logger.debug(
            f"Runtime state changed: {self._runtime_id} "
            f"{old_state.name} -> {new_state.name}"
        )

    async def _register(self) -> None:
        """
        Register the runtime with the runtime registry.
        """
        try:
            self.registry.register(
                runtime_id=self._runtime_id,
                name=self._config.name or self._runtime_id,
                type=self._get_runtime_type(),
                version=self._config.version,
                description=self._config.description,
                capabilities=self._config.capabilities,
                dependencies=self._config.dependencies,
                metadata=self._config.metadata,
                auto_start=False,  # We control startup manually
            )

            # Register with health service if supported
            if self._capabilities.supports_health_checks:
                await self._register_health_checks()

            logger.debug(f"Runtime registered: {self._runtime_id}")

        except Exception as e:
            logger.error(f"Runtime registration failed: {self._runtime_id}: {e}")
            raise RuntimeRegistrationError(
                f"Registration failed: {e}",
                runtime_id=self._runtime_id,
            ) from e

    async def _unregister(self) -> None:
        """
        Unregister the runtime from the runtime registry.
        """
        try:
            self.registry.unregister(self._runtime_id)
            logger.debug(f"Runtime unregistered: {self._runtime_id}")

        except Exception as e:
            logger.error(f"Runtime unregistration failed: {self._runtime_id}: {e}")
            # Don't raise - we're shutting down anyway

    def _get_runtime_type(self) -> str:
        """
        Get the runtime type from the class name.

        Returns:
            Runtime type string.
        """
        # Extract type from class name (e.g., "MemoryRuntime" -> "memory")
        class_name = self.__class__.__name__
        if class_name.endswith("Runtime"):
            return class_name[:-7].lower()
        return class_name.lower()

    async def _register_health_checks(self) -> None:
        """
        Register health checks for the runtime.
        """
        # Subclasses can override this to register custom health checks
        pass

    async def _setup_health_checks(self) -> None:
        """
        Set up health checks for the runtime.
        """
        # Register a basic liveness check
        from tangku_agentos.runtime_communication.services.health import (
            HealthCheck,
            HealthCheckResult,
            HealthStatus,
        )

        async def liveness_check(runtime_id: str) -> HealthCheckResult:
            # Check if runtime is in a running state
            if self._state == RuntimeState.RUNNING:
                return HealthCheckResult(
                    runtime_id=runtime_id,
                    check_name="liveness",
                    status=HealthStatus.HEALTHY,
                    message="Runtime is alive",
                    passed=True,
                )
            else:
                return HealthCheckResult(
                    runtime_id=runtime_id,
                    check_name="liveness",
                    status=HealthStatus.UNHEALTHY,
                    message=f"Runtime is not running (state: {self._state.name})",
                    passed=False,
                )

        check = HealthCheck(
            name="liveness",
            description="Check if runtime is alive",
            check_func=liveness_check,
            interval=30.0,
            timeout=5.0,
            critical=True,
        )

        self.health_service.register_check(self._runtime_id, check)

    async def _publish_started(self) -> None:
        """
        Publish runtime.started event.
        """
        from tangku_agentos.runtime_communication.integration.events import SystemEvents

        event = SystemEvents.runtime_started(
            runtime_id=self._runtime_id,
            name=self._config.name,
            type=self._get_runtime_type(),
            version=self._config.version,
            timestamp=datetime.utcnow(),
        )

        try:
            await self.event_bus.publish(event)
        except Exception as e:
            logger.warning(f"Failed to publish runtime.started event: {e}")

    async def _publish_stopped(self) -> None:
        """
        Publish runtime.stopped event.
        """
        from tangku_agentos.runtime_communication.integration.events import SystemEvents

        event = SystemEvents.runtime_stopped(
            runtime_id=self._runtime_id,
            name=self._config.name,
            type=self._get_runtime_type(),
            version=self._config.version,
            timestamp=datetime.utcnow(),
        )

        try:
            await self.event_bus.publish(event)
        except Exception as e:
            logger.warning(f"Failed to publish runtime.stopped event: {e}")

    async def _publish_paused(self) -> None:
        """
        Publish runtime.paused event.
        """
        from tangku_agentos.runtime_communication.integration.events import SystemEvents

        event = SystemEvents.runtime_paused(
            runtime_id=self._runtime_id,
            name=self._config.name,
            type=self._get_runtime_type(),
            timestamp=datetime.utcnow(),
        )

        try:
            await self.event_bus.publish(event)
        except Exception as e:
            logger.warning(f"Failed to publish runtime.paused event: {e}")

    async def _publish_resumed(self) -> None:
        """
        Publish runtime.resumed event.
        """
        from tangku_agentos.runtime_communication.integration.events import SystemEvents

        event = SystemEvents.runtime_resumed(
            runtime_id=self._runtime_id,
            name=self._config.name,
            type=self._get_runtime_type(),
            timestamp=datetime.utcnow(),
        )

        try:
            await self.event_bus.publish(event)
        except Exception as e:
            logger.warning(f"Failed to publish runtime.resumed event: {e}")

    async def _publish_failed(self, error: Exception) -> None:
        """
        Publish runtime.failed event.
        """
        from tangku_agentos.runtime_communication.integration.events import SystemEvents

        event = SystemEvents.runtime_failed(
            runtime_id=self._runtime_id,
            name=self._config.name,
            type=self._get_runtime_type(),
            error=str(error),
            timestamp=datetime.utcnow(),
        )

        try:
            await self.event_bus.publish(event)
        except Exception as e:
            logger.warning(f"Failed to publish runtime.failed event: {e}")

    @abstractmethod
    async def handle_command(self, command: "Command") -> Any:
        """
        Handle an incoming command.

        Subclasses MUST implement this method to handle commands.

        Args:
            command: The command to handle.

        Returns:
            Result of command execution.

        Raises:
            Exception: If command handling fails.
        """
        pass

    @abstractmethod
    async def handle_query(self, query: "Query") -> Any:
        """
        Handle an incoming query.

        Subclasses MUST implement this method to handle queries.

        Args:
            query: The query to handle.

        Returns:
            Result of query execution.

        Raises:
            Exception: If query handling fails.
        """
        pass

    async def handle_event(self, event: "Event") -> None:
        """
        Handle an incoming event.

        Subclasses can override this method to handle events.
        The default implementation does nothing.

        Args:
            event: The event to handle.
        """
        pass  # Optional to override

    def get_metadata(self) -> Dict[str, Any]:
        """
        Get runtime metadata.

        Returns:
            Dictionary of runtime metadata.
        """
        return {
            "runtime_id": self._runtime_id,
            "name": self._config.name,
            "type": self._get_runtime_type(),
            "version": self._config.version,
            "description": self._config.description,
            "state": self._state.name,
            "created_at": self._created_at.isoformat(),
            "last_state_change": self._last_state_change.isoformat(),
            "capabilities": {
                "can_handle_commands": self._capabilities.can_handle_commands,
                "can_handle_queries": self._capabilities.can_handle_queries,
                "can_publish_events": self._capabilities.can_publish_events,
                "can_subscribe_events": self._capabilities.can_subscribe_events,
                "can_broadcast": self._capabilities.can_broadcast,
                "can_stream": self._capabilities.can_stream,
                "can_execute_tasks": self._capabilities.can_execute_tasks,
                "supports_health_checks": self._capabilities.supports_health_checks,
                "supports_metrics": self._capabilities.supports_metrics,
                "supports_tracing": self._capabilities.supports_tracing,
            },
            **self._config.metadata,
        }

    def __repr__(self) -> str:
        """Return string representation."""
        return (
            f"{self.__class__.__name__}("
            f"id={self._runtime_id}, "
            f"name={self._config.name or self._runtime_id}, "
            f"type={self._get_runtime_type()}, "
            f"state={self._state.name})"
        )


class RuntimeCommunicator:
    """
    Mixin class that provides communication methods for runtimes.

    This class can be mixed into runtime classes to provide convenient
    methods for sending messages, commands, queries, etc.

    Example:
        >>> from tangku_agentos.runtime_communication.integration.base import (
        ...     BaseRuntime,
        ...     RuntimeCommunicator,
        ... )
        >>> 
        >>> class MyRuntime(RuntimeCommunicator, BaseRuntime):
        ...     pass
        >>> 
        >>> runtime = MyRuntime(config)
        >>> await runtime.send_command("other_runtime", "DoSomething", {"param": "value"})
    """

    def __init__(self):
        """Initialize the communicator."""
        # This is a mixin, so we don't call super().__init__()
        pass

    async def send_command(
        self,
        target_runtime_id: str,
        command_type: str,
        payload: Dict[str, Any],
        timeout: Optional[float] = None,
        priority: Optional[str] = None,
        **kwargs,
    ) -> Any:
        """
        Send a command to another runtime.

        Args:
            target_runtime_id: ID of the target runtime.
            command_type: Type of command.
            payload: Command payload.
            timeout: Timeout in seconds.
            priority: Command priority.
            **kwargs: Additional command properties.

        Returns:
            Result of command execution.

        Raises:
            RuntimeNotFoundError: If target runtime is not found.
            MessageDeliveryError: If command delivery fails.
            MessageTimeoutError: If command times out.
        """
        from tangku_agentos.runtime_communication import Command, MessageType

        command = Command(
            message_type=MessageType.COMMAND,
            sender_id=self.runtime_id,
            recipient_id=target_runtime_id,
            command_type=command_type,
            payload=payload,
            timeout=timeout or self.config.timeout,
            priority=priority,
            **kwargs,
        )

        return await self.command_bus.send(command)

    async def send_query(
        self,
        target_runtime_id: str,
        query_type: str,
        payload: Dict[str, Any],
        timeout: Optional[float] = None,
        priority: Optional[str] = None,
        **kwargs,
    ) -> Any:
        """
        Send a query to another runtime.

        Args:
            target_runtime_id: ID of the target runtime.
            query_type: Type of query.
            payload: Query payload.
            timeout: Timeout in seconds.
            priority: Query priority.
            **kwargs: Additional query properties.

        Returns:
            Result of query execution.

        Raises:
            RuntimeNotFoundError: If target runtime is not found.
            MessageDeliveryError: If query delivery fails.
            MessageTimeoutError: If query times out.
        """
        from tangku_agentos.runtime_communication import Query, MessageType

        query = Query(
            message_type=MessageType.QUERY,
            sender_id=self.runtime_id,
            recipient_id=target_runtime_id,
            query_type=query_type,
            payload=payload,
            timeout=timeout or self.config.timeout,
            priority=priority,
            **kwargs,
        )

        return await self.query_bus.ask(query)

    async def publish_event(
        self,
        event_type: str,
        payload: Dict[str, Any],
        priority: Optional[str] = None,
        **kwargs,
    ) -> None:
        """
        Publish an event.

        Args:
            event_type: Type of event.
            payload: Event payload.
            priority: Event priority.
            **kwargs: Additional event properties.
        """
        from tangku_agentos.runtime_communication import Event, MessageType

        event = Event(
            message_type=MessageType.EVENT,
            sender_id=self.runtime_id,
            event_type=event_type,
            payload=payload,
            priority=priority,
            **kwargs,
        )

        await self.event_bus.publish(event)

    async def broadcast(
        self,
        broadcast_type: str,
        payload: Dict[str, Any],
        channels: Optional[List[str]] = None,
        priority: Optional[str] = None,
        **kwargs,
    ) -> int:
        """
        Broadcast a message to all subscribers.

        Args:
            broadcast_type: Type of broadcast.
            payload: Broadcast payload.
            channels: Channels to broadcast to.
            priority: Broadcast priority.
            **kwargs: Additional broadcast properties.

        Returns:
            Number of subscribers notified.
        """
        from tangku_agentos.runtime_communication import Broadcast, MessageType

        broadcast = Broadcast(
            message_type=MessageType.BROADCAST,
            sender_id=self.runtime_id,
            broadcast_type=broadcast_type,
            payload=payload,
            channels=channels,
            priority=priority,
            **kwargs,
        )

        return await self.broadcast_bus.broadcast(broadcast)

    async def request_response(
        self,
        target_runtime_id: str,
        request_type: str,
        payload: Dict[str, Any],
        timeout: Optional[float] = None,
        **kwargs,
    ) -> Any:
        """
        Send a request and wait for a response.

        Args:
            target_runtime_id: ID of the target runtime.
            request_type: Type of request.
            payload: Request payload.
            timeout: Timeout in seconds.
            **kwargs: Additional request properties.

        Returns:
            Response from the target runtime.
        """
        from tangku_agentos.runtime_communication import Message, MessageType

        request = Message(
            message_type=MessageType.QUERY,
            sender_id=self.runtime_id,
            recipient_id=target_runtime_id,
            payload={"type": request_type, **payload},
            timeout=timeout or self.config.timeout,
            **kwargs,
        )

        return await self.request_response_bus.request(request, timeout=timeout)

    async def send_message(
        self,
        target_runtime_id: str,
        message_type: MessageType,
        payload: Dict[str, Any],
        **kwargs,
    ) -> None:
        """
        Send a generic message to another runtime.

        Args:
            target_runtime_id: ID of the target runtime.
            message_type: Type of message.
            payload: Message payload.
            **kwargs: Additional message properties.
        """
        from tangku_agentos.runtime_communication import Message

        message = Message(
            message_type=message_type,
            sender_id=self.runtime_id,
            recipient_id=target_runtime_id,
            payload=payload,
            **kwargs,
        )

        await self.message_bus.send(message)


class RuntimeLifecycleManager:
    """
    Mixin class that provides lifecycle management utilities for runtimes.

    This class can be mixed into runtime classes to provide convenient
    methods for managing runtime lifecycle.

    Example:
        >>> from tangku_agentos.runtime_communication.integration.base import (
        ...     BaseRuntime,
        ...     RuntimeLifecycleManager,
        ... )
        >>> 
        >>> class MyRuntime(RuntimeLifecycleManager, BaseRuntime):
        ...     pass
        >>> 
        >>> runtime = MyRuntime(config)
        >>> await runtime.wait_for_ready()
    """

    def __init__(self):
        """Initialize the lifecycle manager."""
        # This is a mixin, so we don't call super().__init__()
        self._ready_event = asyncio.Event()
        self._stopped_event = asyncio.Event()

    async def wait_for_ready(self, timeout: Optional[float] = None) -> bool:
        """
        Wait for the runtime to be ready.

        Args:
            timeout: Timeout in seconds.

        Returns:
            True if runtime became ready, False if timeout occurred.
        """
        try:
            await asyncio.wait_for(
                self._ready_event.wait(),
                timeout=timeout,
            )
            return True
        except asyncio.TimeoutError:
            return False

    async def wait_for_stopped(self, timeout: Optional[float] = None) -> bool:
        """
        Wait for the runtime to be stopped.

        Args:
            timeout: Timeout in seconds.

        Returns:
            True if runtime stopped, False if timeout occurred.
        """
        try:
            await asyncio.wait_for(
                self._stopped_event.wait(),
                timeout=timeout,
            )
            return True
        except asyncio.TimeoutError:
            return False

    def mark_ready(self) -> None:
        """Mark the runtime as ready."""
        self._ready_event.set()

    def mark_stopped(self) -> None:
        """Mark the runtime as stopped."""
        self._stopped_event.set()

    def reset_ready(self) -> None:
        """Reset the ready event."""
        self._ready_event.clear()

    def reset_stopped(self) -> None:
        """Reset the stopped event."""
        self._stopped_event.clear()


# Custom Exceptions


class RuntimeError(Exception):
    """Base exception for runtime errors."""

    def __init__(
        self,
        message: str,
        runtime_id: str,
        code: Optional[str] = None,
    ):
        """
        Initialize the exception.

        Args:
            message: Error message.
            runtime_id: ID of the runtime.
            code: Error code.
        """
        super().__init__(message)
        self.runtime_id = runtime_id
        self.code = code
        self.timestamp = datetime.utcnow()


class RuntimeInitializationError(RuntimeError):
    """Exception raised when runtime initialization fails."""

    pass


class RuntimeStartupError(RuntimeError):
    """Exception raised when runtime startup fails."""

    pass


class RuntimeShutdownError(RuntimeError):
    """Exception raised when runtime shutdown fails."""

    pass


class RuntimePauseError(RuntimeError):
    """Exception raised when runtime pause fails."""

    pass


class RuntimeResumeError(RuntimeError):
    """Exception raised when runtime resume fails."""

    pass


class RuntimeRestartError(RuntimeError):
    """Exception raised when runtime restart fails."""

    pass


class RuntimeRegistrationError(RuntimeError):
    """Exception raised when runtime registration fails."""

    pass
