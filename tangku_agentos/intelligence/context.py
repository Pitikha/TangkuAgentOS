from __future__ import annotations

from abc import ABC

from .interfaces import IntelligenceContext


class IntelligenceContext(IntelligenceContext):
    """Concrete intelligence context manager."""

    def __init__(self) -> None:
        self._context: dict[str, object] = {}

    def get_context(self) -> dict[str, object]:
        return self._context

    def update_context(self, updates: dict[str, object]) -> None:
        self._context.update(updates)
