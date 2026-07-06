from __future__ import annotations

from .interfaces import ExecutionQueue
from .models import ExecutionSession


class ExecutionQueue(ExecutionQueue):
    """Execution queue abstraction."""

    def enqueue(self, session: ExecutionSession) -> str:
        raise NotImplementedError

    def dequeue(self) -> ExecutionSession | None:
        raise NotImplementedError
