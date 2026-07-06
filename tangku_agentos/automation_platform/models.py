from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict


class AutomationType(Enum):
    SCHEDULED = "scheduled"
    EVENT_DRIVEN = "event_driven"
    MANUAL = "manual"
    BACKGROUND = "background"
    CONTINUOUS = "continuous"
    TRIGGER_BASED = "trigger_based"


@dataclass(frozen=True)
class AutomationDefinition:
    automation_id: str
    name: str
    automation_type: AutomationType
    description: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AutomationSessionModel:
    session_id: str
    automation_id: str
    active: bool = False
    status: str = "created"
    metadata: Dict[str, Any] = field(default_factory=dict)
