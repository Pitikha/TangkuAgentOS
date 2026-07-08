"""Kernel bootstrap logic for TangkuAgentOS.

This module provides the `KernelBootstrap` class, which manages the initialization
steps required to start the kernel. It ensures that all necessary components are
properly initialized in the correct order.
"""

from __future__ import annotations

from typing import Final, List


class KernelBootstrap:
    """Manages the bootstrap steps for the TangkuAgentOS kernel.

    This class defines and tracks the sequence of steps required to initialize
    the kernel, such as loading configuration, registering runtimes, resolving
    dependencies, and performing health checks.

    Attributes:
        _steps: A list of bootstrap step names.
    """

    def __init__(self) -> None:
        """Initializes the bootstrap manager with an empty list of steps."""
        self._steps: Final[List[str]] = []

    def initialize(self) -> None:
        """Initializes the default bootstrap steps.

        This method sets up the standard sequence of steps required to bootstrap
        the kernel, including configuration loading, runtime registration,
        dependency resolution, and health checks.
        """
        self._steps.clear()
        self._steps.extend(
            [
                "config",
                "runtime-registration",
                "dependency-resolution",
                "health-check",
                "ready",
            ]
        )

    def steps(self) -> List[str]:
        """Returns a copy of the current bootstrap steps.

        Returns:
            A list of bootstrap step names in the order they should be executed.
        """
        return list(self._steps)
