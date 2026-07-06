from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from .models import (
    AuditSummary,
    FlowContext,
    FlowRequest,
    FlowResponse,
    HealthStatus,
    IntegrationDiagnosticReport,
    IntegrationEvent,
    IntegrationLogEntry,
    IntegrationMetricRecord,
    IntegrationMessage,
    PermissionResolutionResult,
    PolicyEvaluationResult,
    RiskAggregate,
    SecurityEventRecord,
    SecurityPolicy,
    SubsystemDependency,
    SubsystemType,
    SystemConfiguration,
    SystemDependencyMap,
    SystemHealth,
    SystemMetrics,
    SystemSnapshot,
    SystemState,
)


class IntelligenceIntegration(ABC):
    """Interface for intelligence layer integration."""

    @abstractmethod
    def integrate_intelligence(self) -> None:
        ...


class AgentIntegration(ABC):
    """Interface for agent runtime integration."""

    @abstractmethod
    def integrate_agent_runtime(self) -> None:
        ...


class WorkflowIntegration(ABC):
    """Interface for workflow engine integration."""

    @abstractmethod
    def integrate_workflow(self) -> None:
        ...


class MemoryIntegration(ABC):
    """Interface for memory engine integration."""

    @abstractmethod
    def integrate_memory(self) -> None:
        ...


class KnowledgeIntegration(ABC):
    """Interface for knowledge engine integration."""

    @abstractmethod
    def integrate_knowledge(self) -> None:
        ...


class CapabilityIntegration(ABC):
    """Interface for capability layer integration."""

    @abstractmethod
    def integrate_capability(self) -> None:
        ...


class ToolIntegration(ABC):
    """Interface for tool runtime integration."""

    @abstractmethod
    def integrate_tool_runtime(self) -> None:
        ...


class SecurityIntegration(ABC):
    """Interface for security engine integration."""

    @abstractmethod
    def integrate_security(self) -> None:
        ...


class ObservabilityIntegration(ABC):
    """Interface for observability integration."""

    @abstractmethod
    def integrate_observability(self) -> None:
        ...


class SystemEventBusInterface(ABC):
    """Abstraction for the global system event bus."""

    @abstractmethod
    def subscribe(self, event_name: str, handler: Any) -> None:
        ...

    @abstractmethod
    def unsubscribe(self, event_name: str, handler: Any) -> None:
        ...

    @abstractmethod
    def publish(self, event: IntegrationEvent) -> None:
        ...

    @abstractmethod
    def history(self) -> list[IntegrationEvent]:
        ...


class CrossSubsystemRouterInterface(ABC):
    """Routes messages and requests across Tangku subsystems."""

    @abstractmethod
    def register_route(self, source: SubsystemType, destination: SubsystemType, handler: Any) -> None:
        ...

    @abstractmethod
    def route(self, message: IntegrationMessage) -> IntegrationMessage:
        ...

    @abstractmethod
    def list_routes(self) -> list[dict[str, Any]]:
        ...


class GlobalMessageDispatcherInterface(ABC):
    """Dispatches integration messages across the platform."""

    @abstractmethod
    def dispatch(self, message: IntegrationMessage) -> IntegrationMessage:
        ...

    @abstractmethod
    def broadcast(self, message: IntegrationMessage) -> None:
        ...

    @abstractmethod
    def dispatch_event(self, event: IntegrationEvent) -> None:
        ...


class SystemStateCoordinatorInterface(ABC):
    """Coordinates system state transitions across subsystems."""

    @abstractmethod
    def get_state(self, key: str) -> Any:
        ...

    @abstractmethod
    def update_state(self, key: str, value: Any) -> None:
        ...

    @abstractmethod
    def synchronize_state(self, subsystem: SubsystemType, state: dict[str, Any]) -> None:
        ...

    @abstractmethod
    def list_state_keys(self) -> list[str]:
        ...


class CrossLayerContextSyncInterface(ABC):
    """Synchronizes context between interface, memory, workflow, and model layers."""

    @abstractmethod
    def sync_context(self, context: FlowContext) -> FlowContext:
        ...

    @abstractmethod
    def resolve_conflicts(self, context: FlowContext, candidates: list[FlowContext]) -> FlowContext:
        ...

    @abstractmethod
    def get_context(self, context_id: str) -> FlowContext:
        ...


