from __future__ import annotations

from enum import Enum, IntEnum

# --- Logging Constants ---
DEFAULT_LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
JSON_LOG_FORMAT = "{"timestamp": "%(asctime)s", "name": "%(name)s", "level": "%(levelname)s", "message": "%(message)s", "metadata": %(metadata)s}"
DEFAULT_CONFIG_NAMESPACE = "tangku"
CORE_KERNEL_NAMESPACE = "tangku_agentos.core_runtime"


# --- Log Levels ---
class LogLevel(IntEnum):
    """Standard log levels for the system."""

    DEBUG = 10
    INFO = 20
    WARNING = 30
    ERROR = 40
    CRITICAL = 50


# --- Log Formats ---
class LogFormat(Enum):
    """Supported log output formats."""

    TEXT = "text"
    JSON = "json"


# --- Lifecycle Events ---
class LifecycleEvent(Enum):
    """Events for the lifecycle manager."""

    INITIALIZING = "initializing"
    STARTING = "starting"
    RUNNING = "running"
    PAUSING = "pausing"
    STOPPING = "stopping"
    STOPPED = "stopped"
    FAILED = "failed"


# --- Registry Scopes ---
class RegistryScope(Enum):
    """Scopes for registry entries."""

    GLOBAL = "global"
    SESSION = "session"
    COMPONENT = "component"


# --- State Change Types ---
class StateChangeType(Enum):
    """Types of state changes."""

    CREATED = "created"
    UPDATED = "updated"
    REMOVED = "removed"
    RESET = "reset"


# --- Event Priorities ---
class EventPriority(IntEnum):
    """Priority levels for events."""

    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4


# --- Storage Backend Types ---
class StorageBackendType(Enum):
    """Types of storage backends for state persistence."""

    IN_MEMORY = "in_memory"
    FILE = "file"
    DATABASE = "database"
    CLOUD = "cloud"
