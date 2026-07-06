from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Iterable, Mapping

from .models import (
    ConfidenceScore,
    DecisionRecord,
    IntelligenceGoal,
    IntelligenceMetadata,
    IntelligencePlan,
    IntelligenceRequest,
    IntelligenceResponse,
    IntelligenceResult,
    IntelligenceTask,
    LearningSession,
    Plan,
    PlanningContext,
    ReflectionReport,
    VerificationResult,
)


class IntelligenceManagerInterface(ABC):
    """Interface for core intelligence management."""

    @abstractmethod
    def register_goal(self, goal: IntelligenceGoal) -> None:
        ...

    @abstractmethod
    def evaluate_plan(self, plan: IntelligencePlan) -> IntelligenceResult:
        ...

    @abstractmethod
    def reason_over(self, context: PlanningContext) -> IntelligenceResult:
        ...

    @abstractmethod
    def orchestrate(self, request: IntelligenceRequest) -> IntelligenceResponse:
        ...


class IntelligenceRegistryInterface(ABC):
    """Interface for intelligence component registration."""

    @abstractmethod
    def register(self, key: str, value: Any) -> None:
        ...

    @abstractmethod
    def resolve(self, key: str) -> Any:
        ...

    @abstractmethod
    def list_registered(self) -> list[str]:
        ...


class AgentCoordinator(ABC):
    """Interface for multi-agent coordination."""

    @abstractmethod
    def coordinate(self, tasks: Iterable[IntelligenceTask]) -> list[IntelligenceTask]:
        ...


class AgentScheduler(ABC):
    """Interface for scheduling agent work."""

    @abstractmethod
    def schedule(self, task: IntelligenceTask, cron_expression: str) -> None:
        ...

    @abstractmethod
    def unschedule(self, task_id: str) -> None:
        ...


class AgentSelector(ABC):
    """Interface for selecting the right agent for a task."""

    @abstractmethod
    def select(self, task: IntelligenceTask) -> str:
        ...


class AgentLoadBalancer(ABC):
    """Interface for distributing tasks across agents."""

    @abstractmethod
    def balance(self, tasks: list[IntelligenceTask]) -> list[IntelligenceTask]:
        ...


class AgentHealthMonitor(ABC):
    """Interface for monitoring agent health."""

    @abstractmethod
    def check_agent(self, agent_id: str) -> dict[str, Any]:
        ...


class AgentRecoveryManager(ABC):
    """Interface for managing agent recovery and fallback."""

    @abstractmethod
    def recover(self, agent_id: str) -> None:
        ...


class ConsensusManager(ABC):
    """Interface for coordinating consensus among agents."""

    @abstractmethod
    def propose(self, value: Any) -> bool:
        ...

    @abstractmethod
    def agree(self, proposal_id: str) -> bool:
        ...


class ConflictResolutionManager(ABC):
    """Interface for resolving multi-agent conflicts."""

    @abstractmethod
    def resolve(self, conflicts: list[str]) -> list[str]:
        ...


class SupervisorAgent(ABC):
    """Interface for supervisory agent behavior."""

    @abstractmethod
    def supervise(self, agents: list[str]) -> None:
        ...


class PolicyEvaluator(ABC):
    """Interface for evaluating governance policies."""

    @abstractmethod
    def evaluate(self, plan: IntelligencePlan, preferences: dict[str, Any]) -> ConfidenceScore:
        ...


class PriorityEvaluator(ABC):
    """Interface for calculating plan or task priority."""

    @abstractmethod
    def evaluate(self, task: IntelligenceTask) -> int:
        ...


class RuleEngine(ABC):
    """Interface for applying rule-based reasoning."""

    @abstractmethod
    def apply_rules(self, context: PlanningContext) -> IntelligenceResult:
        ...


class StrategyManager(ABC):
    """Interface for managing intelligence strategies."""

    @abstractmethod
    def choose_strategy(self, context: PlanningContext) -> str:
        ...


class Scheduler(ABC):
    """Generic scheduling interface."""

    @abstractmethod
    def schedule(self, objective: IntelligenceGoal) -> Plan:
        ...


class WorkflowLearning(ABC):
    """Interface for learning from workflow execution."""

    @abstractmethod
    def analyze(self, instance_id: str, outcome: str) -> LearningSession:
        ...


class ToolMessageBus(ABC):
    """Interface for agent/tool messaging bus."""

    @abstractmethod
    def publish(self, message: IntelligenceRequest) -> None:
        ...

    @abstractmethod
    def subscribe(self, channel: str) -> None:
        ...


class IntelligenceContext(ABC):
    """Interface for intelligence context management."""

    @abstractmethod
    def get_context(self) -> dict[str, Any]:
        ...

    @abstractmethod
    def update_context(self, updates: dict[str, Any]) -> None:
        ...


class IntelligenceConfiguration(ABC):
    """Interface for intelligence configuration management."""

    @abstractmethod
    def get(self, key: str) -> Any:
        ...

    @abstractmethod
    def set(self, key: str, value: Any) -> None:
        ...


class IntelligenceSession(ABC):
    """Interface representing an intelligence session."""

    @abstractmethod
    def start(self) -> None:
        ...

    @abstractmethod
    def end(self) -> None:
        ...


class IntelligenceCoordinator(ABC):
    """Interface for intelligence orchestration coordination."""

    @abstractmethod
    def coordinate(self, request: IntelligenceRequest) -> IntelligenceResponse:
        ...


class LearningManager(ABC):
    """Interface for intelligence learning management."""

    @abstractmethod
    def record(self, session: LearningSession) -> None:
        ...

    @abstractmethod
    def summarize(self, goal: IntelligenceGoal) -> ReflectionReport:
        ...


class ReasoningManager(ABC):
    """Interface for intelligence reasoning management."""

    @abstractmethod
    def infer(self, plan: IntelligencePlan) -> IntelligenceResult:
        ...


class Planner(ABC):
    """Interface for planning and goal decomposition."""

    @abstractmethod
    def create_plan(self, goal: IntelligenceGoal) -> IntelligencePlan:
        ...


class Orchestrator(ABC):
    """Interface for multi-agent orchestration."""

    @abstractmethod
    def orchestrate(self, tasks: list[IntelligenceTask]) -> list[IntelligenceTask]:
        ...


class DecisionManager(ABC):
    """Interface for decision-making in intelligence workflows."""

    @abstractmethod
    def decide(self, request: IntelligenceRequest) -> IntelligenceResponse:
        ...


class ConstitutionManager(ABC):
    """Interface for governance and constitutional oversight."""

    @abstractmethod
    def validate(self, plan: IntelligencePlan) -> VerificationResult:
        ...


class IntelligenceRouter(ABC):
    """Interface for routing intelligence interactions."""

    @abstractmethod
    def resolve(self, request: IntelligenceRequest) -> IntelligenceResponse:
        ...
