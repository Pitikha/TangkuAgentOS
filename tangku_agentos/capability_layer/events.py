from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict

from ..core_runtime.event_bus import EventBus
from .interfaces import CapabilityEventManager


class CapabilityEventType(Enum):
    REQUESTED = "capability.requested"
    RESOLVED = "capability.resolved"
    DISPATCHED = "capability.dispatched"
    COMPLETED = "capability.completed"
    FAILED = "capability.failed"
    PERMISSION_CHECK = "capability.permission_check"


class CapabilityEventPriority(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass(frozen=True)
class CapabilityEvent:
    event_type: CapabilityEventType
    request_id: str
    capability_name: str
    payload: Dict[str, Any] = field(default_factory=dict)
    priority: CapabilityEventPriority = CapabilityEventPriority.MEDIUM
    metadata: Dict[str, Any] = field(default_factory=dict)


class CapabilityEventManagerImpl(CapabilityEventManager):
    """Adapter to publish capability events through the core kernel event bus."""

    def __init__(self, event_bus: EventBus) -> None:
        self._event_bus = event_bus

    def publish(self, event_name: str, payload: Dict[str, Any]) -> None:
        self._event_bus.publish(event_name, payload or {}, metadata={"source": "capability_layer"})
