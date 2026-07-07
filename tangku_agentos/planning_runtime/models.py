from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class PlanState(Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


@dataclass(frozen=True)
class PlanDependency:
    dependency_id: str
    target: str
    depends_on: str


@dataclass(frozen=True)
class PlanStage:
    stage_id: str
    name: str
    status: str = "pending"
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class PlanCheckpoint:
    checkpoint_id: str
    plan_id: str
    stage_id: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class Plan:
    plan_id: str
    goal: str
    state: PlanState = PlanState.DRAFT
    stages: tuple[PlanStage, ...] = ()
    dependencies: tuple[PlanDependency, ...] = ()
    checkpoints: tuple[PlanCheckpoint, ...] = ()
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class PlanningSession:
    session_id: str
    plan_id: str
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class PlanningContext:
    context_id: str
    subject_id: str
    goal: str
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class PlanningMetadata:
    plan_id: str
    owner: str = "system"
    classification: str = "internal"
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class PlanningConfiguration:
    settings: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)
