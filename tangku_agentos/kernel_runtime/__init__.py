"""Tangku AgentOS kernel and runtime integration layer.

This package provides the core kernel runtime system for TangkuAgentOS,
including runtime management, lifecycle control, dependency resolution,
scheduling, and resource management.

The main entry point is the `KernelManager` class, which orchestrates all
runtime operations and provides a unified interface for kernel management.
"""

from .bootstrap import KernelBootstrap
from .dependency_manager import RuntimeDependencyManager
from .health import KernelHealthMonitor
from .lifecycle import KernelLifecycle
from .recovery import RecoveryManager
from .resources import (
    ComputeBudgetManager,
    MemoryBudgetManager,
    ResourceManager,
    ResourceRegistry,
    SessionResourceManager,
)
from .runtime_coordinator import RuntimeCoordinator
from .runtime_loader import RuntimeLoader
from .runtime_registry import RuntimeRegistry
from .runtime_supervisor import RuntimeSupervisor
from .scheduler import (
    AgentScheduler,
    GlobalScheduler,
    RuntimeScheduler,
    TaskScheduler,
    WorkflowScheduler,
)
from .state import (
    RuntimeStateRegistry,
    SystemSnapshotManager,
    SystemStateManager,
)
from .types import (
    KernelConfiguration,
    KernelContext,
    KernelHealth,
    KernelMetadata,
    KernelRuntime,
    KernelStatistics,
    SystemSnapshot,
)

# Import KernelManager from kernel.py
from .kernel import KernelManager

# Re-export all symbols for backward compatibility
__all__ = [
    # KernelManager (main class)
    "KernelManager",
    # Types
    "KernelRuntime",
    "KernelContext",
    "KernelConfiguration",
    "KernelMetadata",
    "KernelStatistics",
    "KernelHealth",
    "SystemSnapshot",
    # Lifecycle
    "KernelLifecycle",
    "KernelBootstrap",
    # Runtime Management
    "RuntimeSupervisor",
    "RuntimeRegistry",
    "RuntimeLoader",
    "RuntimeCoordinator",
    "RuntimeDependencyManager",
    # Schedulers
    "GlobalScheduler",
    "RuntimeScheduler",
    "AgentScheduler",
    "WorkflowScheduler",
    "TaskScheduler",
    # Resources
    "ResourceManager",
    "ResourceRegistry",
    "MemoryBudgetManager",
    "ComputeBudgetManager",
    "SessionResourceManager",
    # State
    "SystemStateManager",
    "RuntimeStateRegistry",
    "SystemSnapshotManager",
    # Recovery
    "RecoveryManager",
    # Health
    "KernelHealthMonitor",
]
