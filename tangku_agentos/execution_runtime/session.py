from __future__ import annotations

from .interfaces import ExecutionSession


class ExecutionSession(ExecutionSession):
    """Concrete execution session."""

    def start(self) -> None:
        raise NotImplementedError

    def end(self) -> None:
        raise NotImplementedError
