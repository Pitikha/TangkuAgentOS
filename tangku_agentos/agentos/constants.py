from __future__ import annotations

from enum import Enum


class AgentState(Enum):
    INITIALIZING = "initializing"
    READY = "ready"
    RUNNING = "running"
    PAUSED = "paused"
    SLEEPING = "sleeping"
    STOPPED = "stopped"
    SHUTTING_DOWN = "shutting_down"
    RECOVERING = "recovering"
    FAILED = "failed"


class AgentStatus(Enum):
    PENDING = "pending"
    ACTIVE = "active"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    ERROR = "error"


class PermissionLevel(Enum):
    NONE = "none"
    READ = "read"
    WRITE = "write"
    EXECUTE = "execute"
    ADMIN = "admin"


class CapabilityType(Enum):
    CORE = "core"
    EXTENSION = "extension"
    THIRD_PARTY = "third_party"
