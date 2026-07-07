"""Execution runtime architecture for Tangku AgentOS."""

from .interfaces import (
    ExecutionContext,
    ExecutionHistory,
    ExecutionManager,
    ExecutionRecovery,
    ExecutionResult,
    ExecutionScheduler,
    ExecutionSession,
    ExecutionQueue,
)
from .manager import ExecutionManager
from .queue import ExecutionQueue
from .session import ExecutionSession
from .context import ExecutionContext
from .scheduler import ExecutionScheduler
from .history import ExecutionHistory
from .recovery import ExecutionRecovery
from .results import ExecutionResult
from .runtime import (
    ArtifactManager,
    EnvironmentManager,
    ExecutionManager as RuntimeExecutionManager,
    ExecutionQueueManager,
    ResourceManager,
    SandboxManager,
)

__all__ = [
    "ExecutionManager",
    "ExecutionQueue",
    "ExecutionSession",
    "ExecutionContext",
    "ExecutionScheduler",
    "ExecutionHistory",
    "ExecutionRecovery",
    "ExecutionResult",
    "ArtifactManager",
    "EnvironmentManager",
    "RuntimeExecutionManager",
    "ExecutionQueueManager",
    "ResourceManager",
    "SandboxManager",
]

# Prefer runtime implementations for top-level exports
ExecutionManager = RuntimeExecutionManager