class SystemDependencyMapInterface(ABC):
    """Defines and resolves subsystem dependency relationships."""

    @abstractmethod
    def register_dependency(self, dependency: SubsystemDependency) -> None:
        ...

    @abstractmethod
    def get_dependencies(self, subsystem: SubsystemType) -> list[SubsystemDependency]:
        ...

    @abstractmethod
    def list_dependencies(self) -> SystemDependencyMap:
        ...


class SystemStateManagerInterface(ABC):
    """Global system state manager abstraction."""

    @abstractmethod
    def get_state(self, state_id: str) -> SystemState:
        ...

    @abstractmethod
    def set_state(self, state: SystemState) -> None:
        ...

    @abstractmethod
    def delete_state(self, state_id: str) -> None:
        ...

    @abstractmethod
    def list_states(self) -> list[SystemState]:
        ...

    @abstractmethod
    def snapshot_state(self, state_id: str) -> SystemSnapshot:
        ...

    @abstractmethod
    def restore_snapshot(self, snapshot_id: str) -> None:
        ...

    @abstractmethod
    def list_state_snapshots(self, state_id: str | None = None) -> list[SystemSnapshot]:
        ...


class GlobalStateRegistryInterface(ABC):
    """Registry for global system state objects."""

    @abstractmethod
    def register_state(self, state: SystemState) -> None:
        ...

    @abstractmethod
    def lookup_state(self, key: str) -> SystemState | None:
        ...

    @abstractmethod
    def list_registered_states(self) -> list[SystemState]:
        ...

    @abstractmethod
    def unregister_state(self, state_id: str) -> None:
        ...


class SystemSnapshotManagerInterface(ABC):
    """Manages system snapshots and restore points."""

    @abstractmethod
    def create_snapshot(self, state_id: str, description: str = "") -> SystemSnapshot:
        ...

    @abstractmethod
    def retrieve_snapshot(self, snapshot_id: str) -> SystemSnapshot:
        ...

    @abstractmethod
    def compare_snapshots(self, base_snapshot_id: str, target_snapshot_id: str) -> dict[str, Any]:
        ...

    @abstractmethod
    def list_snapshots(self, state_id: str | None = None) -> list[SystemSnapshot]:
        ...

    @abstractmethod
    def prune_snapshots(self, keep_last: int) -> None:
        ...


class SystemRecoveryManagerInterface(ABC):
    """Manages recovery plans and restore procedures."""

    @abstractmethod
    def plan_recovery(self, snapshot_id: str, reason: str) -> dict[str, Any]:
        ...

    @abstractmethod
    def execute_recovery(self, recovery_plan: dict[str, Any]) -> bool:
        ...

    @abstractmethod
    def validate_recovery(self, recovery_plan: dict[str, Any]) -> bool:
        ...

    @abstractmethod
    def rollback_recovery(self, recovery_id: str) -> bool:
        ...

    @abstractmethod
    def get_recovery_history(self) -> list[dict[str, Any]]:
        ...


class SystemHealthCoordinatorInterface(ABC):
    """Coordinates health state and system-wide health checks."""

    @abstractmethod
    def evaluate_health(self) -> SystemHealth:
        ...

    @abstractmethod
    def update_health(self, health: SystemHealth) -> None:
        ...

    @abstractmethod
    def get_health_report(self) -> SystemHealth:
        ...

    @abstractmethod
    def register_health_check(self, check_name: str, metadata: dict[str, Any]) -> None:
        ...

    @abstractmethod
    def list_health_checks(self) -> list[dict[str, Any]]:
        ...


class GlobalPolicyEngineInterface(ABC):
    """Cross-system policy evaluation and enforcement."""

    @abstractmethod
    def register_policy(self, policy: SecurityPolicy) -> None:
        ...

    @abstractmethod
    def evaluate_policy(self, policy_id: str, context: dict[str, Any]) -> PolicyEvaluationResult:
        ...

    @abstractmethod
    def enforce_policy(self, policy_id: str, context: dict[str, Any]) -> bool:
        ...

    @abstractmethod
    def list_policies(self) -> list[SecurityPolicy]:
        ...

    @abstractmethod
    def resolve_policy_conflict(self, policy_ids: list[str], context: dict[str, Any]) -> PolicyEvaluationResult:
        ...


