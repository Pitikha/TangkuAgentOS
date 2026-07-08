from __future__ import annotations

from enum import Enum, IntEnum


DEFAULT_LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
DEFAULT_CONFIG_NAMESPACE = "tangku"
CORE_KERNEL_NAMESPACE = "tangku_agentos.core_runtime"


class LogLevel(IntEnum):
    DEBUG = 10
    INFO = 20
    WARNING = 30
    ERROR = 40
    CRITICAL = 50


class LifecycleEvent(Enum):
    INITIALIZING = "initializing"
    STARTING = "starting"
    RUNNING = "running"
    PAUSING = "pausing"
    STOPPING = "stopping"
    STOPPED = "stopped"
    FAILED = "failed"


class RegistryScope(Enum):
    GLOBAL = "global"
    SESSION = "session"
    COMPONENT = "component"


class StateChangeType(Enum):
    CREATED = "created"
    UPDATED = "updated"
    REMOVED = "removed"
    RESET = "reset"
