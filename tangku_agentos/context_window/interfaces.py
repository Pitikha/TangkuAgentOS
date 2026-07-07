from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from .models import ContextBudget


class ContextBudgetManager(ABC):
    """Interface for managing context budgets."""

    @abstractmethod
    def allocate(self, budget: ContextBudget) -> None:
        ...

    @abstractmethod
    def consume(self, tokens: int) -> None:
        ...

    @abstractmethod
    def remaining(self) -> int:
        ...


class TokenBudget(ABC):
    """Interface for token budgets."""

    @abstractmethod
    def get_limit(self) -> int:
        ...

    @abstractmethod
    def get_usage(self) -> int:
        ...


class CompressionPolicy(ABC):
    """Interface for context compression policies."""

    @abstractmethod
    def apply(self, context: dict[str, Any]) -> dict[str, Any]:
        ...


class ContextPrioritizer(ABC):
    """Interface for prioritizing context slices."""

    @abstractmethod
    def prioritize(self, context: dict[str, Any]) -> list[str]:
        ...


class OverflowStrategy(ABC):
    """Interface for handling context overflow."""

    @abstractmethod
    def handle_overflow(self, context: dict[str, Any]) -> dict[str, Any]:
        ...
