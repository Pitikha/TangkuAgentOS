"""
Kernel Runtime - Kernel Runtime Manager

The KernelRuntimeManager is responsible for managing the lifecycle of the
Kernel Runtime and all its components. It works closely with the
KernelCommunicator to ensure proper initialization, startup, and shutdown
of the entire TangkuAgentOS system.

This class provides:
- Kernel lifecycle management
- Runtime registration and management
- Health monitoring
- Error recovery
- Graceful shutdown

Author: TangkuAgentOS Team
License: MIT
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional, Set, TYPE_CHECKING

if TYPE_CHECKING:
    from tangku_agentos.kernel_runtime.integration.kernel_communicator import KernelCommunicator
    from tangku_agentos.runtime_communication.integration.base import BaseRuntime

logger = logging.getLogger(__name__)


@dataclass
class KernelRuntimeConfig:
    """
    Configuration for the Kernel Runtime Manager.

    Attributes:
        auto_start: Whether to auto-start the kernel on initialization.
        auto_register: Whether to auto-register runtimes.
        recovery_enabled: Whether to enable automatic recovery.
        max_recovery_attempts: Maximum recovery attempts per runtime.
        recovery_backoff: Base backoff time for recovery attempts.
        shutdown_timeout: Timeout for graceful shutdown.
    """

    auto_start: bool = True
    auto_register: bool = True
    recovery_enabled: bool = True
    max_recovery_attempts: int = 3
    recovery_backoff: float = 1.0
    shutdown_timeout: float = 60.0


class KernelRuntimeManager:
    """
    Manager for the Kernel Runtime lifecycle.

    The KernelRuntimeManager is responsible for:
    - Initializing the kernel and all its components
    - Starting and stopping runtimes
    - Monitoring runtime health
    - Recovering from runtime failures
    - Performing graceful shutdown

    Thread Safety:
        This class is thread-safe for concurrent access.

    Example:
        >>> from tangku_agentos.kernel_runtime.integration import KernelRuntimeManager
        >>> 
        >>> # Create and start the kernel manager
        >>> manager = KernelRuntimeManager()
        >>> await manager.initialize()
        >>> await manager.start()
        >>> 
        >>> # Register and start runtimes
        >>> await manager.register_runtime(my_runtime)
        >>> await manager.start_runtime(my_runtime.runtime_id)
    """

    def __init__(
        self,
        communicator: Optional["KernelCommunicator"] = None,
        config: Optional[KernelRuntimeConfig] = None,
    ):
        """
        Initialize the Kernel Runtime Manager.

        Args:
            communicator: KernelCommunicator instance.
            config: Kernel runtime configuration.
        """
        self._communicator = communicator
        self._config = config or KernelRuntimeConfig()
        self._initialized = False
        self._started = False

        # Runtime tracking
        self._runtimes: Dict[str, Any] = {}
        self._runtime_lock = asyncio.Lock()

        # Recovery tracking
        self._recovery_attempts: Dict[str, int] = {}
        self._recovery_lock = asyncio.Lock()

        # Lifecycle callbacks
        self._on_initialize: List[Callable[[], None]] = []
        self._on_start: List[Callable[[], None]] = []
        self._on_stop: List[Callable[[], None]] = []
        self._on_runtime_registered: List[Callable[[str], None]] = []
        self._on_runtime_unregistered: List[Callable[[str], None]] = []
        self._on_runtime_failed: List[Callable[[str, Exception], None]] = []

        # Startup timestamp
        self._started_at: Optional[datetime] = None

        logger.info("KernelRuntimeManager initialized")

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
    def config(self) -> KernelRuntimeConfig:
        """Get the kernel runtime configuration."""
        return self._config

    @property
    def is_initialized(self) -> bool:
        """Check if the kernel runtime manager is initialized."""
        return self._initialized

    @property
    def is_started(self) -> bool:
        """Check if the kernel runtime manager is started."""
        return self._started

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

    def on_runtime_registered(self, callback: Callable[[str], None]) -> None:
        """
        Register a callback for runtime registration.

        Args:
            callback: Callback to call when a runtime is registered.
        """
        self._on_runtime_registered.append(callback)

    def on_runtime_unregistered(self, callback: Callable[[str], None]) -> None:
        """
        Register a callback for runtime unregistration.

        Args:
            callback: Callback to call when a runtime is unregistered.
        """
        self._on_runtime_unregistered.append(callback)

    def on_runtime_failed(self, callback: Callable[[str, Exception], None]) -> None:
        """
        Register a callback for runtime failure.

        Args:
            callback: Callback to call when a runtime fails.
        """
        self._on_runtime_failed.append(callback)

    async def initialize(self) -> None:
        """
        Initialize the Kernel Runtime Manager.

        This method:
        1. Initializes the KernelCommunicator
        2. Sets up runtime tracking
        3. Calls initialization callbacks

        Raises:
            Exception: If initialization fails.
        """
        if self._initialized:
            logger.warning("KernelRuntimeManager already initialized")
            return

        logger.info("Initializing Kernel Runtime Manager...")

        try:
            # Initialize the communicator
            await self.communicator.initialize()

            # Set up runtime tracking
            self._setup_runtime_tracking()

            # Mark as initialized
            self._initialized = True

            # Call initialization callbacks
            for callback in self._on_initialize:
                try:
                    callback()
                except Exception as e:
                    logger.error(f"Error in initialization callback: {e}")

            logger.info("Kernel Runtime Manager initialized successfully")

            # Auto-start if configured
            if self._config.auto_start:
                await self.start()

        except Exception as e:
            logger.error(f"Failed to initialize Kernel Runtime Manager: {e}")
            raise

    def _setup_runtime_tracking(self) -> None:
        """Set up runtime tracking."""
        # Register callbacks with the integration registry
        if self.communicator.integration_registry:
            self.communicator.integration_registry.on_register(
                self._on_runtime_integration_registered
            )
            self.communicator.integration_registry.on_unregister(
                self._on_runtime_integration_unregistered
            )
            self.communicator.integration_registry.on_status_change(
                self._on_runtime_status_change
            )

    async def _on_runtime_integration_registered(
        self, info: Any
    ) -> None:
        """Handle runtime integration registration."""
        runtime_id = info.runtime_id
        logger.info(f"Runtime integration registered: {runtime_id}")

        # Call registered callbacks
        for callback in self._on_runtime_registered:
            try:
                callback(runtime_id)
            except Exception as e:
                logger.error(f"Error in runtime registered callback: {e}")

    async def _on_runtime_integration_unregistered(
        self, info: Any
    ) -> None:
        """Handle runtime integration unregistration."""
        runtime_id = info.runtime_id
        logger.info(f"Runtime integration unregistered: {runtime_id}")

        # Call unregistered callbacks
        for callback in self._on_runtime_unregistered:
            try:
                callback(runtime_id)
            except Exception as e:
                logger.error(f"Error in runtime unregistered callback: {e}")

    async def _on_runtime_status_change(
        self, info: Any, new_status: Any
    ) -> None:
        """Handle runtime status change."""
        runtime_id = info.runtime_id
        logger.info(f"Runtime status changed: {runtime_id} -> {new_status.name}")

        # Check for failure
        from tangku_agentos.runtime_communication.integration.registry import RuntimeIntegrationStatus

        if new_status == RuntimeIntegrationStatus.FAILED:
            # Try to recover if enabled
            if self._config.recovery_enabled:
                await self._recover_runtime(runtime_id)

    async def start(self) -> None:
        """
        Start the Kernel Runtime Manager.

        This method:
        1. Starts the KernelCommunicator
        2. Sets startup timestamp
        3. Calls start callbacks

        Raises:
            Exception: If start fails.
        """
        if self._started:
            logger.warning("KernelRuntimeManager already started")
            return

        if not self._initialized:
            raise RuntimeError("KernelRuntimeManager not initialized. Call initialize() first.")

        logger.info("Starting Kernel Runtime Manager...")

        try:
            # Start the communicator
            await self.communicator.start()

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

            logger.info("Kernel Runtime Manager started successfully")

        except Exception as e:
            logger.error(f"Failed to start Kernel Runtime Manager: {e}")
            raise

    async def stop(self, force: bool = False) -> None:
        """
        Stop the Kernel Runtime Manager.

        Args:
            force: Whether to force stop.

        Raises:
            Exception: If stop fails.
        """
        if not self._started:
            logger.warning("KernelRuntimeManager not started")
            return

        logger.info("Stopping Kernel Runtime Manager...")

        try:
            # Stop all runtimes first
            await self.stop_all_runtimes(force=force)

            # Stop the communicator
            await self.communicator.stop()

            # Mark as stopped
            self._started = False

            # Call stop callbacks
            for callback in self._on_stop:
                try:
                    callback()
                except Exception as e:
                    logger.error(f"Error in stop callback: {e}")

            logger.info("Kernel Runtime Manager stopped successfully")

        except Exception as e:
            logger.error(f"Failed to stop Kernel Runtime Manager: {e}")
            raise

    async def shutdown(self, reason: str = "shutdown") -> None:
        """
        Shutdown the Kernel Runtime Manager.

        Args:
            reason: Reason for shutdown.
        """
        logger.info(f"Shutting down Kernel Runtime Manager (reason: {reason})...")

        # Stop the manager
        await self.stop()

        # Shutdown the communicator
        await self.communicator.shutdown(reason=reason)

        # Mark as not initialized
        self._initialized = False

        logger.info("Kernel Runtime Manager shutdown complete")

    async def register_runtime(self, runtime: "BaseRuntime") -> None:
        """
        Register a runtime with the Kernel Runtime Manager.

        Args:
            runtime: Runtime instance to register.
        """
        async with self._runtime_lock:
            # Check if already registered
            if runtime.runtime_id in self._runtimes:
                logger.warning(f"Runtime already registered: {runtime.runtime_id}")
                return

            # Store the runtime
            self._runtimes[runtime.runtime_id] = runtime

            # Register with the communicator
            await self.communicator.register_runtime(runtime)

            # Initialize recovery tracking
            self._recovery_attempts[runtime.runtime_id] = 0

            logger.info(f"Runtime registered: {runtime.runtime_id}")

            # Call registered callbacks
            for callback in self._on_runtime_registered:
                try:
                    callback(runtime.runtime_id)
                except Exception as e:
                    logger.error(f"Error in runtime registered callback: {e}")

    async def unregister_runtime(self, runtime_id: str) -> None:
        """
        Unregister a runtime from the Kernel Runtime Manager.

        Args:
            runtime_id: ID of the runtime to unregister.
        """
        async with self._runtime_lock:
            # Check if registered
            if runtime_id not in self._runtimes:
                logger.warning(f"Runtime not registered: {runtime_id}")
                return

            # Get the runtime
            runtime = self._runtimes[runtime_id]

            # Unregister from the communicator
            await self.communicator.unregister_runtime(runtime_id)

            # Remove from tracking
            del self._runtimes[runtime_id]
            del self._recovery_attempts[runtime_id]

            logger.info(f"Runtime unregistered: {runtime_id}")

            # Call unregistered callbacks
            for callback in self._on_runtime_unregistered:
                try:
                    callback(runtime_id)
                except Exception as e:
                    logger.error(f"Error in runtime unregistered callback: {e}")

    async def start_runtime(self, runtime_id: str) -> None:
        """
        Start a runtime.

        Args:
            runtime_id: ID of the runtime to start.
        """
        async with self._runtime_lock:
            # Check if registered
            if runtime_id not in self._runtimes:
                raise ValueError(f"Runtime not registered: {runtime_id}")

            runtime = self._runtimes[runtime_id]

            # Start the runtime
            await self.communicator.start_runtime(runtime)

            logger.info(f"Runtime started: {runtime_id}")

    async def stop_runtime(self, runtime_id: str, force: bool = False) -> None:
        """
        Stop a runtime.

        Args:
            runtime_id: ID of the runtime to stop.
            force: Whether to force stop.
        """
        async with self._runtime_lock:
            # Check if registered
            if runtime_id not in self._runtimes:
                raise ValueError(f"Runtime not registered: {runtime_id}")

            runtime = self._runtimes[runtime_id]

            # Stop the runtime
            await self.communicator.stop_runtime(runtime, force=force)

            # Remove from tracking
            del self._runtimes[runtime_id]
            del self._recovery_attempts[runtime_id]

            logger.info(f"Runtime stopped: {runtime_id}")

    async def restart_runtime(self, runtime_id: str) -> None:
        """
        Restart a runtime.

        Args:
            runtime_id: ID of the runtime to restart.
        """
        async with self._runtime_lock:
            # Check if registered
            if runtime_id not in self._runtimes:
                raise ValueError(f"Runtime not registered: {runtime_id}")

            runtime = self._runtimes[runtime_id]

            # Restart the runtime
            await self.communicator.restart_runtime(runtime)

            # Reset recovery attempts
            self._recovery_attempts[runtime_id] = 0

            logger.info(f"Runtime restarted: {runtime_id}")

    async def register_all_runtimes(self, runtimes: List["BaseRuntime"]) -> None:
        """
        Register all runtimes.

        Args:
            runtimes: List of runtime instances to register.
        """
        logger.info(f"Registering {len(runtimes)} runtimes...")

        for runtime in runtimes:
            try:
                await self.register_runtime(runtime)
            except Exception as e:
                logger.error(f"Failed to register runtime {runtime.runtime_id}: {e}")
                # Continue with other runtimes

        logger.info(f"All {len(runtimes)} runtimes registered")

    async def start_all_runtimes(self) -> None:
        """Start all registered runtimes."""
        async with self._runtime_lock:
            runtime_ids = list(self._runtimes.keys())

        logger.info(f"Starting {len(runtime_ids)} runtimes...")

        for runtime_id in runtime_ids:
            try:
                await self.start_runtime(runtime_id)
            except Exception as e:
                logger.error(f"Failed to start runtime {runtime_id}: {e}")
                # Continue with other runtimes

        logger.info(f"All {len(runtime_ids)} runtimes started")

    async def stop_all_runtimes(self, force: bool = False) -> None:
        """
        Stop all registered runtimes.

        Args:
            force: Whether to force stop.
        """
        async with self._runtime_lock:
            runtime_ids = list(self._runtimes.keys())

        logger.info(f"Stopping {len(runtime_ids)} runtimes...")

        # Stop in reverse order
        for runtime_id in reversed(runtime_ids):
            try:
                await self.stop_runtime(runtime_id, force=force)
            except Exception as e:
                logger.error(f"Failed to stop runtime {runtime_id}: {e}")
                # Continue with other runtimes

        logger.info(f"All {len(runtime_ids)} runtimes stopped")

    async def _recover_runtime(self, runtime_id: str) -> None:
        """
        Attempt to recover a failed runtime.

        Args:
            runtime_id: ID of the runtime to recover.
        """
        async with self._recovery_lock:
            # Check if recovery is enabled
            if not self._config.recovery_enabled:
                logger.info(f"Recovery disabled for runtime: {runtime_id}")
                return

            # Check max recovery attempts
            attempts = self._recovery_attempts.get(runtime_id, 0)
            if attempts >= self._config.max_recovery_attempts:
                logger.warning(
                    f"Max recovery attempts reached for runtime: {runtime_id} "
                    f"({attempts}/{self._config.max_recovery_attempts})"
                )
                return

            # Increment recovery attempts
            self._recovery_attempts[runtime_id] = attempts + 1

            # Calculate backoff
            backoff = self._config.recovery_backoff * (2 ** attempts)
            logger.info(
                f"Attempting to recover runtime: {runtime_id} "
                f"(attempt {attempts + 1}/{self._config.max_recovery_attempts}, "
                f"backoff: {backoff}s)"
            )

            # Wait for backoff
            await asyncio.sleep(backoff)

            # Try to restart the runtime
            try:
                if runtime_id in self._runtimes:
                    await self.restart_runtime(runtime_id)
                    logger.info(f"Runtime recovered: {runtime_id}")
                else:
                    logger.warning(f"Runtime not found for recovery: {runtime_id}")

            except Exception as e:
                logger.error(f"Failed to recover runtime {runtime_id}: {e}")
                # Call failure callbacks
                for callback in self._on_runtime_failed:
                    try:
                        callback(runtime_id, e)
                    except Exception as cb_e:
                        logger.error(f"Error in runtime failed callback: {cb_e}")

    async def get_runtime(self, runtime_id: str) -> Optional["BaseRuntime"]:
        """
        Get a runtime by ID.

        Args:
            runtime_id: ID of the runtime to get.

        Returns:
            Runtime instance if found, None otherwise.
        """
        async with self._runtime_lock:
            return self._runtimes.get(runtime_id)

    async def list_runtimes(self) -> List[str]:
        """
        List all registered runtime IDs.

        Returns:
            List of runtime IDs.
        """
        async with self._runtime_lock:
            return list(self._runtimes.keys())

    async def get_runtime_info(self, runtime_id: str) -> Optional[Any]:
        """
        Get runtime information.

        Args:
            runtime_id: ID of the runtime.

        Returns:
            Runtime info if found, None otherwise.
        """
        return self.communicator.registry.get(runtime_id)

    async def get_runtime_status(self, runtime_id: str) -> Optional[str]:
        """
        Get runtime status.

        Args:
            runtime_id: ID of the runtime.

        Returns:
            Runtime status if found, None otherwise.
        """
        info = await self.get_runtime_info(runtime_id)
        return info.status.name if info else None

    async def is_runtime_healthy(self, runtime_id: str) -> bool:
        """
        Check if a runtime is healthy.

        Args:
            runtime_id: ID of the runtime.

        Returns:
            True if healthy, False otherwise.
        """
        if self.communicator.health_service:
            health = self.communicator.health_service.get_health(runtime_id)
            return health is not None and health.status.value == "HEALTHY"
        return False

    async def get_metrics(self) -> Dict[str, Any]:
        """
        Get kernel runtime manager metrics.

        Returns:
            Dictionary of metrics.
        """
        metrics = {
            "kernel": {
                "initialized": self._initialized,
                "started": self._started,
                "started_at": self._started_at.isoformat() if self._started_at else None,
                "runtime_count": len(self._runtimes),
                "recovery_attempts": sum(self._recovery_attempts.values()),
            },
            "runtimes": {},
        }

        # Add runtime statuses
        for runtime_id, runtime in self._runtimes.items():
            metrics["runtimes"][runtime_id] = {
                "status": runtime.state.name,
                "recovery_attempts": self._recovery_attempts.get(runtime_id, 0),
            }

        # Add communicator metrics
        metrics["communicator"] = await self.communicator.get_metrics()

        return metrics

    def __repr__(self) -> str:
        """Return string representation."""
        status = "started" if self._started else ("initialized" if self._initialized else "stopped")
        return (
            f"KernelRuntimeManager("
            f"status={status}, "
            f"runtimes={len(self._runtimes)})"
        )
