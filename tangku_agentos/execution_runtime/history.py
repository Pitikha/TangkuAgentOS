from __future__ import annotations

from .interfaces import ExecutionHistory
from .models import ExecutionSession, ExecutionResult


class ExecutionHistory(ExecutionHistory):
    """Concrete execution history manager."""

    def record(self, session: ExecutionSession, result: ExecutionResult) -> None:
        raise NotImplementedError

    def list_history(self, session_id: str) -> list[ExecutionHistory]:
        raise NotImplementedError
