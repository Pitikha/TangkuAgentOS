from __future__ import annotations

from .interfaces import ExecutionResult
from .models import ExecutionResult as ExecutionResultModel


class ExecutionResult(ExecutionResult):
    """Concrete execution result representation."""

    def get_result(self) -> dict[str, object]:
        raise NotImplementedError

    def is_success(self) -> bool:
        raise NotImplementedError