class CrossSystemPermissionResolverInterface(ABC):
    """Resolves permission visibility across Tangku subsystems."""

    @abstractmethod
    def resolve_permissions(self, identity_id: str, resource: str, action: str) -> PermissionResolutionResult:
        ...

    @abstractmethod
    def check_access(self, identity_id: str, permission: str, resource: str) -> bool:
        ...

    @abstractmethod
    def map_permission_context(self, context: dict[str, Any]) -> dict[str, Any]:
        ...

    @abstractmethod
    def get_effective_permissions(self, identity_id: str) -> list[str]:
        ...


class SecurityEventRouterInterface(ABC):
    """Routes security events through the integration layer."""

    @abstractmethod
    def publish_security_event(self, event: SecurityEventRecord) -> None:
        ...

    @abstractmethod
    def route_security_event(self, event: SecurityEventRecord) -> None:
        ...

    @abstractmethod
    def subscribe_security_event(self, event_type: str, handler: Any) -> None:
        ...

    @abstractmethod
    def list_security_routes(self) -> list[dict[str, Any]]:
        ...


class RiskAggregationManagerInterface(ABC):
    """Aggregates and normalizes security risk across system boundaries."""

    @abstractmethod
    def aggregate_risk(self, context: dict[str, Any]) -> RiskAggregate:
        ...

    @abstractmethod
    def list_risk_summaries(self) -> list[RiskAggregate]:
        ...

    @abstractmethod
    def register_risk_source(self, source_name: str, metadata: dict[str, Any]) -> None:
        ...

    @abstractmethod
    def get_risk_score(self, scope: str) -> float:
        ...


class AuditAggregatorInterface(ABC):
    """Collects and summarizes audit activity from multiple subsystems."""

    @abstractmethod
    def record_audit_event(self, audit_record: AuditSummary) -> None:
        ...

    @abstractmethod
    def query_audit_events(self, filters: dict[str, Any]) -> list[AuditSummary]:
        ...

    @abstractmethod
    def summarize_audit_trail(self, scope: str) -> AuditSummary:
        ...

    @abstractmethod
    def export_audit_summary(self, scope: str) -> dict[str, Any]:
        ...


class UnifiedLoggingSystemInterface(ABC):
    """Unified cross-system logging contract."""

    @abstractmethod
    def log(self, entry: IntegrationLogEntry) -> None:
        ...

    @abstractmethod
    def query_logs(self, filters: dict[str, Any]) -> list[IntegrationLogEntry]:
        ...

    @abstractmethod
    def register_log_sink(self, sink_name: str, metadata: dict[str, Any]) -> None:
        ...

    @abstractmethod
    def list_log_sinks(self) -> list[dict[str, Any]]:
        ...


class GlobalMetricsAggregatorInterface(ABC):
    """Global metric collection and aggregation abstractions."""

    @abstractmethod
    def collect_metric(self, metric: IntegrationMetricRecord) -> None:
        ...

    @abstractmethod
    def query_metrics(self, name: str, start_time: float | None = None, end_time: float | None = None) -> list[SystemMetrics]:
        ...

    @abstractmethod
    def aggregate_metrics(self, name: str, interval: str) -> dict[str, Any]:
        ...

    @abstractmethod
    def register_metric_source(self, source: str, metadata: dict[str, Any]) -> None:
        ...


class DistributedTraceCoordinatorInterface(ABC):
    """Coordinates distributed trace propagation."""

    @abstractmethod
    def start_trace(self, trace: TraceSegment) -> None:
        ...

    @abstractmethod
    def continue_trace(self, trace_id: str, span: TraceSegment) -> None:
        ...

    @abstractmethod
    def finish_trace(self, trace_id: str) -> None:
        ...

    @abstractmethod
    def get_trace(self, trace_id: str) -> TraceSegment:
        ...


class EventTimelineSystemInterface(ABC):
    """Manages event timelines and correlation across subsystems."""

    @abstractmethod
    def record_event(self, event: TimelineEvent) -> None:
        ...

    @abstractmethod
    def query_timeline(self, start_time: float | None = None, end_time: float | None = None) -> list[TimelineEvent]:
        ...

    @abstractmethod
    def correlate_events(self, correlation_id: str) -> list[TimelineEvent]:
        ...

    @abstractmethod
    def build_timeline(self, scope: str) -> list[TimelineEvent]:
        ...


