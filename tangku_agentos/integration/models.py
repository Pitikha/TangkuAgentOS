from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class SubsystemType(Enum):
    AGENT_OS = "agent_os"
    INTELLIGENCE = "intelligence"
    WORKFLOW = "workflow"
    CAPABILITY = "capability"
    TOOL = "tool"
    MEMORY = "memory"
    KNOWLEDGE = "knowledge"
    MODEL = "model"
    SECURITY = "security"
    OBSERVABILITY = "observability"
    PLUGIN = "plugin"
    SDK = "sdk"
    INTERFACE = "interface"
    DEPLOYMENT = "deployment"


class SubsystemRelationship(Enum):
    DEPENDS_ON = "depends_on"
    PROVIDES = "provides"
    ROUTES_TO = "routes_to"
    PUBLISHES_TO = "publishes_to"
    SUBSCRIBES_TO = "subscribes_to"


@dataclass(frozen=True)
class SubsystemDependency:
    source: SubsystemType
    target: SubsystemType
    relationship: SubsystemRelationship
    description: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class SystemDependencyMap:
    dependencies: List[SubsystemDependency] = field(default_factory=list)


@dataclass(frozen=True)
class FlowRequest:
    request_id: str
    subsystem: SubsystemType
    payload: Dict[str, Any] = field(default_factory=dict)
    context_id: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class FlowResponse:
    request_id: str
    subsystem: SubsystemType
    success: bool
    payload: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None


@dataclass(frozen=True)
class FlowContext:
    context_id: str
    session_id: str
    subsystem: SubsystemType
    data: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class IntegrationMessage:
    message_id: str
    source: SubsystemType
    destination: SubsystemType
    payload: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class IntegrationEvent:
    event_id: str
    source: SubsystemType
    event_type: str
    payload: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: Optional[float] = None


class HealthStatus(Enum):
    OK = "ok"
    WARNING = "warning"
    DEGRADED = "degraded"
    CRITICAL = "critical"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class SystemState:
    state_id: str
    name: str
    values: Dict[str, Any] = field(default_factory=dict)
    status: HealthStatus = HealthStatus.UNKNOWN
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: Optional[float] = None
    updated_at: Optional[float] = None


@dataclass(frozen=True)
class SystemSnapshot:
    snapshot_id: str
    state_id: str
    state_data: Dict[str, Any] = field(default_factory=dict)
    description: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: Optional[float] = None


@dataclass(frozen=True)
class SystemHealth:
    health_id: str
    status: HealthStatus
    summary: str = ""
    metrics: Dict[str, Any] = field(default_factory=dict)
    details: Dict[str, Any] = field(default_factory=dict)
    last_checked: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class SystemConfiguration:
    configuration_id: str
    profile_name: str
    configuration: Dict[str, Any] = field(default_factory=dict)
    effective_rules: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: Optional[float] = None
    updated_at: Optional[float] = None


@dataclass(frozen=True)
class SystemMetrics:
    metric_id: str
    name: str
    value: float
    unit: str = ""
    tags: Dict[str, str] = field(default_factory=dict)
    timestamp: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class SecurityPolicy:
    policy_id: str
    name: str
    description: str = ""
    rules: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class PolicyEvaluationResult:
    policy_id: str
    allowed: bool
    reason: str = ""
    matched_rules: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class PermissionResolutionResult:
    identity_id: str
    effective_permissions: list[str] = field(default_factory=list)
    denied_reasons: list[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class SecurityEventRecord:
    event_id: str
    source: SubsystemType
    event_type: str
    payload: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: Optional[float] = None


@dataclass(frozen=True)
class RiskAggregate:
    aggregate_id: str
    scope: str
    score: float
    severity: HealthStatus = HealthStatus.UNKNOWN
    contributors: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: Optional[float] = None


@dataclass(frozen=True)
class AuditSummary:
    summary_id: str
    scope: str
    entries_count: int
    findings: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    generated_at: Optional[float] = None


@dataclass(frozen=True)
class IntegrationLogEntry:
    entry_id: str
    source: SubsystemType
    level: str
    message: str
    timestamp: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class IntegrationMetricRecord:
    metric_id: str
    source: SubsystemType
    name: str
    value: float
    unit: str = ""
    labels: Dict[str, str] = field(default_factory=dict)
    timestamp: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class TraceSegment:
    trace_id: str
    span_id: str
    parent_span_id: Optional[str] = None
    source: SubsystemType = SubsystemType.AGENT_OS
    operation_name: str = ""
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    attributes: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class TimelineEvent:
    event_id: str
    trace_id: Optional[str] = None
    source: SubsystemType = SubsystemType.AGENT_OS
    event_type: str = ""
    timestamp: Optional[float] = None
    payload: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class IntegrationDiagnosticReport:
    report_id: str
    target: str
    status: HealthStatus
    findings: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    generated_at: Optional[float] = None
