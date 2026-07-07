from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class ReasoningMode(Enum):
    SEQUENTIAL = "sequential"
    TREE = "tree"
    GRAPH = "graph"
    REFLECTIVE = "reflective"


@dataclass(frozen=True)
class ReasoningContext:
    context_id: str
    subject_id: str
    mode: ReasoningMode = ReasoningMode.SEQUENTIAL
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ReasoningSession:
    session_id: str
    context_id: str
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ReasoningMetadata:
    session_id: str
    owner: str = "system"
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ReasoningStep:
    step_id: str
    content: str
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ReasoningTrace:
    trace_id: str
    steps: tuple[ReasoningStep, ...] = ()
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ReasoningDecision:
    decision_id: str
    trace_id: str
    decision_type: str
    selected: str
    alternatives: list[str] = field(default_factory=list)
    confidence: float = 0.0
    reasoning: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class ReasoningStatistics:
    traces_executed: int = 0
    steps_executed: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)
