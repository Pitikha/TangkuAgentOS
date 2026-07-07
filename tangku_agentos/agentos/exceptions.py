from __future__ import annotations


class AgentRuntimeError(Exception):
    """Base exception for AgentOS runtime failures."""


class AgentStateError(AgentRuntimeError):
    """Raised when an invalid agent state transition occurs."""


class AgentLifecycleError(AgentRuntimeError):
    """Raised when lifecycle operations fail."""


class AgentRegistryError(AgentRuntimeError):
    """Raised when agent registry operations fail."""


class AgentPermissionError(AgentRuntimeError):
    """Raised when an agent permission check fails."""
