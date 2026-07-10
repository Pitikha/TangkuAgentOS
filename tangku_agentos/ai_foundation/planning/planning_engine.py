"""
Planning Engine for TangkuAgentOS AI Foundation Framework.

Creates and manages execution plans for tasks.
"""
from typing import Any, Optional, Dict, List
from dataclasses import dataclass, field
import logging
from enum import Enum
from ..reasoning.reasoning_engine import ReasoningEngine

logger = logging.getLogger(__name__)


class TaskStatus(Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class Task:
    task_id: str
    description: str
    dependencies: List[str] = field(default_factory=list)
    status: TaskStatus = TaskStatus.PENDING
    result: Optional[Any] = None
    error: Optional[str] = None


@dataclass
class ExecutionPlan:
    plan_id: str
    goal: str
    tasks: List[Task]
    status: TaskStatus = TaskStatus.PENDING
    current_task_index: int = 0


class PlanningEngine:
    def __init__(self, reasoning_engine: ReasoningEngine):
        self._reasoning_engine = reasoning_engine
        self._plans: Dict[str, ExecutionPlan] = {}
        logger.info("PlanningEngine initialized.")

    async def create_plan(
        self,
        goal: str,
        constraints: Optional[List[str]] = None,
        **kwargs: Any,
    ) -> ExecutionPlan:
        reasoning_result = await self._reasoning_engine.plan(goal, constraints)
        plan_data = reasoning_result.output
        tasks = []
        for i, step in enumerate(plan_data.get("plan", [])):
            task_id = f"task_{i}"
            tasks.append(
                Task(
                    task_id=task_id,
                    description=step.get("action", step),
                    dependencies=step.get("dependencies", []),
                )
            )
        plan_id = f"plan_{len(self._plans)}"
        plan = ExecutionPlan(
            plan_id=plan_id,
            goal=goal,
            tasks=tasks,
        )
        self._plans[plan_id] = plan
        logger.info(f"Created plan {plan_id} for goal: {goal[:50]}...")
        return plan

    def get_plan(self, plan_id: str) -> Optional[ExecutionPlan]:
        return self._plans.get(plan_id)

    def update_task_status(
        self,
        plan_id: str,
        task_id: str,
        status: TaskStatus,
        result: Optional[Any] = None,
        error: Optional[str] = None,
    ) -> bool:
        plan = self._plans.get(plan_id)
        if not plan:
            return False
        for task in plan.tasks:
            if task.task_id == task_id:
                task.status = status
                task.result = result
                task.error = error
                logger.info(f"Updated task {task_id} in plan {plan_id} to status: {status.value}")
                return True
        return False

    def get_next_task(self, plan_id: str) -> Optional[Task]:
        plan = self._plans.get(plan_id)
        if not plan:
            return None
        for task in plan.tasks:
            if task.status == TaskStatus.PENDING:
                return task
        return None
