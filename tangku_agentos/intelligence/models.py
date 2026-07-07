from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List


class IntelligenceState(Enum):
    PENDING = "pending"
    ACTIVE = "active"
    COMPLETED = "completed"
    FAILED = "failed"


class PlanPhase(Enum):
    DISCOVERY = "discovery"
    PLANNING = "planning"
    EXECUTION = "execution"
    REVIEW = "review"


class LearningState(Enum):
    INITIATED = "initiated"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    REVIEW = "review"


@dataclass(frozen=True)
class IntelligenceMetadata:
    created_by: str
    created_at: str
    tags: List[str] = field(default_factory=list)
    annotations: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ConfidenceScore:
    score: float
    rationale: str = ""


@dataclass(frozen=True)
class DecisionRecord:
    decision_id: str
    agent_id: str
    outcome: str
    reasoning: str
    confidence: ConfidenceScore


@dataclass(frozen=True)
class IntelligenceGoal:
    goal_id: str
    description: str
    priority: int = 0
    deadline: str | None = None
    metadata: IntelligenceMetadata | None = None


@dataclass(frozen=True)
class IntelligenceTask:
    task_id: str
    description: str
    goal_id: str
    assigned_agent: str | None = None
    metadata: IntelligenceMetadata | None = None


@dataclass(frozen=True)
class IntelligencePlan:
    plan_id: str
    goal_id: str
    tasks: List[IntelligenceTask] = field(default_factory=list)
    phases: List[PlanPhase] = field(default_factory=list)
    metadata: IntelligenceMetadata | None = None


@dataclass(frozen=True)
class IntelligenceRequest:
    request_id: str
    plan: IntelligencePlan | None = None
    goal: IntelligenceGoal | None = None
    task: IntelligenceTask | None = None
    context: Dict[str, Any] = field(default_factory=dict)
    metadata: IntelligenceMetadata | None = None


@dataclass(frozen=True)
class IntelligenceResult:
    success: bool
    message: str = ""
    details: Dict[str, Any] = field(default_factory=dict)
    confidence: ConfidenceScore | None = None


@dataclass(frozen=True)
class IntelligenceResponse:
    request_id: str
    result: IntelligenceResult
    metadata: IntelligenceMetadata | None = None


@dataclass(frozen=True)
class PlanPhaseDefinition:
    phase: PlanPhase
    description: str


@dataclass(frozen=True)
class PlanGraph:
    plan_id: str
    nodes: List[str] = field(default_factory=list)
    edges: List[tuple[str, str]] = field(default_factory=list)


@dataclass(frozen=True)
class PlanDependencyGraph:
    plan_id: str
    dependencies: List[tuple[str, str]] = field(default_factory=list)


@dataclass(frozen=True)
class Milestone:
    milestone_id: str
    description: str
    completed: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class PlanningContext:
    context_id: str
    environment: Dict[str, Any] = field(default_factory=dict)
    preferences: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class Plan:
    plan_id: str
    name: str
    goals: List[str] = field(default_factory=list)
    milestones: List[Milestone] = field(default_factory=list)
    metadata: IntelligenceMetadata | None = None


@dataclass(frozen=True)
class Goal:
    goal_id: str
    description: str
    importance: int = 0
    metadata: IntelligenceMetadata | None = None


@dataclass(frozen=True)
class Objective:
    objective_id: str
    description: str
    related_goal: str
    metadata: IntelligenceMetadata | None = None


@dataclass(frozen=True)
class PreferenceProfile:
    profile_id: str
    preferences: Dict[str, Any] = field(default_factory=dict)
    weights: Dict[str, float] = field(default_factory=dict)


@dataclass(frozen=True)
class OptimizationRecord:
    record_id: str
    plan_id: str
    metrics: Dict[str, Any] = field(default_factory=dict)
    optimized_at: str | None = None


@dataclass(frozen=True)
class ReasoningSession:
    session_id: str
    plan_id: str
    inputs: Dict[str, Any] = field(default_factory=dict)
    results: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ReasoningStrategy:
    strategy_id: str
    name: str
    description: str = ""
    parameters: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class IntelligenceDecision:
    decision_id: str
    request_id: str
    decision: str
    rationale: str
    confidence: ConfidenceScore


@dataclass(frozen=True)
class LearningRecord:
    record_id: str
    session_id: str
    observations: Dict[str, Any] = field(default_factory=dict)
    outcome: str = ""


@dataclass(frozen=True)
class LearningSession:
    session_id: str
    goal_id: str
    state: LearningState = LearningState.INITIATED
    records: List[LearningRecord] = field(default_factory=list)


@dataclass(frozen=True)
class ReflectionReport:
    report_id: str
    summary: str
    suggestions: List[str] = field(default_factory=list)


@dataclass(frozen=True)
class VerificationResult:
    verified: bool
    issues: List[str] = field(default_factory=list)
    details: Dict[str, Any] = field(default_factory=dict)
