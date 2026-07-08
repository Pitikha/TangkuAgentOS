"""Core Kernel foundation for Tangku AgentOS."""

from .base import CoreComponent, Configurable, Monitorable
from .configuration import ConfigurationManager
from .constants import LogLevel, LifecycleEvent, RegistryScope, StateChangeType
from .event_bus import EventBus, EventListener
from .exceptions import (
    CoreError,
    ConfigurationError,
    EventBusError,
    LifecycleError,
    LoggerError,
    RegistryError,
    StateError,
)
from .lifecycle_manager import LifecycleManager
from .logger import Logger
from .registry import Registry
from .state_manager import StateManager
from .types import (
    ConfigData,
    ConfigKey,
    ConfigValue,
    EventHandler,
    EventPayload,
    EventRecord,
    LifecycleState,
    Metadata,
    RegistryEntry,
    RegistryKey,
    RegistryValue,
    StateSnapshot,
)
from .utils import SingletonMeta, validate_identifier, merge_configurations

__all__ = [
    "CoreComponent",
    "Configurable",
    "Monitorable",
    "ConfigurationManager",
    "EventBus",
    "EventListener",
    "Logger",
    "Registry",
    "StateManager",
    "LifecycleManager",
    "LogLevel",
    "LifecycleEvent",
    "RegistryScope",
    "StateChangeType",
    "CoreError",
    "ConfigurationError",
    "EventBusError",
    "LifecycleError",
    "LoggerError",
    "RegistryError",
    "StateError",
    "ConfigData",
    "ConfigKey",
    "ConfigValue",
    "EventHandler",
    "EventPayload",
    "EventRecord",
    "LifecycleState",
    "Metadata",
    "RegistryEntry",
    "RegistryKey",
    "RegistryValue",
    "StateSnapshot",
    "SingletonMeta",
    "validate_identifier",
    "merge_configurations",
]
