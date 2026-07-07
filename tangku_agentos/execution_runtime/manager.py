from __future__ import annotations

from .interfaces import ExecutionManager


class ExecutionManager(ExecutionManager):
    """Execution manager abstraction."""

    def execute(self, context):
        raise NotImplementedError

    def execute_async(self, context):
        raise NotImplementedError

    def cancel(self, execution_id: str) -> None:
        raise NotImplementedError

    def resume(self, execution_id: str):
        raise NotImplementedError
