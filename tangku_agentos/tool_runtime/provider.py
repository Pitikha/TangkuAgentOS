from __future__ import annotations

from .interfaces import ToolProvider
from .models import Tool


class ToolProvider(ToolProvider):
    """Tool provider contract."""

    def provide(self, tool_id: str) -> Tool:
        raise NotImplementedError
