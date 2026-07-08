"""Runtime coordination for TangkuAgentOS kernel.

This module provides the `RuntimeCoordinator` class, which is responsible for
coordinating runtime operations, such as ensuring that runtimes are started
and stopped in the correct order.
"""

from __future__ import annotations

from typing import Final

from .types import KernelRuntime


class RuntimeCoordinator:
    """Coordinates runtime operations in the kernel.

    This class provides a simple interface for coordinating runtime operations,
    such as ensuring that runtimes are started and stopped in the correct order
    based on their dependencies.

    Attributes:
        None (stateless class).
    """

    def coordinate(self, runtime: KernelRuntime) -> str:
        """Coordinated a runtime operation.

        Args:
            runtime: The `KernelRuntime` object to coordinate.

        Returns:
            A string indicating that the runtime has been coordinated.
        """
        return f"coordinated:{runtime.runtime_id}"
