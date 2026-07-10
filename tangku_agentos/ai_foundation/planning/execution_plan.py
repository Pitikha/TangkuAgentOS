"""
Execution Plan for TangkuAgentOS AI Foundation Framework.

Represents and manages execution plans for tasks.
"""
from typing import Any, Optional, Dict, List
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class PlanStatus(Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class ExecutionStep:
    """Represents a single step in an execution plan."""
    step_id: str
    description: str
    dependencies: List[str] = field(default_factory=list)
    status: PlanStatus = PlanStatus.PENDING
    result: Optional[Any] = None
    error: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


@dataclass
class ExecutionPlan:
    """Represents an execution plan for a task or goal."""
    plan_id: str
    goal: str
    steps: List[ExecutionStep] = field(default_factory=list)
    status: PlanStatus = PlanStatus.PENDING
    current_step_index: int = 0
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def add_step(
        self,
        step_id: str,
        description: str,
        dependencies: Optional[List[str]] = None,
    ) -> None:
        """Add a step to the execution plan.

        Args:
            step_id: The ID of the step.
            description: The description of the step.
            dependencies: List of step IDs this step depends on.
        """
        step = ExecutionStep(
            step_id=step_id,
            description=description,
            dependencies=dependencies or [],
        )
        self.steps.append(step)
        self.updated_at = datetime.utcnow()

    def get_step(self, step_id: str) -> Optional[ExecutionStep]:
        """Retrieve a step by its ID.

        Args:
            step_id: The ID of the step.

        Returns:
            The ExecutionStep if found, otherwise None.
        """
        for step in self.steps:
            if step.step_id == step_id:
                return step
        return None

    def update_step_status(
        self,
        step_id: str,
        status: PlanStatus,
        result: Optional[Any] = None,
        error: Optional[str] = None,
    ) -> bool:
        """Update the status of a step.

        Args:
            step_id: The ID of the step to update.
            status: The new status for the step.
            result: Optional result of the step.
            error: Optional error message if the step failed.

        Returns:
            True if the step was updated, False otherwise.
        """
        step = self.get_step(step_id)
        if step:
            step.status = status
            step.result = result
            step.error = error
            if status == PlanStatus.IN_PROGRESS:
                step.started_at = datetime.utcnow()
            elif status in (PlanStatus.COMPLETED, PlanStatus.FAILED):
                step.completed_at = datetime.utcnow()
            self.updated_at = datetime.utcnow()
            return True
        return False

    def get_next_step(self) -> Optional[ExecutionStep]:
        """Get the next pending step in the plan.

        Returns:
            The next ExecutionStep if found, otherwise None.
        """
        for step in self.steps:
            if step.status == PlanStatus.PENDING:
                return step
        return None

    def get_completed_steps(self) -> List[ExecutionStep]:
        """Get all completed steps in the plan.

        Returns:
            List of completed ExecutionSteps.
        """
        return [step for step in self.steps if step.status == PlanStatus.COMPLETED]

    def get_failed_steps(self) -> List[ExecutionStep]:
        """Get all failed steps in the plan.

        Returns:
            List of failed ExecutionSteps.
        """
        return [step for step in self.steps if step.status == PlanStatus.FAILED]

    def is_complete(self) -> bool:
        """Check if the plan is complete.

        Returns:
            True if all steps are completed or skipped, False otherwise.
        """
        return all(
            step.status in (PlanStatus.COMPLETED, PlanStatus.SKIPPED)
            for step in self.steps
        )

    def is_failed(self) -> bool:
        """Check if the plan has failed.

        Returns:
            True if any step has failed, False otherwise.
        """
        return any(step.status == PlanStatus.FAILED for step in self.steps)
