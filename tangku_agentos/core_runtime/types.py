from __future__ import annotations

from dataclasses import dataclass, field
from enum import IntEnum, auto
from typing import (
    Any,
    Awaitable,
    Callable,
    Dict,
    List,
    Optional,
    Protocol,
    runtime_checkable,
    TypeVar,
    Union,
)

# --- Core Types ---
Metadata = Dict[str, Any]


# --- Event Types ---
@dataclass(frozen=True)
class EventPayload:
    """Represents the payload of an event."""

    data: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class EventRecord:
    """Represents a recorded event with metadata."""

    name: str
    payload: EventPayload
    timestamp: float
    metadata: Metadata = field(default_factory=dict)


class EventPriority(IntEnum):
    """Priority levels for events."""

    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4


EventHandler = Callable[[str, EventPayload], None]
AsyncEventHandler = Callable[[str, EventPayload], Awaitable[None]]


@runtime_checkable
class Middleware(Protocol):
    """Protocol for event bus middleware."""

    def __call__(
        self, event_name: str, payload: EventPayload, next_handler: Callable[[], None]
    ) -> None:
        """Process an event before/after the next handler."""
        ...


@runtime_checkable
class AsyncMiddleware(Protocol):
    """Protocol for async event bus middleware."""

    async def __call__(
        self, event_name: str, payload: EventPayload, next_handler: Callable[[], Awaitable[None]]
    ) -> None:
        """Process an event asynchronously before/after the next handler."""
        ...


# --- Configuration Types ---
ConfigValue = Union[str, int, float, bool, None, List["ConfigValue"], Dict[str, "ConfigValue"]]
ConfigKey = str
ConfigData = Dict[ConfigKey, ConfigValue]


@dataclass
class ConfigurationSchema:
    """Schema for configuration validation."""

    defaults: ConfigData = field(default_factory=dict)
    validators: Optional[Dict[ConfigKey, Callable[[Any], bool]]] = None
    required_keys: Optional[List[ConfigKey]] = None
    nested_schemas: Optional[Dict[ConfigKey, "ConfigurationSchema"]] = None


# --- Registry Types ---
RegistryKey = str
RegistryValue = Any


@dataclass
class RegistryEntry:
    """Represents an entry in the registry."""

    key: RegistryKey
    value: RegistryValue
    scope: str
    metadata: Metadata = field(default_factory=dict)
    ttl: Optional[float] = None  # Time-to-live in seconds
    lazy_loader: Optional[Callable[[], RegistryValue]] = None


# --- State Types ---
StateData = Dict[str, Any]


@dataclass
class StateSnapshot:
    """Represents a snapshot of the state."""

    state: StateData = field(default_factory=dict)
    metadata: Metadata = field(default_factory=dict)
    timestamp: float = field(default_factory=lambda: 0.0)
    version: int = 1


class StateChangeType(str):
    """Type of state change."""

    CREATED = "created"
    UPDATED = "updated"
    REMOVED = "removed"
    RESET = "reset"


@runtime_checkable
class StorageBackend(Protocol):
    """Protocol for state storage backends."""

    def save(self, snapshot: StateSnapshot) -> None:
        """Save a state snapshot."""
        ...

    def load(self) -> Optional[StateSnapshot]:
        """Load the latest state snapshot."""
        ...

    def list_snapshots(self) -> List[StateSnapshot]:
        """List all available snapshots."""
        ...


# --- Lifecycle Types ---
LifecycleState = str


@dataclass
class LifecycleMetrics:
    """Metrics for lifecycle management."""

    transition_count: int = 0
    failure_count: int = 0
    last_transition_time: float = 0.0
    current_state: Optional[LifecycleState] = None


# --- Logger Types ---
LogLevel = IntEnum
CorrelationID = str
RequestID = str


@dataclass
class LogContext:
    """Context for structured logging."""

    correlation_id: Optional[CorrelationID] = None
    request_id: Optional[RequestID] = None
    metadata: Metadata = field(default_factory=dict)
