"""Recovery logic for TangkuAgentOS kernel runtimes.

This module provides the `RecoveryManager` class, which is responsible for
recovering failed runtimes by restarting them and tracking recovery actions.
"""

from __future__ import annotations

from threading import RLock
from typing import Any, Dict, Final, List


class RecoveryManager:
    """Manages the recovery of failed runtimes in the kernel.

    This class provides methods for recovering failed runtimes by restarting
    them and tracking the results of recovery actions. It ensures thread-safe
    recovery operations.

    Attributes:
        _recovery_actions: A list of recovery actions taken.
        _lock: A reentrant lock to ensure thread-safe operations.
    """

    def __init__(self) -> None:
        """Initializes the recovery manager with an empty list of actions."""
        self._recovery_actions: List[Dict[str, Any]] = []
        self._lock: Final[RLock] = RLock()

    def record_recovery_action(
        self,
        runtime_id: str,
        action: str,
        status: str,
        error: str = "",
    ) -> None:
        """Records a recovery action.

        Args:
            runtime_id: The ID of the runtime the action was taken for.
            action: The type of action taken (e.g., "recovery").
            status: The status of the action (e.g., "recovered", "failed").
            error: An error message if the action failed.
        """
        with self._lock:
            self._recovery_actions.append(
                {
                    "runtime_id": runtime_id,
                    "action": action,
                    "status": status,
                    "error": error,
                }
            )

    def get_recovery_actions(self) -> List[Dict[str, Any]]:
        """Retrieves all recorded recovery actions.

        Returns:
            A list of dictionaries representing recovery actions.
        """
        with self._lock:
            return list(self._recovery_actions)

    def clear_recovery_actions(self) -> None:
        """Clears all recorded recovery actions."""
        with self._lock:
            self._recovery_actions.clear()
