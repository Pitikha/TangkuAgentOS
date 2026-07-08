from __future__ import annotations

import time
from threading import RLock
from typing import Any, Callable, Dict, List, Optional, Set

from .constants import LifecycleEvent
from .exceptions import (
    HealthCheckError,
    LifecycleError,
    LifecycleRollbackError,
    LifecycleTimeoutError,
)
from .types import EventPayload, LifecycleMetrics, LifecycleState


class LifecycleManager:
    """
    Production-grade lifecycle manager with:
    - Timeout support
    - Rollback on failure
    - Event notifications
    - Lifecycle metrics
    - Health checks
    """

    def __init__(self) -> None:
        self._event_handlers: Dict[LifecycleEvent, List[Callable[[EventPayload], None]]] = {
            event: [] for event in LifecycleEvent
        }
        self._state: LifecycleEvent = LifecycleEvent.STOPPED
        self._lock = RLock()
        self._metrics = LifecycleMetrics()
        self._health_checks: List[Callable[[], bool]] = []
        self._rollback_handlers: List[Callable[[LifecycleEvent, Exception], None]] = []

    @property
    def state(self) -> LifecycleEvent:
        """Get the current lifecycle state."""
        with self._lock:
            return self._state

    @property
    def metrics(self) -> LifecycleMetrics:
        """Get lifecycle metrics."""
        with self._lock:
            return LifecycleMetrics(
                transition_count=self._metrics.transition_count,
                failure_count=self._metrics.failure_count,
                last_transition_time=self._metrics.last_transition_time,
                current_state=self._state.value,
            )

    # --- Handler Management ---
    def register_handler(
        self, event: LifecycleEvent, handler: Callable[[EventPayload], None]
    ) -> None:
        """Register a handler for a lifecycle event."""
        if event not in self._event_handlers:
            raise LifecycleError(f"Unsupported lifecycle event: {event}")
        with self._lock:
            self._event_handlers[event].append(handler)

    def deregister_handler(
        self, event: LifecycleEvent, handler: Callable[[EventPayload], None]
    ) -> None:
        """Deregister a handler for a lifecycle event."""
        if event not in self._event_handlers:
            raise LifecycleError(f"Unsupported lifecycle event: {event}")
        with self._lock:
            self._event_handlers[event] = [
                h for h in self._event_handlers[event] if h != handler
            ]

    # --- Rollback Handlers ---
    def register_rollback_handler(
        self, handler: Callable[[LifecycleEvent, Exception], None]
    ) -> None:
        """Register a handler for rollback on failure."""
        with self._lock:
            self._rollback_handlers.append(handler)

    def deregister_rollback_handler(
        self, handler: Callable[[LifecycleEvent, Exception], None]
    ) -> None:
        """Deregister a rollback handler."""
        with self._lock:
            self._rollback_handlers = [
                h for h in self._rollback_handlers if h != handler
            ]

    # --- Health Checks ---
    def register_health_check(self, check: Callable[[], bool]) -> None:
        """Register a health check function."""
        with self._lock:
            self._health_checks.append(check)

    def deregister_health_check(self, check: Callable[[], bool]) -> None:
        """Deregister a health check function."""
        with self._lock:
            self._health_checks = [c for c in self._health_checks if c != check]

    def is_healthy(self) -> bool:
        """Check if the system is healthy."""
        with self._lock:
            for check in self._health_checks:
                try:
                    if not check():
                        return False
                except Exception as e:
                    raise HealthCheckError(f"Health check failed: {e}") from e
            return True

    # --- State Transitions ---
    def trigger(
        self,
        event: LifecycleEvent,
        payload: EventPayload | None = None,
        timeout: Optional[float] = None,
    ) -> None:
        """
        Trigger a lifecycle event with optional timeout.
        Automatically rolls back on failure.
        """
        if event not in self._event_handlers:
            raise LifecycleError(f"Unsupported lifecycle event: {event}")

        payload = payload or EventPayload()
        start_time = time.time()

        with self._lock:
            self._state = event
            self._metrics.transition_count += 1
            self._metrics.last_transition_time = start_time
            handlers = list(self._event_handlers[event])

        errors: List[Exception] = []
        for handler in handlers:
            try:
                if timeout is not None and (time.time() - start_time) > timeout:
                    raise LifecycleTimeoutError(
                        f"Lifecycle transition timed out after {timeout} seconds."
                    )
                handler(payload)
            except Exception as error:
                errors.append(error)

        if errors:
            with self._lock:
                self._state = LifecycleEvent.FAILED
                self._metrics.failure_count += 1

            # Trigger rollback
            for rollback_handler in self._rollback_handlers:
                try:
                    rollback_handler(event, errors[0])
                except Exception as e:
                    raise LifecycleRollbackError(
                        f"Rollback handler failed: {e}"
                    ) from e

            raise LifecycleError(
                f"{len(errors)} lifecycle handler(s) failed for event {event}: {errors}"
            )

    # --- Utility ---
    def supported_events(self) -> List[LifecycleEvent]:
        """Get all supported lifecycle events."""
        return list(self._event_handlers.keys())

    def is_running(self) -> bool:
        """Check if the system is running."""
        return self.state == LifecycleEvent.RUNNING

    def status(self) -> Dict[str, Any]:
        """Get the current status of the lifecycle manager."""
        return {
            "state": self.state.value,
            "supported_events": ", ".join(event.value for event in self.supported_events()),
            "is_healthy": self.is_healthy(),
            "metrics": self.metrics,
        }

    def reset(self) -> None:
        """Reset the lifecycle manager to the initial state."""
        with self._lock:
            self._state = LifecycleEvent.STOPPED
            self._metrics = LifecycleMetrics()
