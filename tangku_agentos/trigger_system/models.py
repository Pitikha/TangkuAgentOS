from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict


@dataclass(frozen=True)
class Trigger:
    trigger_id: str
    trigger_type: str
    source: str
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TriggerContext:
    trigger: Trigger
    payload: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class TriggerResult:
    trigger_id: str
    success: bool
    details: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
