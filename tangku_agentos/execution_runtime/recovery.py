from __future__ import annotations

from .interfaces import ExecutionRecovery


class ExecutionRecovery(ExecutionRecovery):
    """Concrete execution recovery manager."""

    def checkpoint(self, session_id: str) -> str:
        raise NotImplementedError

    def resume(self, checkpoint_id: str):
        raise NotImplementedError
