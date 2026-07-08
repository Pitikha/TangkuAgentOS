"""
Runtime Communication Framework - Runtime Integration Layer

This package provides the integration infrastructure for connecting all
TangkuAgentOS runtimes to the Runtime Communication Framework.

It includes:
- Base runtime classes that all runtimes must inherit from
- Runtime communication mixins
- Standard system events, commands, and queries
- Integration utilities and helpers
- Backward compatibility adapters

All runtimes must use this integration layer to communicate with each other.

Example usage:
    from tangku_agentos.runtime_communication.integration import (
        BaseRuntime,
        RuntimeCommunicator,
        SystemEvents,
        SystemCommands,
        SystemQueries,
    )
"""

from tangku_agentos.runtime_communication.integration.base import (
    BaseRuntime,
    RuntimeCommunicator,
    RuntimeLifecycleManager,
)
from tangku_agentos.runtime_communication.integration.events import SystemEvents
from tangku_agentos.runtime_communication.integration.commands import SystemCommands
from tangku_agentos.runtime_communication.integration.queries import SystemQueries
from tangku_agentos.runtime_communication.integration.adapters import (
    LegacyRuntimeAdapter,
    RuntimeCompatibilityLayer,
)
from tangku_agentos.runtime_communication.integration.registry import RuntimeIntegrationRegistry

__all__ = [
    # Base classes
    "BaseRuntime",
    "RuntimeCommunicator",
    "RuntimeLifecycleManager",
    # System definitions
    "SystemEvents",
    "SystemCommands",
    "SystemQueries",
    # Adapters
    "LegacyRuntimeAdapter",
    "RuntimeCompatibilityLayer",
    # Registry
    "RuntimeIntegrationRegistry",
]
