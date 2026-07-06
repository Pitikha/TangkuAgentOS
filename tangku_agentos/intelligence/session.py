from __future__ import annotations

from .interfaces import IntelligenceSession


class IntelligenceSession(IntelligenceSession):
    """Concrete intelligence session representation."""

    def __init__(self, session_id: str) -> None:
        self.session_id = session_id
        self.active = False

    def start(self) -> None:
        self.active = True

    def end(self) -> None:
        self.active = False
