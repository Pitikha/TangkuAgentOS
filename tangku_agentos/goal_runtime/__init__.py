"""Goal runtime for Tangku AgentOS (minimal stubs for integration tests)."""

from .manager import GoalManager
from .registry import GoalRegistry
from .lifecycle import GoalLifecycle

__all__ = ["GoalManager", "GoalRegistry", "GoalLifecycle"]
