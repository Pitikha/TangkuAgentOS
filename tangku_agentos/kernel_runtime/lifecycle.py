"""Kernel lifecycle management for TangkuAgentOS.

This module provides the `KernelLifecycle` class, which manages the state transitions
of the kernel (e.g., start, stop, pause, resume). It ensures thread-safe state updates
and provides a simple interface for querying the current state.
"""

from __future__ import annotations

from threading import RLock
from typing import Final


class KernelLifecycle:
    """Manages the lifecycle state of the TangkuAgentOS kernel.

    This class provides thread-safe state transitions for the kernel, ensuring that
    the kernel can be started, stopped, paused, and resumed without race conditions.

    Attributes:
        _state: The current state of the kernel (e.g., "stopped", "running", "paused").
        _lock: A reentrant lock to ensure thread-safe state updates.
    """

    def __init__(self) -> None:
        """Initializes the kernel lifecycle with a default state of 'stopped'."""
        self._state: str = "stopped"
        self._lock: Final[RLock] = RLock()

    def start(self) -> None:
        """Transitions the kernel state to 'running'."""
        with self._lock:
            self._state = "running"

    def stop(self) -> None:
        """Transitions the kernel state to 'stopped'."""
        with self._lock:
            self._state = "stopped"

    def pause(self) -> None:
        """Transitions the kernel state to 'paused'."""
        with self._lock:
            self._state = "paused"

    def resume(self) -> None:
        """Transitions the kernel state to 'running'."""
        with self._lock:
            self._state = "running"

    def state(self) -> str:
        """Returns the current state of the kernel.

        Returns:
            The current state as a string (e.g., "stopped", "running", "paused").
        """
        with self._lock:
            return self._state
