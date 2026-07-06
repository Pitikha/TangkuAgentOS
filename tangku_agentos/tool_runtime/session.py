from __future__ import annotations

from .interfaces import ToolSession


class ToolSession(ToolSession):
    """Manage a simple tool execution session lifecycle."""

    def __init__(self, session_id: str) -> None:
        self._session_id = session_id
        self._active = False

    def start(self) -> None:
        self._active = True

    def end(self) -> None:
        self._active = False

    @property
    def active(self) -> bool:
        return self._active
