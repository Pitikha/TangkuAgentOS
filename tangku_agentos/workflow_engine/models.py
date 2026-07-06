from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class WorkflowState(Enum):
    CREATED = "created"
    READY = "ready"
    RUNNING = "running"
    WAITING = "waiting"
    PAUSED = "paused"
    CANCELLED = "cancelled"
    COMPLETED = "completed"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"
    ARCHIVED = "archived"


class ExecutionMode(Enum):
    SEQUENTIAL = "sequential"
    PARALLEL = "parallel"


class RetryPolicy(Enum):
    NONE = "none"
    IMMEDIATE = "immediate"
    DELAYED = "delayed"
    EXPONENTIAL_BACKOFF = "exponential_backoff"


class ApprovalType(Enum):
    AUTOMATIC = "automatic"
    HUMAN = "human"


@dataclass(frozen=True)
class WorkflowMetadata:
    name: str = ""
    description: str = ""
    created_by: str = ""
    version: str = ""
    tags: List[str] = field(default_factory=list)
    labels: Dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class WorkflowConfiguration:
    execution_mode: ExecutionMode = ExecutionMode.SEQUENTIAL
    retry_policy: RetryPolicy = RetryPolicy.NONE
    max_retries: int = 0
    checkpoint_enabled: bool = False
    rollback_enabled: bool = False
    schedule_cron: str = ""
    allow_parallel_steps: bool = False


@dataclass(frozen=True)
class WorkflowCondition:
    expression: str
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class WorkflowTriggerDescriptor:
    trigger_type: str
    source: str
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class WorkflowActionDescriptor:
    name: str
    description: str = ""
    parameters: Dict[str, Any] = field(default_factory=dict)
    output_schema: Dict[str, Any] = field(default_factory=dict)
    approval: ApprovalType = ApprovalType.AUTOMATIC


@dataclass(frozen=True)
class WorkflowNode:
    node_id: str
    name: str = ""
    label: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        # ensure backward-compatible `label` when `name` is provided
        if not self.label and self.name:
            object.__setattr__(self, "label", self.name)


@dataclass(frozen=True)
class WorkflowEdge:
    edge_id: str = ""
    source_node_id: str = ""
    target_node_id: str = ""
    condition: Optional[WorkflowCondition] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class WorkflowStep:
    step_id: str
    name: str
    action: WorkflowActionDescriptor
    condition: Optional[WorkflowCondition] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class WorkflowStage:
    stage_id: str
    name: str
    steps: List[WorkflowStep] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class WorkflowAction:
    action_id: str
    descriptor: WorkflowActionDescriptor
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class WorkflowTrigger:
    trigger_id: str
    descriptor: WorkflowTriggerDescriptor
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class WorkflowResult:
    workflow_id: str
    status: WorkflowState
    output: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class Workflow:
    workflow_id: str
    name: str = ""
    description: str = ""
    metadata: WorkflowMetadata = field(default_factory=WorkflowMetadata)
    configuration: WorkflowConfiguration = field(default_factory=WorkflowConfiguration)
    stages: List[WorkflowStage] = field(default_factory=list)
    nodes: List[WorkflowNode] = field(default_factory=list)
    edges: List[WorkflowEdge] = field(default_factory=list)
    triggers: List[WorkflowTrigger] = field(default_factory=list)
    actions: List[WorkflowAction] = field(default_factory=list)


@dataclass
class WorkflowInstance:
    instance_id: str
    workflow: Workflow
    state: WorkflowState
    context: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: str = ""
    updated_at: str = ""
