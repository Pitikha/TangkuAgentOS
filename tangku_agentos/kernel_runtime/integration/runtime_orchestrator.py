"""
Kernel Runtime - Runtime Orchestrator

The RuntimeOrchestrator is the highest-level component in the Kernel Runtime
that orchestrates the entire TangkuAgentOS system. It provides a unified
interface for starting, stopping, and managing all runtimes.

This class is responsible for:
- Initializing the entire system
- Starting all runtimes in the correct order
- Monitoring system health
- Handling runtime failures
- Performing graceful shutdown
- Providing system-level APIs

Author: TangkuAgentOS Team
License: MIT
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional, Set, TYPE_CHECKING, Union

if TYPE_CHECKING:
    from tangku_agentos.kernel_runtime.integration.kernel_communicator import KernelCommunicator
    from tangku_agentos.kernel_runtime.integration.kernel_manager import KernelRuntimeManager
    from tangku_agentos.runtime_communication.integration.base import BaseRuntime

logger = logging.getLogger(__name__)


@dataclass
class OrchestratorConfig:
    """
    Configuration for the Runtime Orchestrator.

    Attributes:
        startup_timeout: Timeout for system startup.
        shutdown_timeout: Timeout for system shutdown.
        runtime_startup_timeout: Timeout for individual runtime startup.
        runtime_shutdown_timeout: Timeout for individual runtime shutdown.
        health_check_interval: Interval for system health checks.
        auto_recover: Whether to automatically recover failed runtimes.
        max_concurrent_starts: Maximum concurrent runtime starts.
    """

    startup_timeout: float = 120.0
    shutdown_timeout: float = 60.0
    runtime_startup_timeout: float = 30.0
    runtime_shutdown_timeout: float = 30.0
    health_check_interval: float = 60.0
    auto_recover: bool = True
    max_concurrent_starts: int = 10


class RuntimeOrchestrator:
    """
    Orchestrator for all TangkuAgentOS runtimes.

    The RuntimeOrchestrator provides a unified interface for managing
    the entire TangkuAgentOS system. It coordinates the startup and
    shutdown of all runtimes and provides system-level monitoring.

    Thread Safety:
        This class is thread-safe for concurrent access.

    Example:
        >>> from tangku_agentos.kernel_runtime.integration import RuntimeOrchestrator
        >>> 
        >>> # Create and start the orchestrator
        >>> orchestrator = RuntimeOrchestrator()
        >>> await orchestrator.initialize()
        >>> await orchestrator.start()
        >>> 
        >>> # The system is now running
        >>> 
        >>> # Stop the system
        >>> await orchestrator.stop()
    """

    def __init__(
        self,
        communicator: Optional["KernelCommunicator"] = None,
        manager: Optional["KernelRuntimeManager"] = None,
        config: Optional[OrchestratorConfig] = None,
    ):
        """
        Initialize the Runtime Orchestrator.

        Args:
            communicator: KernelCommunicator instance.
            manager: KernelRuntimeManager instance.
            config: Orchestrator configuration.
        """
        self._communicator = communicator
        self._manager = manager
        self._config = config or OrchestratorConfig()
        self._initialized = False
        self._started = False

        # Runtime startup tracking
        self._startup_tasks: Dict[str, asyncio.Task] = {}
        self._startup_lock = asyncio.Lock()

        # Runtime shutdown tracking
        self._shutdown_tasks: Dict[str, asyncio.Task] = {}
        self._shutdown_lock = asyncio.Lock()

        # System health tracking
        self._system_health: Dict[str, Any] = {}
        self._health_lock = asyncio.Lock()

        # Lifecycle callbacks
        self._on_initialize: List[Callable[[], None]] = []
        self._on_start: List[Callable[[], None]] = []
        self._on_stop: List[Callable[[], None]] = []
        self._on_system_ready: List[Callable[[], None]] = []
        self._on_system_shutdown: List[Callable[[str], None]] = []

        # Startup timestamp
        self._started_at: Optional[datetime] = None

        logger.info("RuntimeOrchestrator initialized")

    @property
    def communicator(self) -> "KernelCommunicator":
        """Get the kernel communicator."""
        if self._communicator is None:
            from tangku_agentos.kernel_runtime.integration import KernelCommunicator

            self._communicator = KernelCommunicator()
        return self._communicator

    @communicator.setter
    def communicator(self, value: "KernelCommunicator") -> None:
        """Set the kernel communicator."""
        self._communicator = value

    @property
    def manager(self) -> "KernelRuntimeManager":
        """Get the kernel runtime manager."""
        if self._manager is None:
            from tangku_agentos.kernel_runtime.integration import KernelRuntimeManager

            self._manager = KernelRuntimeManager(communicator=self._communicator)
        return self._manager

    @manager.setter
    def manager(self, value: "KernelRuntimeManager") -> None:
        """Set the kernel runtime manager."""
        self._manager = value

    @property
    def config(self) -> OrchestratorConfig:
        """Get the orchestrator configuration."""
        return self._config

    @property
    def is_initialized(self) -> bool:
        """Check if the orchestrator is initialized."""
        return self._initialized

    @property
    def is_started(self) -> bool:
        """Check if the orchestrator is started."""
        return self._started

    @property
    def is_ready(self) -> bool:
        """Check if the system is ready."""
        return self._started and self._all_runtimes_ready()

    def on_initialize(self, callback: Callable[[], None]) -> None:
        """
        Register a callback for initialization.

        Args:
            callback: Callback to call when orchestrator is initialized.
        """
        self._on_initialize.append(callback)

    def on_start(self, callback: Callable[[], None]) -> None:
        """
        Register a callback for start.

        Args:
            callback: Callback to call when orchestrator is started.
        """
        self._on_start.append(callback)

    def on_stop(self, callback: Callable[[], None]) -> None:
        """
        Register a callback for stop.

        Args:
            callback: Callback to call when orchestrator is stopped.
        """
        self._on_stop.append(callback)

    def on_system_ready(self, callback: Callable[[], None]) -> None:
        """
        Register a callback for system ready.

        Args:
            callback: Callback to call when system is ready.
        """
        self._on_system_ready.append(callback)

    def on_system_shutdown(self, callback: Callable[[str], None]) -> None:
        """
        Register a callback for system shutdown.

        Args:
            callback: Callback to call when system shuts down.
        """
        self._on_system_shutdown.append(callback)

    async def initialize(self) -> None:
        """
        Initialize the Runtime Orchestrator.

        This method:
        1. Initializes the KernelCommunicator
        2. Initializes the KernelRuntimeManager
        3. Sets up system monitoring
        4. Calls initialization callbacks

        Raises:
            Exception: If initialization fails.
        """
        if self._initialized:
            logger.warning("RuntimeOrchestrator already initialized")
            return

        logger.info("Initializing Runtime Orchestrator...")

        try:
            # Initialize the communicator
            await self.communicator.initialize()

            # Initialize the manager
            self._manager = KernelRuntimeManager(
                communicator=self.communicator,
                config=self._config,
            )
            await self._manager.initialize()

            # Set up system monitoring
            await self._setup_monitoring()

            # Mark as initialized
            self._initialized = True

            # Call initialization callbacks
            for callback in self._on_initialize:
                try:
                    callback()
                except Exception as e:
                    logger.error(f"Error in initialization callback: {e}")

            logger.info("Runtime Orchestrator initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize Runtime Orchestrator: {e}")
            raise

    async def _setup_monitoring(self) -> None:
        """Set up system monitoring."""
        logger.debug("Setting up system monitoring...")

        # Set up health monitoring
        if self._config.health_check_interval > 0:
            self._health_monitor_task = asyncio.create_task(
                self._health_monitor_loop()
            )

        logger.info("System monitoring setup complete")

    async def _health_monitor_loop(self) -> None:
        """Background health monitoring loop."""
        while True:
            try:
                await asyncio.sleep(self._config.health_check_interval)
                await self._check_system_health()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in health monitor loop: {e}")

    async def _check_system_health(self) -> None:
        """Check the health of the entire system."""
        async with self._health_lock:
            self._system_health = {
                "timestamp": datetime.utcnow().isoformat(),
                "runtimes": {},
                "overall_status": "HEALTHY",
            }

            # Check each runtime
            runtime_ids = await self.manager.list_runtimes()
            for runtime_id in runtime_ids:
                try:
                    is_healthy = await self.manager.is_runtime_healthy(runtime_id)
                    status = await self.manager.get_runtime_status(runtime_id)

                    self._system_health["runtimes"][runtime_id] = {
                        "status": status,
                        "healthy": is_healthy,
                    }

                    if not is_healthy:
                        self._system_health["overall_status"] = "DEGRADED"

                except Exception as e:
                    logger.error(f"Error checking health for runtime {runtime_id}: {e}")
                    self._system_health["runtimes"][runtime_id] = {
                        "status": "UNKNOWN",
                        "healthy": False,
                        "error": str(e),
                    }
                    self._system_health["overall_status"] = "UNHEALTHY"

            logger.debug(f"System health check complete: {self._system_health['overall_status']}")

    async def _all_runtimes_ready(self) -> bool:
        """Check if all runtimes are ready."""
        runtime_ids = await self.manager.list_runtimes()
        for runtime_id in runtime_ids:
            status = await self.manager.get_runtime_status(runtime_id)
            if status != "RUNNING":
                return False
        return True

    async def start(self) -> None:
        """
        Start the Runtime Orchestrator.

        This method:
        1. Starts the KernelCommunicator
        2. Starts the KernelRuntimeManager
        3. Sets startup timestamp
        4. Calls start callbacks

        Raises:
            Exception: If start fails.
        """
        if self._started:
            logger.warning("RuntimeOrchestrator already started")
            return

        if not self._initialized:
            raise RuntimeError("RuntimeOrchestrator not initialized. Call initialize() first.")

        logger.info("Starting Runtime Orchestrator...")

        try:
            # Start the communicator
            await self.communicator.start()

            # Start the manager
            await self.manager.start()

            # Set startup timestamp
            self._started_at = datetime.utcnow()

            # Mark as started
            self._started = True

            # Call start callbacks
            for callback in self._on_start:
                try:
                    callback()
                except Exception as e:
                    logger.error(f"Error in start callback: {e}")

            logger.info("Runtime Orchestrator started successfully")

        except Exception as e:
            logger.error(f"Failed to start Runtime Orchestrator: {e}")
            raise

    async def stop(self, reason: str = "shutdown") -> None:
        """
        Stop the Runtime Orchestrator.

        Args:
            reason: Reason for stopping.

        Raises:
            Exception: If stop fails.
        """
        if not self._started:
            logger.warning("RuntimeOrchestrator not started")
            return

        logger.info(f"Stopping Runtime Orchestrator (reason: {reason})...")

        try:
            # Call shutdown callbacks
            for callback in self._on_system_shutdown:
                try:
                    callback(reason)
                except Exception as e:
                    logger.error(f"Error in system shutdown callback: {e}")

            # Stop the manager
            await self.manager.stop()

            # Stop the communicator
            await self.communicator.stop()

            # Cancel health monitor
            if hasattr(self, "_health_monitor_task"):
                self._health_monitor_task.cancel()
                try:
                    await self._health_monitor_task
                except asyncio.CancelledError:
                    pass

            # Mark as stopped
            self._started = False

            # Call stop callbacks
            for callback in self._on_stop:
                try:
                    callback()
                except Exception as e:
                    logger.error(f"Error in stop callback: {e}")

            logger.info("Runtime Orchestrator stopped successfully")

        except Exception as e:
            logger.error(f"Failed to stop Runtime Orchestrator: {e}")
            raise

    async def shutdown(self, reason: str = "shutdown") -> None:
        """
        Shutdown the Runtime Orchestrator.

        Args:
            reason: Reason for shutdown.
        """
        logger.info(f"Shutting down Runtime Orchestrator (reason: {reason})...")

        # Stop the orchestrator
        await self.stop(reason=reason)

        # Shutdown the communicator
        await self.communicator.shutdown(reason=reason)

        # Mark as not initialized
        self._initialized = False

        logger.info("Runtime Orchestrator shutdown complete")

    async def register_runtime(self, runtime: "BaseRuntime") -> None:
        """
        Register a runtime with the orchestrator.

        Args:
            runtime: Runtime instance to register.
        """
        await self.manager.register_runtime(runtime)
        logger.info(f"Runtime registered with orchestrator: {runtime.runtime_id}")

    async def register_all_runtimes(self, runtimes: List["BaseRuntime"]) -> None:
        """
        Register all runtimes with the orchestrator.

        Args:
            runtimes: List of runtime instances to register.
        """
        logger.info(f"Registering {len(runtimes)} runtimes with orchestrator...")

        for runtime in runtimes:
            try:
                await self.register_runtime(runtime)
            except Exception as e:
                logger.error(f"Failed to register runtime {runtime.runtime_id}: {e}")

        logger.info(f"All {len(runtimes)} runtimes registered with orchestrator")

    async def start_runtime(self, runtime_id: str) -> None:
        """
        Start a runtime.

        Args:
            runtime_id: ID of the runtime to start.
        """
        async with self._startup_lock:
            # Check if already starting
            if runtime_id in self._startup_tasks:
                logger.warning(f"Runtime already starting: {runtime_id}")
                return

            # Create startup task
            task = asyncio.create_task(self._start_runtime_task(runtime_id))
            self._startup_tasks[runtime_id] = task

            # Wait for startup to complete
            try:
                await task
            except Exception as e:
                logger.error(f"Failed to start runtime {runtime_id}: {e}")
                raise
            finally:
                del self._startup_tasks[runtime_id]

    async def _start_runtime_task(self, runtime_id: str) -> None:
        """Task to start a runtime."""
        await self.manager.start_runtime(runtime_id)
        logger.info(f"Runtime started by orchestrator: {runtime_id}")

    async def start_all_runtimes(self) -> None:
        """
        Start all registered runtimes.

        This method starts runtimes with controlled concurrency
        to avoid overwhelming the system.
        """
        runtime_ids = await self.manager.list_runtimes()
        logger.info(f"Starting {len(runtime_ids)} runtimes...")

        # Start runtimes with controlled concurrency
        semaphore = asyncio.Semaphore(self._config.max_concurrent_starts)

        async def start_with_semaphore(runtime_id: str) -> None:
            async with semaphore:
                try:
                    await self.start_runtime(runtime_id)
                except Exception as e:
                    logger.error(f"Failed to start runtime {runtime_id}: {e}")

        # Start all runtimes concurrently (with semaphore control)
        tasks = [start_with_semaphore(runtime_id) for runtime_id in runtime_ids]
        await asyncio.gather(*tasks, return_exceptions=True)

        # Check if all runtimes are ready
        if await self._all_runtimes_ready():
            await self._publish_system_ready()
            for callback in self._on_system_ready:
                try:
                    callback()
                except Exception as e:
                    logger.error(f"Error in system ready callback: {e}")

        logger.info(f"All {len(runtime_ids)} runtimes started")

    async def _publish_system_ready(self) -> None:
        """Publish system.ready event."""
        from tangku_agentos.runtime_communication.integration import SystemEvents

        runtime_count = len(await self.manager.list_runtimes())

        event = SystemEvents.kernel_ready(
            version=self.communicator.config.version,
            runtimes_loaded=runtime_count,
        )

        try:
            await self.communicator.event_bus.publish(event.to_event())
            logger.info(f"Published system.ready event ({runtime_count} runtimes)")
        except Exception as e:
            logger.error(f"Failed to publish system.ready event: {e}")

    async def stop_runtime(self, runtime_id: str, force: bool = False) -> None:
        """
        Stop a runtime.

        Args:
            runtime_id: ID of the runtime to stop.
            force: Whether to force stop.
        """
        async with self._shutdown_lock:
            # Check if already shutting down
            if runtime_id in self._shutdown_tasks:
                logger.warning(f"Runtime already shutting down: {runtime_id}")
                return

            # Create shutdown task
            task = asyncio.create_task(self._stop_runtime_task(runtime_id, force))
            self._shutdown_tasks[runtime_id] = task

            # Wait for shutdown to complete
            try:
                await task
            except Exception as e:
                logger.error(f"Failed to stop runtime {runtime_id}: {e}")
                raise
            finally:
                del self._shutdown_tasks[runtime_id]

    async def _stop_runtime_task(self, runtime_id: str, force: bool) -> None:
        """Task to stop a runtime."""
        await self.manager.stop_runtime(runtime_id, force=force)
        logger.info(f"Runtime stopped by orchestrator: {runtime_id}")

    async def stop_all_runtimes(self, force: bool = False) -> None:
        """
        Stop all registered runtimes.

        Args:
            force: Whether to force stop.
        """
        runtime_ids = await self.manager.list_runtimes()
        logger.info(f"Stopping {len(runtime_ids)} runtimes...")

        # Stop runtimes with controlled concurrency
        semaphore = asyncio.Semaphore(self._config.max_concurrent_starts)

        async def stop_with_semaphore(runtime_id: str) -> None:
            async with semaphore:
                try:
                    await self.stop_runtime(runtime_id, force=force)
                except Exception as e:
                    logger.error(f"Failed to stop runtime {runtime_id}: {e}")

        # Stop all runtimes concurrently (with semaphore control)
        tasks = [stop_with_semaphore(runtime_id) for runtime_id in reversed(runtime_ids)]
        await asyncio.gather(*tasks, return_exceptions=True)

        logger.info(f"All {len(runtime_ids)} runtimes stopped")

    async def restart_runtime(self, runtime_id: str) -> None:
        """
        Restart a runtime.

        Args:
            runtime_id: ID of the runtime to restart.
        """
        await self.manager.restart_runtime(runtime_id)
        logger.info(f"Runtime restarted by orchestrator: {runtime_id}")

    async def get_runtime(self, runtime_id: str) -> Optional["BaseRuntime"]:
        """
        Get a runtime by ID.

        Args:
            runtime_id: ID of the runtime to get.

        Returns:
            Runtime instance if found, None otherwise.
        """
        return await self.manager.get_runtime(runtime_id)

    async def list_runtimes(self) -> List[str]:
        """
        List all registered runtime IDs.

        Returns:
            List of runtime IDs.
        """
        return await self.manager.list_runtimes()

    async def get_system_health(self) -> Dict[str, Any]:
        """
        Get the health of the entire system.

        Returns:
            System health information.
        """
        async with self._health_lock:
            return self._system_health.copy()

    async def is_system_healthy(self) -> bool:
        """
        Check if the entire system is healthy.

        Returns:
            True if healthy, False otherwise.
        """
        health = await self.get_system_health()
        return health.get("overall_status") == "HEALTHY"

    async def get_metrics(self) -> Dict[str, Any]:
        """
        Get orchestrator metrics.

        Returns:
            Dictionary of metrics.
        """
        metrics = {
            "orchestrator": {
                "initialized": self._initialized,
                "started": self._started,
                "started_at": self._started_at.isoformat() if self._started_at else None,
                "runtime_count": len(await self.list_runtimes()),
            },
            "manager": await self.manager.get_metrics(),
            "communicator": await self.communicator.get_metrics(),
            "system_health": await self.get_system_health(),
        }

        return metrics

    def __repr__(self) -> str:
        """Return string representation."""
        status = "started" if self._started else ("initialized" if self._initialized else "stopped")
        runtime_count = len(self._startup_tasks) if self._started else 0
        return (
            f"RuntimeOrchestrator("
            f"status={status}, "
            f"runtimes={runtime_count})"
        )
