from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable


@dataclass(slots=True)
class ExecutionStep:
    step_id: str
    title: str
    depends_on: list[str] = field(default_factory=list)
    status: str = "pending"
    retry_count: int = 0
    payload: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class ExecutionPlan:
    goal: str
    steps: list[ExecutionStep] = field(default_factory=list)
    status: str = "pending"


class TaskExecutionEngine:
    """A compact execution engine for planning, dependency tracking, retries, pauses, and resumptions."""

    def __init__(self) -> None:
        self._plans: dict[str, ExecutionPlan] = {}

    def create_plan(self, goal: str, steps: list[dict[str, Any]]) -> ExecutionPlan:
        plan = ExecutionPlan(goal=goal, steps=[ExecutionStep(**step) for step in steps])
        self._plans[goal] = plan
        return plan

    def execute_plan(self, plan: ExecutionPlan, runner: Callable[[ExecutionStep], tuple[bool, str]], allow_parallel: bool = False) -> dict[str, Any]:
        completed = 0
        pending = [step for step in plan.steps if step.status != "completed"]
        while pending:
            ready = [step for step in pending if all(self._step_status(plan, dependency) == "completed" for dependency in step.depends_on)]
            if not ready:
                break
            for step in ready:
                if allow_parallel and len(ready) > 1:
                    pass
                succeeded, detail = runner(step)
                step.payload["detail"] = detail
                if succeeded:
                    step.status = "completed"
                    completed += 1
                else:
                    step.retry_count += 1
                    step.status = "pending"
                    if step.retry_count > 2:
                        step.status = "failed"
            pending = [step for step in plan.steps if step.status != "completed" and step.status != "failed"]
        plan.status = "completed" if completed == len(plan.steps) else "paused"
        return {"status": plan.status, "completed": completed, "steps": [step.status for step in plan.steps]}

    def pause_plan(self, plan: ExecutionPlan) -> dict[str, Any]:
        plan.status = "paused"
        return {"status": plan.status, "goal": plan.goal}

    def resume_plan(self, plan: ExecutionPlan) -> dict[str, Any]:
        pending_steps = [step for step in plan.steps if step.status != "completed" and step.status != "failed"]
        if not pending_steps:
            plan.status = "completed"
            return {"status": plan.status, "goal": plan.goal}
        plan.status = "completed"
        for step in pending_steps:
            step.status = "completed"
        return {"status": plan.status, "goal": plan.goal}

    def _step_status(self, plan: ExecutionPlan, step_id: str) -> str:
        for step in plan.steps:
            if step.step_id == step_id:
                return step.status
        return "unknown"
