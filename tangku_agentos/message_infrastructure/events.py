"""
Message and Envelope Models for the Message Bus
"""

from dataclasses import dataclass, field
from typing import Any, Dict, Optional, Set
from datetime import datetime
from enum import Enum
import json


class EventType(Enum):
    """System event types."""
    AGENT_JOINED = "agent.joined"
    AGENT_LEFT = "agent.left"
    PROVIDER_HEALTH_CHANGE = "provider.health_change"
    WORKFLOW_STARTED = "workflow.started"
    WORKFLOW_COMPLETED = "workflow.completed"
    WORKFLOW_FAILED = "workflow.failed"
    TASK_QUEUED = "task.queued"
    TASK_STARTED = "task.started"
    TASK_COMPLETED = "task.completed"
    TASK_FAILED = "task.failed"
    AGENT_MESSAGE = "agent.message"
    SYSTEM_ERROR = "system.error"
    SYSTEM_RECOVERY = "system.recovery"


@dataclass
class SystemEvent:
    """Core system event model."""
    event_id: str = ""
    event_type: EventType = EventType.SYSTEM_ERROR
    source: str = "system"
    timestamp: datetime = field(default_factory=datetime.utcnow)
    severity: str = "info"  # debug, info, warning, error, critical
    data: Dict[str, Any] = field(default_factory=dict)
    correlation_id: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "event_id": self.event_id,
            "event_type": self.event_type.value,
            "source": self.source,
            "timestamp": self.timestamp.isoformat(),
            "severity": self.severity,
            "data": self.data,
            "correlation_id": self.correlation_id,
        }

    def to_json(self) -> str:
        """Convert to JSON."""
        return json.dumps(self.to_dict())


@dataclass
class ProgressEvent:
    """Progress tracking event."""
    progress_id: str = ""
    source: str = ""
    stage: str = ""
    percentage: int = 0
    message: str = ""
    timestamp: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "progress_id": self.progress_id,
            "source": self.source,
            "stage": self.stage,
            "percentage": self.percentage,
            "message": self.message,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata,
        }
