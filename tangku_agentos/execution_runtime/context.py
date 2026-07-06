from __future__ import annotations

from .interfaces import ExecutionContext


class ExecutionContext(ExecutionContext):
    """Concrete execution context."""

    def __init__(self, data: dict[str, object]) -> None:
        self._data = data

    def get_context(self) -> dict[str, object]:
        return self._data

    def update_context(self, updates: dict[str, object]) -> None:
        self._data.update(updates)
