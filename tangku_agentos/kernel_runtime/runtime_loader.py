"""Runtime loading logic for TangkuAgentOS kernel.

This module provides the `RuntimeLoader` class, which is responsible for
loading runtimes and updating their status to 'loaded'.
"""

from __future__ import annotations

from typing import Final

from .types import KernelRuntime


class RuntimeLoader:
    """Loads runtimes and updates their status to 'loaded'.

    This class provides a simple interface for loading runtimes, which involves
    updating their status to indicate that they have been successfully loaded
    into the kernel.

    Attributes:
        None (stateless class).
    """

    def load_runtime(self, runtime: KernelRuntime) -> KernelRuntime:
        """Loads a runtime and updates its status to 'loaded'.

        Args:
            runtime: The `KernelRuntime` object to load.

        Returns:
            A new `KernelRuntime` object with the status set to 'loaded'.
        """
        return KernelRuntime(
            runtime_id=runtime.runtime_id,
            name=runtime.name,
            status="loaded",
            metadata=runtime.metadata,
        )