class SystemDiagnosticsEngineInterface(ABC):
    """Runs system diagnostics and health assessments."""

    @abstractmethod
    def run_diagnostics(self, target: str) -> IntegrationDiagnosticReport:
        ...

    @abstractmethod
    def retrieve_diagnostics_report(self, report_id: str) -> IntegrationDiagnosticReport:
        ...

    @abstractmethod
    def schedule_diagnostics(self, target: str, interval_seconds: int) -> str:
        ...

    @abstractmethod
    def get_diagnostic_history(self, target: str) -> list[IntegrationDiagnosticReport]:
        ...


class SubsystemFlow(ABC):
    """Base contract for a subsystem execution flow."""

    @abstractmethod
    def execute(self, request: FlowRequest) -> FlowResponse:
        ...

    @abstractmethod
    def get_context(self, request_id: str) -> FlowContext:
        ...


class AgentRuntimeFlow(SubsystemFlow):
    """Represents the agent runtime execution flow."""

    @abstractmethod
    def execute_agent(self, request: FlowRequest) -> FlowResponse:
        ...


class WorkflowExecutionFlow(SubsystemFlow):
    """Represents workflow execution and orchestration."""

    @abstractmethod
    def execute_workflow(self, request: FlowRequest) -> FlowResponse:
        ...


class CapabilityExecutionFlow(SubsystemFlow):
    """Represents capability execution flow."""

    @abstractmethod
    def execute_capability(self, request: FlowRequest) -> FlowResponse:
        ...


class ToolExecutionFlow(SubsystemFlow):
    """Represents the tool execution flow."""

    @abstractmethod
    def execute_tool(self, request: FlowRequest) -> FlowResponse:
        ...


class MemoryFlow(SubsystemFlow):
    """Represents memory read/write flow."""

    @abstractmethod
    def persist_memory(self, request: FlowRequest) -> FlowResponse:
        ...

    @abstractmethod
    def retrieve_memory(self, request: FlowRequest) -> FlowResponse:
        ...


class KnowledgeFlow(SubsystemFlow):
    """Represents knowledge retrieval and enrichment flow."""

    @abstractmethod
    def query_knowledge(self, request: FlowRequest) -> FlowResponse:
        ...

    @abstractmethod
    def update_knowledge(self, request: FlowRequest) -> FlowResponse:
        ...


class ContextAssemblyFlow(SubsystemFlow):
    """Represents context assembly and synchronization flow."""

    @abstractmethod
    def assemble_context(self, request: FlowRequest) -> FlowResponse:
        ...


class ModelExecutionFlow(SubsystemFlow):
    """Represents the model execution flow."""

    @abstractmethod
    def execute_model(self, request: FlowRequest) -> FlowResponse:
        ...


class PluginExecutionFlow(SubsystemFlow):
    """Represents plugin invocation and extension flow."""

    @abstractmethod
    def execute_plugin(self, request: FlowRequest) -> FlowResponse:
        ...


class EventPropagationFlow(SubsystemFlow):
    """Represents event propagation across subsystems."""

    @abstractmethod
    def propagate_event(self, event: IntegrationEvent) -> FlowResponse:
        ...


class SystemIntegration(ABC):
    """Interface for end-to-end platform integration."""

    @abstractmethod
    def initialize(self) -> None:
        ...

    @abstractmethod
    def connect_interface_layer(self) -> None:
        ...

    @abstractmethod
    def connect_deployment_layer(self) -> None:
        ...

    @abstractmethod
    def connect_security(self) -> None:
        ...

    @abstractmethod
    def connect_observability(self) -> None:
        ...

    @abstractmethod
    def synchronize_sessions(self) -> None:
        ...

    @abstractmethod
    def route_events(self) -> None:
        ...

    @abstractmethod
    def publish_lifecycle_state(self) -> None:
        ...

    @abstractmethod
    def get_global_bus(self) -> SystemEventBusInterface:
        ...

    @abstractmethod
    def get_router(self) -> CrossSubsystemRouterInterface:
        ...

    @abstractmethod
    def get_dispatcher(self) -> GlobalMessageDispatcherInterface:
        ...

    @abstractmethod
    def get_state_coordinator(self) -> SystemStateCoordinatorInterface:
        ...

    @abstractmethod
    def get_context_sync(self) -> CrossLayerContextSyncInterface:
        ...

    @abstractmethod
    def get_dependency_map(self) -> SystemDependencyMapInterface:
        ...

    @abstractmethod
    def map_subsystem_relationship(self, dependency: SubsystemDependency) -> None:
        ...
