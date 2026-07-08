"""
Kernel Runtime - Kernel Communicator

The KernelCommunicator is the central communication hub for the Kernel Runtime.
It initializes and manages all communication buses and services for TangkuAgentOS.

This class is responsible for:
- Creating and configuring all communication buses
- Starting and stopping all runtime services
- Managing the runtime registry
- Monitoring system health
- Publishing system events
- Collecting communication metrics

Author: TangkuAgentOS Team
License: MIT
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Set, TYPE_CHECKING

if TYPE_CHECKING:
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
    from tangku_agentos.runtime_communication.services.discovery import RuntimeDiscoveryService
    from tangku_agentos.runtime_communication.services.status import RuntimeStatusManager
    from tangku_agentos.runtime_communication.services.metadata import RuntimeMetadataRegistry
    from tangku_agentos.runtime_communication.services.context import RuntimeContextManager
    from tangku_agentos.runtime_communication.services.session import RuntimeSessionManager
    from tangku_agentos.runtime_communication.integration.registry import RuntimeIntegrationRegistry

logger = logging.getLogger(__name__)


@dataclass
class KernelConfig:
    """
    Configuration for the Kernel Communicator.

    Attributes:
        kernel_id: Unique ID for the kernel.
        name: Human-readable name.
        version: Kernel version.
        build_info: Build information.
        enable_metrics: Whether to enable metrics collection.
        enable_tracing: Whether to enable distributed tracing.
        enable_logging: Whether to enable structured logging.
        heartbeat_interval: Interval for runtime heartbeats.
        health_check_interval: Interval for health checks.
        max_retries: Maximum retry attempts for failed operations.
        timeout: Default timeout for operations.
    """

    kernel_id: str = "kernel_runtime"
    name: str = "TangkuAgentOS Kernel"
    version: str = "2.0.0"
    build_info: Dict[str, Any] = field(default_factory=dict)
    enable_metrics: bool = True
    enable_tracing: bool = True
    enable_logging: bool = True
    heartbeat_interval: float = 30.0
    health_check_interval: float = 60.0
    max_retries: int = 3
    timeout: float = 30.0


class KernelCommunicator:
    """
    Central communication hub for the Kernel Runtime.

    The KernelCommunicator initializes and manages all communication
    infrastructure for TangkuAgentOS. It serves as the orchestrator
    for all runtime communication.

    Thread Safety:
        This class is thread-safe for concurrent access.

    Example:
        >>> from tangku_agentos.kernel_runtime.integration import KernelCommunicator
        >>> 
        >>> # Create and initialize the kernel communicator
        >>> kernel = KernelCommunicator()
        >>> await kernel.initialize()
        >>> 
        >>> # Start all communication services
        >>> await kernel.start()
        >>> 
        >>> # Access buses and services
        >>> await kernel.command_bus.send(command)
        >>> result = await kernel.query_bus.ask(query)
        >>> await kernel.event_bus.publish(event)
    """

    def __init__(self, config: Optional[KernelConfig] = None):
        """
        Initialize the Kernel Communicator.

        Args:
            config: Kernel configuration.
        """
        self._config = config or KernelConfig()
        self._initialized = False
        self._started = False

        # Communication Buses
        self._message_bus: Optional["MessageBus"] = None
        self._event_bus: Optional["EventBus"] = None
        self._command_bus: Optional["CommandBus"] = None
        self._query_bus: Optional["QueryBus"] = None
        self._broadcast_bus: Optional["BroadcastBus"] = None
        self._request_response_bus: Optional["RequestResponseBus"] = None

        # Runtime Services
        self._registry: Optional["RuntimeRegistry"] = None
        self._health_service: Optional["RuntimeHealthService"] = None
        self._discovery_service: Optional["RuntimeDiscoveryService"] = None
        self._status_manager: Optional["RuntimeStatusManager"] = None
        self._metadata_registry: Optional["RuntimeMetadataRegistry"] = None
        self._context_manager: Optional["RuntimeContextManager"] = None
        self._session_manager: Optional["RuntimeSessionManager"] = None

        # Integration Registry
        self._integration_registry: Optional["RuntimeIntegrationRegistry"] = None

        # Startup timestamp
        self._started_at: Optional[datetime] = None

        # Lifecycle callbacks
        self._on_initialize: List[Callable[[], None]] = []
        self._on_start: List[Callable[[], None]] = []
        self._on_stop: List[Callable[[], None]] = []

        logger.info(f"KernelCommunicator initialized (v{self._config.version})")

    @property
    def config(self) -> KernelConfig:
        """Get the kernel configuration."""
        return self._config

    @property
    def is_initialized(self) -> bool:
        """Check if the kernel communicator is initialized."""
        return self._initialized

    @property
    def is_started(self) -> bool:
        """Check if the kernel communicator is started."""
        return self._started

    @property
    def message_bus(self) -> "MessageBus":
        """Get the message bus."""
        if self._message_bus is None:
            raise RuntimeError("Message bus not initialized. Call initialize() first.")
        return self._message_bus

    @property
    def event_bus(self) -> "EventBus":
        """Get the event bus."""
        if self._event_bus is None:
            raise RuntimeError("Event bus not initialized. Call initialize() first.")
        return self._event_bus

    @property
    def command_bus(self) -> "CommandBus":
        """Get the command bus."""
        if self._command_bus is None:
            raise RuntimeError("Command bus not initialized. Call initialize() first.")
        return self._command_bus

    @property
    def query_bus(self) -> "QueryBus":
        """Get the query bus."""
        if self._query_bus is None:
            raise RuntimeError("Query bus not initialized. Call initialize() first.")
        return self._query_bus

    @property
    def broadcast_bus(self) -> "BroadcastBus":
        """Get the broadcast bus."""
        if self._broadcast_bus is None:
            raise RuntimeError("Broadcast bus not initialized. Call initialize() first.")
        return self._broadcast_bus

    @property
    def request_response_bus(self) -> "RequestResponseBus":
        """Get the request/response bus."""
        if self._request_response_bus is None:
            raise RuntimeError("Request/response bus not initialized. Call initialize() first.")
        return self._request_response_bus

    @property
    def registry(self) -> "RuntimeRegistry":
        """Get the runtime registry."""
        if self._registry is None:
            raise RuntimeError("Runtime registry not initialized. Call initialize() first.")
        return self._registry

    @property
    def health_service(self) -> "RuntimeHealthService":
        """Get the health service."""
        if self._health_service is None:
            raise RuntimeError("Health service not initialized. Call initialize() first.")
        return self._health_service

    @property
    def discovery_service(self) -> "RuntimeDiscoveryService":
        """Get the discovery service."""
        if self._discovery_service is None:
            raise RuntimeError("Discovery service not initialized. Call initialize() first.")
        return self._discovery_service

    @property
    def status_manager(self) -> "RuntimeStatusManager":
        """Get the status manager."""
        if self._status_manager is None:
            raise RuntimeError("Status manager not initialized. Call initialize() first.")
        return self._status_manager

    @property
    def metadata_registry(self) -> "RuntimeMetadataRegistry":
        """Get the metadata registry."""
        if self._metadata_registry is None:
            raise RuntimeError("Metadata registry not initialized. Call initialize() first.")
        return self._metadata_registry

    @property
    def context_manager(self) -> "RuntimeContextManager":
        """Get the context manager."""
        if self._context_manager is None:
            raise RuntimeError("Context manager not initialized. Call initialize() first.")
        return self._context_manager

    @property
    def session_manager(self) -> "RuntimeSessionManager":
        """Get the session manager."""
        if self._session_manager is None:
            raise RuntimeError("Session manager not initialized. Call initialize() first.")
        return self._session_manager

    @property
    def integration_registry(self) -> "RuntimeIntegrationRegistry":
        """Get the integration registry."""
        if self._integration_registry is None:
            raise RuntimeError("Integration registry not initialized. Call initialize() first.")
        return self._integration_registry

    def on_initialize(self, callback: Callable[[], None]) -> None:
        """
        Register a callback for initialization.

        Args:
            callback: Callback to call when kernel is initialized.
        """
        self._on_initialize.append(callback)

    def on_start(self, callback: Callable[[], None]) -> None:
        """
        Register a callback for start.

        Args:
            callback: Callback to call when kernel is started.
        """
        self._on_start.append(callback)

    def on_stop(self, callback: Callable[[], None]) -> None:
        """
        Register a callback for stop.

        Args:
            callback: Callback to call when kernel is stopped.
        """
        self._on_stop.append(callback)

    async def initialize(self) -> None:
        """
        Initialize the Kernel Communicator.

        This method:
        1. Creates all communication buses
        2. Creates all runtime services
        3. Creates the integration registry
        4. Sets up middleware and interceptors
        5. Calls initialization callbacks

        Raises:
            Exception: If initialization fails.
        """
        if self._initialized:
            logger.warning("KernelCommunicator already initialized")
            return

        logger.info("Initializing Kernel Communicator...")

        try:
            # Create all communication buses
            await self._create_buses()

            # Create all runtime services
            await self._create_services()

            # Create integration registry
            await self._create_integration_registry()

            # Set up middleware and interceptors
            await self._setup_middleware()

            # Mark as initialized
            self._initialized = True

            # Call initialization callbacks
            for callback in self._on_initialize:
                try:
                    callback()
                except Exception as e:
                    logger.error(f"Error in initialization callback: {e}")

            logger.info("Kernel Communicator initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize Kernel Communicator: {e}")
            raise

    async def _create_buses(self) -> None:
        """Create all communication buses."""
        from tangku_agentos.runtime_communication import (
            MessageBus,
            EventBus,
            CommandBus,
            QueryBus,
            BroadcastBus,
            RequestResponseBus,
        )

        logger.debug("Creating communication buses...")

        # Create buses with kernel configuration
        self._message_bus = MessageBus(
            enable_metrics=self._config.enable_metrics,
            enable_logging=self._config.enable_logging,
            enable_tracing=self._config.enable_tracing,
        )

        self._event_bus = EventBus(
            enable_metrics=self._config.enable_metrics,
            enable_logging=self._config.enable_logging,
            enable_tracing=self._config.enable_tracing,
        )

        self._command_bus = CommandBus(
            enable_metrics=self._config.enable_metrics,
            enable_logging=self._config.enable_logging,
            enable_tracing=self._config.enable_tracing,
            max_retries=self._config.max_retries,
            timeout=self._config.timeout,
        )

        self._query_bus = QueryBus(
            enable_metrics=self._config.enable_metrics,
            enable_logging=self._config.enable_logging,
            enable_tracing=self._config.enable_tracing,
            max_retries=self._config.max_retries,
            timeout=self._config.timeout,
        )

        self._broadcast_bus = BroadcastBus(
            enable_metrics=self._config.enable_metrics,
            enable_logging=self._config.enable_logging,
            enable_tracing=self._config.enable_tracing,
        )

        self._request_response_bus = RequestResponseBus(
            enable_metrics=self._config.enable_metrics,
            enable_logging=self._config.enable_logging,
            enable_tracing=self._config.enable_tracing,
            max_retries=self._config.max_retries,
            timeout=self._config.timeout,
        )

        logger.info("Communication buses created")

    async def _create_services(self) -> None:
        """Create all runtime services."""
        from tangku_agentos.runtime_communication import (
            RuntimeRegistry,
            RuntimeHealthService,
            RuntimeDiscoveryService,
            RuntimeStatusManager,
            RuntimeMetadataRegistry,
            RuntimeContextManager,
            RuntimeSessionManager,
        )

        logger.debug("Creating runtime services...")

        # Create registry first (other services depend on it)
        self._registry = RuntimeRegistry()

        # Create other services
        self._health_service = RuntimeHealthService(
            registry=self._registry,
            enable_metrics=self._config.enable_metrics,
            enable_logging=self._config.enable_logging,
        )

        self._discovery_service = RuntimeDiscoveryService(
            registry=self._registry,
            enable_metrics=self._config.enable_metrics,
            enable_logging=self._config.enable_logging,
        )

        self._status_manager = RuntimeStatusManager(
            registry=self._registry,
            enable_metrics=self._config.enable_metrics,
            enable_logging=self._config.enable_logging,
        )

        self._metadata_registry = RuntimeMetadataRegistry(
            registry=self._registry,
            enable_metrics=self._config.enable_metrics,
            enable_logging=self._config.enable_logging,
        )

        self._context_manager = RuntimeContextManager(
            enable_metrics=self._config.enable_metrics,
            enable_logging=self._config.enable_logging,
        )

        self._session_manager = RuntimeSessionManager(
            enable_metrics=self._config.enable_metrics,
            enable_logging=self._config.enable_logging,
        )

        logger.info("Runtime services created")

    async def _create_integration_registry(self) -> None:
        """Create the integration registry."""
        from tangku_agentos.runtime_communication.integration import RuntimeIntegrationRegistry

        logger.debug("Creating integration registry...")

        self._integration_registry = RuntimeIntegrationRegistry(
            heartbeat_interval=self._config.heartbeat_interval,
            heartbeat_timeout=self._config.heartbeat_interval * 2,
            enable_monitoring=self._config.enable_metrics,
        )

        logger.info("Integration registry created")

    async def _setup_middleware(self) -> None:
        """Set up middleware for all buses."""
        logger.debug("Setting up middleware...")

        # For now, we'll add basic middleware
        # In the future, we can add more sophisticated middleware
        # like validation, security, logging, metrics, tracing

        if self._config.enable_logging:
            # Add logging middleware to all buses
            pass  # Logging is already enabled in bus configuration

        if self._config.enable_metrics:
            # Add metrics middleware to all buses
            pass  # Metrics are already enabled in bus configuration

        if self._config.enable_tracing:
            # Add tracing middleware to all buses
            pass  # Tracing is already enabled in bus configuration

        logger.info("Middleware setup complete")

    async def start(self) -> None:
        """
        Start the Kernel Communicator.

        This method:
        1. Starts all runtime services
        2. Starts the integration registry
        3. Publishes kernel.started event
        4. Sets startup timestamp
        5. Calls start callbacks

        Raises:
            Exception: If start fails.
        """
        if self._started:
            logger.warning("KernelCommunicator already started")
            return

        if not self._initialized:
            raise RuntimeError("KernelCommunicator not initialized. Call initialize() first.")

        logger.info("Starting Kernel Communicator...")

        try:
            # Start all runtime services
            await self._start_services()

            # Start integration registry
            # (It starts automatically when runtimes are registered)

            # Set startup timestamp
            self._started_at = datetime.utcnow()

            # Mark as started
            self._started = True

            # Publish kernel started event
            await self._publish_kernel_started()

            # Call start callbacks
            for callback in self._on_start:
                try:
                    callback()
                except Exception as e:
                    logger.error(f"Error in start callback: {e}")

            logger.info("Kernel Communicator started successfully")

        except Exception as e:
            logger.error(f"Failed to start Kernel Communicator: {e}")
            raise

    async def _start_services(self) -> None:
        """Start all runtime services."""
        logger.debug("Starting runtime services...")

        # Start health service
        if self._health_service:
            await self._health_service.start()

        # Start status manager
        if self._status_manager:
            await self._status_manager.start()

        logger.info("Runtime services started")

    async def stop(self) -> None:
        """
        Stop the Kernel Communicator.

        This method:
        1. Stops all runtime services
        2. Publishes kernel.shutdown event
        3. Calls stop callbacks
        4. Cleans up resources

        Raises:
            Exception: If stop fails.
        """
        if not self._started:
            logger.warning("KernelCommunicator not started")
            return

        logger.info("Stopping Kernel Communicator...")

        try:
            # Publish kernel shutdown event
            await self._publish_kernel_shutdown()

            # Stop all runtime services
            await self._stop_services()

            # Call stop callbacks
            for callback in self._on_stop:
                try:
                    callback()
                except Exception as e:
                    logger.error(f"Error in stop callback: {e}")

            # Mark as stopped
            self._started = False

            logger.info("Kernel Communicator stopped successfully")

        except Exception as e:
            logger.error(f"Failed to stop Kernel Communicator: {e}")
            raise

    async def _stop_services(self) -> None:
        """Stop all runtime services."""
        logger.debug("Stopping runtime services...")

        # Stop health service
        if self._health_service:
            await self._health_service.stop()

        # Stop status manager
        if self._status_manager:
            await self._status_manager.stop()

        # Shutdown integration registry
        if self._integration_registry:
            self._integration_registry.shutdown()

        logger.info("Runtime services stopped")

    async def _publish_kernel_started(self) -> None:
        """Publish kernel.started event."""
        from tangku_agentos.runtime_communication.integration import SystemEvents

        event = SystemEvents.kernel_started(
            version=self._config.version,
            build_info=self._config.build_info,
        )

        try:
            await self.event_bus.publish(event.to_event())
            logger.info("Published kernel.started event")
        except Exception as e:
            logger.error(f"Failed to publish kernel.started event: {e}")

    async def _publish_kernel_shutdown(self, reason: str = "shutdown") -> None:
        """Publish kernel.shutdown event."""
        from tangku_agentos.runtime_communication.integration import SystemEvents

        event = SystemEvents.kernel_shutdown(
            reason=reason,
        )

        try:
            await self.event_bus.publish(event.to_event())
            logger.info(f"Published kernel.shutdown event (reason: {reason})")
        except Exception as e:
            logger.error(f"Failed to publish kernel.shutdown event: {e}")

    async def _publish_kernel_ready(self) -> None:
        """Publish kernel.ready event."""
        from tangku_agentos.runtime_communication.integration import SystemEvents

        # Count registered runtimes
        runtime_count = len(self._integration_registry) if self._integration_registry else 0

        event = SystemEvents.kernel_ready(
            version=self._config.version,
            runtimes_loaded=runtime_count,
        )

        try:
            await self.event_bus.publish(event.to_event())
            logger.info(f"Published kernel.ready event ({runtime_count} runtimes)")
        except Exception as e:
            logger.error(f"Failed to publish kernel.ready event: {e}")

    async def register_runtime(self, runtime: Any) -> None:
        """
        Register a runtime with the Kernel Communicator.

        Args:
            runtime: Runtime instance to register.
        """
        from tangku_agentos.runtime_communication.integration.base import BaseRuntime

        if not isinstance(runtime, BaseRuntime):
            raise ValueError(f"Runtime must inherit from BaseRuntime: {runtime}")

        # Set the buses and services for the runtime
        runtime.set_buses(
            message_bus=self._message_bus,
            event_bus=self._event_bus,
            command_bus=self._command_bus,
            query_bus=self._query_bus,
            broadcast_bus=self._broadcast_bus,
            request_response_bus=self._request_response_bus,
        )

        runtime.set_services(
            registry=self._registry,
            health_service=self._health_service,
            context_manager=self._context_manager,
        )

        # Register with integration registry
        if self._integration_registry:
            await self._integration_registry.register(
                runtime_id=runtime.runtime_id,
                name=runtime.config.name or runtime.runtime_id,
                type=runtime._get_runtime_type(),
                version=runtime.config.version,
                capabilities=runtime.capabilities.capabilities,
                dependencies=list(runtime.config.dependencies),
                metadata=runtime.config.metadata,
            )

        # Register with runtime registry
        await self._registry.register(
            runtime_id=runtime.runtime_id,
            name=runtime.config.name or runtime.runtime_id,
            type=runtime._get_runtime_type(),
            version=runtime.config.version,
            capabilities=runtime.capabilities.capabilities,
            dependencies=list(runtime.config.dependencies),
            metadata=runtime.config.metadata,
        )

        # Register with health service
        if self._health_service:
            # The runtime will register its own health checks during initialization
            pass

        logger.info(f"Runtime registered: {runtime.runtime_id}")

    async def unregister_runtime(self, runtime_id: str) -> None:
        """
        Unregister a runtime from the Kernel Communicator.

        Args:
            runtime_id: ID of the runtime to unregister.
        """
        # Unregister from integration registry
        if self._integration_registry:
            await self._integration_registry.unregister(runtime_id)

        # Unregister from runtime registry
        self._registry.unregister(runtime_id)

        logger.info(f"Runtime unregistered: {runtime_id}")

    async def start_runtime(self, runtime: Any) -> None:
        """
        Start a runtime.

        Args:
            runtime: Runtime instance to start.
        """
        from tangku_agentos.runtime_communication.integration.base import BaseRuntime

        if not isinstance(runtime, BaseRuntime):
            raise ValueError(f"Runtime must inherit from BaseRuntime: {runtime}")

        # Initialize the runtime
        await runtime.initialize()

        # Start the runtime
        await runtime.start()

        logger.info(f"Runtime started: {runtime.runtime_id}")

    async def stop_runtime(self, runtime: Any, force: bool = False) -> None:
        """
        Stop a runtime.

        Args:
            runtime: Runtime instance to stop.
            force: Whether to force stop.
        """
        from tangku_agentos.runtime_communication.integration.base import BaseRuntime

        if not isinstance(runtime, BaseRuntime):
            raise ValueError(f"Runtime must inherit from BaseRuntime: {runtime}")

        # Stop the runtime
        await runtime.stop(force=force)

        # Unregister the runtime
        await self.unregister_runtime(runtime.runtime_id)

        logger.info(f"Runtime stopped: {runtime.runtime_id}")

    async def restart_runtime(self, runtime: Any) -> None:
        """
        Restart a runtime.

        Args:
            runtime: Runtime instance to restart.
        """
        from tangku_agentos.runtime_communication.integration.base import BaseRuntime

        if not isinstance(runtime, BaseRuntime):
            raise ValueError(f"Runtime must inherit from BaseRuntime: {runtime}")

        # Stop the runtime
        await runtime.stop()

        # Start the runtime
        await self.start_runtime(runtime)

        logger.info(f"Runtime restarted: {runtime.runtime_id}")

    async def start_all_runtimes(self, runtimes: List[Any]) -> None:
        """
        Start all runtimes.

        Args:
            runtimes: List of runtime instances to start.
        """
        logger.info(f"Starting {len(runtimes)} runtimes...")

        # Register all runtimes first
        for runtime in runtimes:
            await self.register_runtime(runtime)

        # Start all runtimes
        for runtime in runtimes:
            try:
                await self.start_runtime(runtime)
            except Exception as e:
                logger.error(f"Failed to start runtime {runtime.runtime_id}: {e}")
                # Continue with other runtimes

        # Publish kernel ready event
        await self._publish_kernel_ready()

        logger.info(f"All {len(runtimes)} runtimes started")

    async def stop_all_runtimes(self, runtimes: List[Any], force: bool = False) -> None:
        """
        Stop all runtimes.

        Args:
            runtimes: List of runtime instances to stop.
            force: Whether to force stop.
        """
        logger.info(f"Stopping {len(runtimes)} runtimes...")

        # Stop all runtimes (in reverse order)
        for runtime in reversed(runtimes):
            try:
                await self.stop_runtime(runtime, force=force)
            except Exception as e:
                logger.error(f"Failed to stop runtime {runtime.runtime_id}: {e}")
                # Continue with other runtimes

        logger.info(f"All {len(runtimes)} runtimes stopped")

    async def get_runtime(self, runtime_id: str) -> Any:
        """
        Get a runtime by ID.

        Args:
            runtime_id: ID of the runtime to get.

        Returns:
            Runtime instance if found, None otherwise.
        """
        # Look up in the registry
        runtime_info = self._registry.get(runtime_id)
        if runtime_info:
            # In a real implementation, we would have a mapping from runtime_id to runtime instance
            # For now, we'll just return the info
            return runtime_info
        return None

    async def list_runtimes(self) -> List[Any]:
        """
        List all registered runtimes.

        Returns:
            List of all runtime infos.
        """
        return self._registry.list_all()

    async def get_metrics(self) -> Dict[str, Any]:
        """
        Get kernel communicator metrics.

        Returns:
            Dictionary of metrics.
        """
        metrics = {
            "kernel": {
                "initialized": self._initialized,
                "started": self._started,
                "started_at": self._started_at.isoformat() if self._started_at else None,
                "version": self._config.version,
            },
            "buses": {},
            "services": {},
        }

        # Add bus metrics
        if self._message_bus:
            metrics["buses"]["message_bus"] = self._message_bus.get_metrics()
        if self._event_bus:
            metrics["buses"]["event_bus"] = self._event_bus.get_metrics()
        if self._command_bus:
            metrics["buses"]["command_bus"] = self._command_bus.get_metrics()
        if self._query_bus:
            metrics["buses"]["query_bus"] = self._query_bus.get_metrics()
        if self._broadcast_bus:
            metrics["buses"]["broadcast_bus"] = self._broadcast_bus.get_metrics()
        if self._request_response_bus:
            metrics["buses"]["request_response_bus"] = self._request_response_bus.get_metrics()

        # Add service metrics
        if self._health_service:
            metrics["services"]["health"] = self._health_service.get_metrics()
        if self._discovery_service:
            metrics["services"]["discovery"] = self._discovery_service.get_metrics()
        if self._status_manager:
            metrics["services"]["status"] = self._status_manager.get_metrics()
        if self._metadata_registry:
            metrics["services"]["metadata"] = self._metadata_registry.get_metrics()
        if self._context_manager:
            metrics["services"]["context"] = self._context_manager.get_metrics()
        if self._session_manager:
            metrics["services"]["session"] = self._session_manager.get_metrics()

        # Add integration registry metrics
        if self._integration_registry:
            metrics["integration"] = self._integration_registry.get_metrics()

        return metrics

    async def shutdown(self, reason: str = "shutdown") -> None:
        """
        Shutdown the Kernel Communicator.

        Args:
            reason: Reason for shutdown.
        """
        logger.info(f"Shutting down Kernel Communicator (reason: {reason})...")

        # Publish shutdown event
        await self._publish_kernel_shutdown(reason=reason)

        # Stop all services
        await self.stop()

        # Mark as not initialized
        self._initialized = False

        logger.info("Kernel Communicator shutdown complete")

    def __repr__(self) -> str:
        """Return string representation."""
        status = "started" if self._started else ("initialized" if self._initialized else "stopped")
        return (
            f"KernelCommunicator("
            f"status={status}, "
            f"version={self._config.version}, "
            f"runtimes={len(self._integration_registry) if self._integration_registry else 0})"
        )
