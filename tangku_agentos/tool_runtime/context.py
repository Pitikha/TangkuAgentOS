from __future__ import annotations

from .interfaces import ToolContext


class ToolContext(ToolContext):
    """Tool execution context abstraction."""

    def __init__(self, values: dict[str, str] | None = None) -> None:
        self._values = dict(values or {})

    def get_context(self) -> dict[str, str]:
        return dict(self._values)
