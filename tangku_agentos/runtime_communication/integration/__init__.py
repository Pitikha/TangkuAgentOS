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
- Runtime integration templates

All runtimes must use this integration layer to communicate with each other.

Example usage:
    from tangku_agentos.runtime_communication.integration import (
        BaseRuntime,
        RuntimeCommunicator,
        RuntimeLifecycleManager,
        SystemEvents,
        SystemCommands,
        SystemQueries,
        LegacyRuntimeAdapter,
        RuntimeCompatibilityLayer,
        RuntimeIntegrationRegistry,
        RuntimeIntegrationMixin,
        IntegratedRuntime,
        create_runtime_config,
        create_runtime_capabilities,
    )

Architecture:
    The integration layer ensures that:
    1. All runtimes communicate ONLY through the Runtime Communication Framework
    2. No runtime directly calls another runtime
    3. All communication goes through the appropriate bus (MessageBus, EventBus, etc.)
    4. Standard events, commands, and queries are used for system-level communication
    5. Backward compatibility is maintained for existing runtimes
"""

# Base classes
from tangku_agentos.runtime_communication.integration.base import (
    BaseRuntime,
    RuntimeCommunicator,
    RuntimeLifecycleManager,
    RuntimeConfig,
    RuntimeCapabilities,
    RuntimeState,
    RuntimeError,
    RuntimeInitializationError,
    RuntimeStartupError,
    RuntimeShutdownError,
    RuntimePauseError,
    RuntimeResumeError,
    RuntimeRestartError,
    RuntimeRegistrationError,
)

# Standard system events
from tangku_agentos.runtime_communication.integration.events import (
    SystemEvent,
    SystemEvents,
)

# Standard system commands
from tangku_agentos.runtime_communication.integration.commands import (
    SystemCommand,
    SystemCommands,
)

# Standard system queries
from tangku_agentos.runtime_communication.integration.queries import (
    SystemQuery,
    SystemQueries,
)

# Backward compatibility adapters
from tangku_agentos.runtime_communication.integration.adapters import (
    LegacyMessage,
    LegacyCommand,
    LegacyQuery,
    MessageAdapter,
    CommandAdapter,
    QueryAdapter,
    LegacyRuntimeAdapter,
    RuntimeCompatibilityLayer,
)

# Integration registry
from tangku_agentos.runtime_communication.integration.registry import (
    RuntimeIntegrationRegistry,
    RuntimeIntegrationStatus,
    RuntimeIntegrationInfo,
)

# Runtime templates
from tangku_agentos.runtime_communication.integration.runtime_template import (
    RuntimeIntegrationMixin,
    IntegratedRuntime,
    create_runtime_config,
    create_runtime_capabilities,
)

__all__ = [
    # Base classes
    "BaseRuntime",
    "RuntimeCommunicator",
    "RuntimeLifecycleManager",
    "RuntimeConfig",
    "RuntimeCapabilities",
    "RuntimeState",
    # Exceptions
    "RuntimeError",
    "RuntimeInitializationError",
    "RuntimeStartupError",
    "RuntimeShutdownError",
    "RuntimePauseError",
    "RuntimeResumeError",
    "RuntimeRestartError",
    "RuntimeRegistrationError",
    # System events
    "SystemEvent",
    "SystemEvents",
    # System commands
    "SystemCommand",
    "SystemCommands",
    # System queries
    "SystemQuery",
    "SystemQueries",
    # Adapters
    "LegacyMessage",
    "LegacyCommand",
    "LegacyQuery",
    "MessageAdapter",
    "CommandAdapter",
    "QueryAdapter",
    "LegacyRuntimeAdapter",
    "RuntimeCompatibilityLayer",
    # Registry
    "RuntimeIntegrationRegistry",
    "RuntimeIntegrationStatus",
    "RuntimeIntegrationInfo",
    # Runtime templates
    "RuntimeIntegrationMixin",
    "IntegratedRuntime",
    "create_runtime_config",
    "create_runtime_capabilities",
]
