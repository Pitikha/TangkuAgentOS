"""
AI Foundation Framework - Planning Manager

This module provides the PlanningManager class for managing AI planning operations.
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from typing import Any, Dict, List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from tangku_agentos.ai_foundation.models.request import AIRequest
    from tangku_agentos.ai_foundation.models.response import AIResponse
    from tangku_agentos.ai_foundation.core.config import AIConfig
    from tangku_agentos.ai_foundation.core.foundation import AIFoundation

logger = logging.getLogger(__name__)


class PlanningStrategy(Enum):
    """Strategies for AI planning."""
    HIERARCHICAL = auto()
    PARALLEL = auto()
    ADAPTIVE = auto()
    REACTIVE = auto()
    OPPORTUNISTIC = auto()
    CUSTOM = auto()


class PlanStatus(Enum):
    """Status of a plan."""
    CREATED = auto()
    PLANNING = auto()
    READY = auto()
    EXECUTING = auto()
    COMPLETED = auto()
    FAILED = auto()
    CANCELLED = auto()


@dataclass
class PlanStep:
    """
    Represents a single step in a plan.
    
    Attributes:
        step_id: Unique identifier for the step.
        description: Description of the step.
        action: Action to perform.
        parameters: Parameters for the action.
        dependencies: List of step IDs this step depends on.
        status: Current status of the step.
        result: Result of the step execution.
        timestamp: When the step was created.
        metadata: Additional metadata.
    """

    step_id: str
    description: str
    action: str
    parameters: Dict[str, Any] = field(default_factory=dict)
    dependencies: List[str] = field(default_factory=list)
    status: PlanStatus = PlanStatus.CREATED
    result: Any = None
    timestamp: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "step_id": self.step_id,
            "description": self.description,
            "action": self.action,
            "parameters": self.parameters,
            "dependencies": self.dependencies,
            "status": self.status.value,
            "result": self.result,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata,
        }


@dataclass
class Plan:
    """
    Represents an AI plan.
    
    Attributes:
        plan_id: Unique identifier for the plan.
        goal: The goal the plan aims to achieve.
        steps: List of steps in the plan.
        status: Current status of the plan.
        created_at: When the plan was created.
        updated_at: When the plan was last updated.
        completed_at: When the plan was completed.
        metrics: Metrics for the plan.
        metadata: Additional metadata.
    """

    plan_id: str
    goal: str
    steps: List[PlanStep] = field(default_factory=list)
    status: PlanStatus = PlanStatus.CREATED
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    metrics: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def step_count(self) -> int:
        """Get the number of steps in the plan."""
        return len(self.steps)

    @property
    def completed_steps(self) -> int:
        """Get the number of completed steps."""
        return sum(1 for step in self.steps if step.status == PlanStatus.COMPLETED)

    @property
    def is_complete(self) -> bool:
        """Check if the plan is complete."""
        return self.status == PlanStatus.COMPLETED

    @property
    def is_failed(self) -> bool:
        """Check if the plan has failed."""
        return self.status == PlanStatus.FAILED

    def add_step(self, step: PlanStep) -> None:
        """Add a step to the plan."""
        self.steps.append(step)
        self.updated_at = datetime.utcnow()

    def get_step(self, step_id: str) -> Optional[PlanStep]:
        """Get a step by ID."""
        for step in self.steps:
            if step.step_id == step_id:
                return step
        return None

    def update_step_status(self, step_id: str, status: PlanStatus, result: Any = None) -> bool:
        """Update the status of a step."""
        step = self.get_step(step_id)
        if step:
            step.status = status
            step.result = result
            self.updated_at = datetime.utcnow()
            return True
        return False

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "plan_id": self.plan_id,
            "goal": self.goal,
            "steps": [step.to_dict() for step in self.steps],
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "step_count": self.step_count,
            "completed_steps": self.completed_steps,
            "metrics": self.metrics,
            "metadata": self.metadata,
        }


@dataclass
class PlanningManagerMetrics:
    """Metrics for the planning manager."""
    plans_created: int = 0
    plans_completed: int = 0
    plans_failed: int = 0
    steps_created: int = 0
    steps_completed: int = 0
    errors: int = 0
    last_error: Optional[str] = None
    last_error_time: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "plans_created": self.plans_created,
            "plans_completed": self.plans_completed,
            "plans_failed": self.plans_failed,
            "steps_created": self.steps_created,
            "steps_completed": self.steps_completed,
            "errors": self.errors,
            "last_error": self.last_error,
            "last_error_time": self.last_error_time.isoformat() if self.last_error_time else None,
        }


class PlanningManager:
    """
    Manager for AI planning operations.
    
    This class provides advanced planning capabilities for AI operations,
    supporting multiple planning strategies and adaptive planning.
    
    Thread Safety:
        This class is thread-safe for concurrent access.
    
    Example:
        >>> from tangku_agentos.ai_foundation import PlanningManager
        >>> 
        >>> # Create manager
        >>> manager = PlanningManager()
        >>> 
        >>> # Create a plan
        >>> plan = await manager.create_plan("Solve complex problem")
        >>> 
        >>> # Execute the plan
        >>> result = await manager.execute_plan(plan.plan_id)
        >>> 
        >>> # Get plan status
        >>> status = await manager.get_plan_status(plan.plan_id)
    """

    def __init__(self, config: "AIConfig", foundation: "AIFoundation"):
        """
        Initialize the planning manager.
        
        Args:
            config: AI Foundation configuration.
            foundation: AI Foundation instance.
        """
        self._config = config
        self._foundation = foundation
        self._plans: Dict[str, Plan] = {}
        self._metrics = PlanningManagerMetrics()
        self._lock = asyncio.Lock()
        self._initialized = False
        self._started = False
        
        logger.info("PlanningManager initialized")

    @property
    def config(self) -> "AIConfig":
        """Get the configuration."""
        return self._config

    @property
    def foundation(self) -> "AIFoundation":
        """Get the AI Foundation instance."""
        return self._foundation

    @property
    def metrics(self) -> PlanningManagerMetrics:
        """Get the planning manager metrics."""
        return self._metrics

    @property
    def is_initialized(self) -> bool:
        """Check if the manager is initialized."""
        return self._initialized

    @property
    def is_started(self) -> bool:
        """Check if the manager is started."""
        return self._started

    async def initialize(self) -> None:
        """
        Initialize the planning manager.
        """
        if self._initialized:
            logger.warning("PlanningManager already initialized")
            return
        
        logger.info("Initializing PlanningManager...")
        
        self._initialized = True
        logger.info("PlanningManager initialized successfully")

    async def start(self) -> None:
        """
        Start the planning manager.
        """
        if self._started:
            logger.warning("PlanningManager already started")
            return
        
        if not self._initialized:
            await self.initialize()
        
        logger.info("Starting PlanningManager...")
        
        self._started = True
        logger.info("PlanningManager started successfully")

    async def stop(self) -> None:
        """
        Stop the planning manager.
        """
        if not self._started:
            logger.warning("PlanningManager not started")
            return
        
        logger.info("Stopping PlanningManager...")
        
        self._started = False
        logger.info("PlanningManager stopped successfully")

    async def create_plan(
        self,
        goal: str,
        strategy: PlanningStrategy = PlanningStrategy.HIERARCHICAL,
        context: Optional[Dict[str, Any]] = None,
        constraints: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Plan:
        """
        Create a new plan.
        
        Args:
            goal: The goal the plan aims to achieve.
            strategy: Planning strategy to use.
            context: Optional context for planning.
            constraints: Optional constraints for the plan.
            metadata: Optional additional metadata.
        
        Returns:
            Plan instance.
        """
        import hashlib
        import time
        
        async with self._lock:
            # Generate plan ID
            unique_str = f"{goal}:{time.time()}"
            plan_id = f"plan_{hashlib.sha256(unique_str.encode()).hexdigest()[:16]}"
            
            # Create plan
            plan = Plan(
                plan_id=plan_id,
                goal=goal,
                metadata=metadata or {},
            )
            
            # Store plan
            self._plans[plan_id] = plan
            
            # Update metrics
            self._metrics.plans_created += 1
            
            # Generate initial steps based on strategy
            await self._generate_initial_steps(plan, strategy, context, constraints)
            
            logger.debug(f"Plan created: {plan_id}")
            return plan

    async def _generate_initial_steps(
        self,
        plan: Plan,
        strategy: PlanningStrategy,
        context: Optional[Dict[str, Any]],
        constraints: Optional[List[str]],
    ) -> None:
        """Generate initial steps for a plan."""
        if strategy == PlanningStrategy.HIERARCHICAL:
            await self._generate_hierarchical_steps(plan, context, constraints)
        elif strategy == PlanningStrategy.PARALLEL:
            await self._generate_parallel_steps(plan, context, constraints)
        elif strategy == PlanningStrategy.ADAPTIVE:
            await self._generate_adaptive_steps(plan, context, constraints)
        elif strategy == PlanningStrategy.REACTIVE:
            await self._generate_reactive_steps(plan, context, constraints)
        elif strategy == PlanningStrategy.OPPORTUNISTIC:
            await self._generate_opportunistic_steps(plan, context, constraints)
        else:
            await self._generate_hierarchical_steps(plan, context, constraints)

    async def _generate_hierarchical_steps(
        self,
        plan: Plan,
        context: Optional[Dict[str, Any]],
        constraints: Optional[List[str]],
    ) -> None:
        """Generate hierarchical plan steps."""
        # Step 1: Define high-level objectives
        step1 = PlanStep(
            step_id=f"{plan.plan_id}_1",
            description="Define high-level objectives",
            action="define_objectives",
            parameters={"goal": plan.goal},
        )
        plan.add_step(step1)
        self._metrics.steps_created += 1
        
        # Step 2: Break down into tasks
        step2 = PlanStep(
            step_id=f"{plan.plan_id}_2",
            description="Break down objectives into tasks",
            action="breakdown_tasks",
            dependencies=[step1.step_id],
        )
        plan.add_step(step2)
        self._metrics.steps_created += 1
        
        # Step 3: Identify dependencies
        step3 = PlanStep(
            step_id=f"{plan.plan_id}_3",
            description="Identify task dependencies",
            action="identify_dependencies",
            dependencies=[step2.step_id],
        )
        plan.add_step(step3)
        self._metrics.steps_created += 1
        
        # Step 4: Sequence tasks
        step4 = PlanStep(
            step_id=f"{plan.plan_id}_4",
            description="Sequence tasks based on dependencies",
            action="sequence_tasks",
            dependencies=[step3.step_id],
        )
        plan.add_step(step4)
        self._metrics.steps_created += 1

    async def _generate_parallel_steps(
        self,
        plan: Plan,
        context: Optional[Dict[str, Any]],
        constraints: Optional[List[str]],
    ) -> None:
        """Generate parallel plan steps."""
        # Step 1: Identify parallelizable tasks
        step1 = PlanStep(
            step_id=f"{plan.plan_id}_1",
            description="Identify tasks that can be executed in parallel",
            action="identify_parallel_tasks",
            parameters={"goal": plan.goal},
        )
        plan.add_step(step1)
        self._metrics.steps_created += 1
        
        # Step 2: Group parallel tasks
        step2 = PlanStep(
            step_id=f"{plan.plan_id}_2",
            description="Group tasks for parallel execution",
            action="group_parallel_tasks",
            dependencies=[step1.step_id],
        )
        plan.add_step(step2)
        self._metrics.steps_created += 1
        
        # Step 3: Execute parallel groups
        step3 = PlanStep(
            step_id=f"{plan.plan_id}_3",
            description="Execute parallel task groups",
            action="execute_parallel",
            dependencies=[step2.step_id],
        )
        plan.add_step(step3)
        self._metrics.steps_created += 1
        
        # Step 4: Combine results
        step4 = PlanStep(
            step_id=f"{plan.plan_id}_4",
            description="Combine results from parallel execution",
            action="combine_results",
            dependencies=[step3.step_id],
        )
        plan.add_step(step4)
        self._metrics.steps_created += 1

    async def _generate_adaptive_steps(
        self,
        plan: Plan,
        context: Optional[Dict[str, Any]],
        constraints: Optional[List[str]],
    ) -> None:
        """Generate adaptive plan steps."""
        # Step 1: Assess current state
        step1 = PlanStep(
            step_id=f"{plan.plan_id}_1",
            description="Assess current state and context",
            action="assess_state",
            parameters={"goal": plan.goal, "context": context or {}},
        )
        plan.add_step(step1)
        self._metrics.steps_created += 1
        
        # Step 2: Generate initial plan
        step2 = PlanStep(
            step_id=f"{plan.plan_id}_2",
            description="Generate initial plan based on assessment",
            action="generate_initial_plan",
            dependencies=[step1.step_id],
        )
        plan.add_step(step2)
        self._metrics.steps_created += 1
        
        # Step 3: Monitor progress
        step3 = PlanStep(
            step_id=f"{plan.plan_id}_3",
            description="Monitor progress and adapt as needed",
            action="monitor_progress",
            dependencies=[step2.step_id],
        )
        plan.add_step(step3)
        self._metrics.steps_created += 1
        
        # Step 4: Adapt plan
        step4 = PlanStep(
            step_id=f"{plan.plan_id}_4",
            description="Adapt plan based on progress and changes",
            action="adapt_plan",
            dependencies=[step3.step_id],
        )
        plan.add_step(step4)
        self._metrics.steps_created += 1

    async def _generate_reactive_steps(
        self,
        plan: Plan,
        context: Optional[Dict[str, Any]],
        constraints: Optional[List[str]],
    ) -> None:
        """Generate reactive plan steps."""
        # Step 1: Identify triggers
        step1 = PlanStep(
            step_id=f"{plan.plan_id}_1",
            description="Identify triggers and conditions",
            action="identify_triggers",
            parameters={"goal": plan.goal},
        )
        plan.add_step(step1)
        self._metrics.steps_created += 1
        
        # Step 2: Define reactions
        step2 = PlanStep(
            step_id=f"{plan.plan_id}_2",
            description="Define reactions for each trigger",
            action="define_reactions",
            dependencies=[step1.step_id],
        )
        plan.add_step(step2)
        self._metrics.steps_created += 1
        
        # Step 3: Implement monitoring
        step3 = PlanStep(
            step_id=f"{plan.plan_id}_3",
            description="Implement trigger monitoring",
            action="implement_monitoring",
            dependencies=[step2.step_id],
        )
        plan.add_step(step3)
        self._metrics.steps_created += 1
        
        # Step 4: Execute reactions
        step4 = PlanStep(
            step_id=f"{plan.plan_id}_4",
            description="Execute reactions when triggers fire",
            action="execute_reactions",
            dependencies=[step3.step_id],
        )
        plan.add_step(step4)
        self._metrics.steps_created += 1

    async def _generate_opportunistic_steps(
        self,
        plan: Plan,
        context: Optional[Dict[str, Any]],
        constraints: Optional[List[str]],
    ) -> None:
        """Generate opportunistic plan steps."""
        # Step 1: Identify opportunities
        step1 = PlanStep(
            step_id=f"{plan.plan_id}_1",
            description="Identify opportunities and resources",
            action="identify_opportunities",
            parameters={"goal": plan.goal, "context": context or {}},
        )
        plan.add_step(step1)
        self._metrics.steps_created += 1
        
        # Step 2: Prioritize opportunities
        step2 = PlanStep(
            step_id=f"{plan.plan_id}_2",
            description="Prioritize opportunities based on value",
            action="prioritize_opportunities",
            dependencies=[step1.step_id],
        )
        plan.add_step(step2)
        self._metrics.steps_created += 1
        
        # Step 3: Exploit opportunities
        step3 = PlanStep(
            step_id=f"{plan.plan_id}_3",
            description="Exploit highest priority opportunities",
            action="exploit_opportunities",
            dependencies=[step2.step_id],
        )
        plan.add_step(step3)
        self._metrics.steps_created += 1
        
        # Step 4: Reassess
        step4 = PlanStep(
            step_id=f"{plan.plan_id}_4",
            description="Reassess and identify new opportunities",
            action="reassess",
            dependencies=[step3.step_id],
        )
        plan.add_step(step4)
        self._metrics.steps_created += 1

    async def get_plan(self, plan_id: str) -> Optional[Plan]:
        """
        Get a plan by ID.
        
        Args:
            plan_id: ID of the plan to get.
        
        Returns:
            Plan or None if not found.
        """
        return self._plans.get(plan_id)

    async def list_plans(
        self,
        status: Optional[PlanStatus] = None,
        limit: Optional[int] = None,
    ) -> List[Plan]:
        """
        List all plans, optionally filtered.
        
        Args:
            status: Optional plan status to filter by.
            limit: Optional maximum number of plans to return.
        
        Returns:
            List of Plan instances.
        """
        plans = []
        
        for plan in self._plans.values():
            if status and plan.status != status:
                continue
            plans.append(plan)
            if limit and len(plans) >= limit:
                break
        
        return plans

    async def update_plan(
        self,
        plan_id: str,
        **kwargs,
    ) -> bool:
        """
        Update a plan.
        
        Args:
            plan_id: ID of the plan to update.
            **kwargs: Plan attributes to update.
        
        Returns:
            True if plan was updated, False if not found.
        """
        plan = self._plans.get(plan_id)
        if not plan:
            return False
        
        for key, value in kwargs.items():
            if hasattr(plan, key):
                setattr(plan, key, value)
        
        plan.updated_at = datetime.utcnow()
        return True

    async def add_step(
        self,
        plan_id: str,
        step: PlanStep,
    ) -> bool:
        """
        Add a step to a plan.
        
        Args:
            plan_id: ID of the plan.
            step: PlanStep to add.
        
        Returns:
            True if step was added, False if plan not found.
        """
        plan = self._plans.get(plan_id)
        if not plan:
            return False
        
        plan.add_step(step)
        self._metrics.steps_created += 1
        return True

    async def update_step(
        self,
        plan_id: str,
        step_id: str,
        **kwargs,
    ) -> bool:
        """
        Update a step in a plan.
        
        Args:
            plan_id: ID of the plan.
            step_id: ID of the step to update.
            **kwargs: Step attributes to update.
        
        Returns:
            True if step was updated, False if not found.
        """
        plan = self._plans.get(plan_id)
        if not plan:
            return False
        
        step = plan.get_step(step_id)
        if not step:
            return False
        
        for key, value in kwargs.items():
            if hasattr(step, key):
                setattr(step, key, value)
        
        plan.updated_at = datetime.utcnow()
        return True

    async def execute_plan(
        self,
        plan_id: str,
        timeout: Optional[float] = None,
    ) -> Optional[Plan]:
        """
        Execute a plan.
        
        Args:
            plan_id: ID of the plan to execute.
            timeout: Optional timeout for the execution.
        
        Returns:
            Plan with updated status and results, or None if not found.
        """
        plan = self._plans.get(plan_id)
        if not plan:
            return None
        
        plan.status = PlanStatus.EXECUTING
        plan.updated_at = datetime.utcnow()
        
        try:
            # Execute each step in order
            for step in plan.steps:
                # Check dependencies
                dependencies_met = all(
                    plan.get_step(dep).status == PlanStatus.COMPLETED
                    for dep in step.dependencies
                )
                
                if not dependencies_met:
                    continue
                
                # Execute the step
                await self._execute_step(plan, step, timeout)
            
            # Mark plan as completed
            plan.status = PlanStatus.COMPLETED
            plan.completed_at = datetime.utcnow()
            self._metrics.plans_completed += 1
            
        except Exception as e:
            plan.status = PlanStatus.FAILED
            plan.updated_at = datetime.utcnow()
            self._metrics.plans_failed += 1
            logger.error(f"Plan execution failed: {e}")
            raise
        
        return plan

    async def _execute_step(
        self,
        plan: Plan,
        step: PlanStep,
        timeout: Optional[float],
    ) -> None:
        """Execute a single plan step."""
        try:
            # In a real implementation, this would execute the step action
            # For now, simulate execution
            
            # Update step status
            plan.update_step_status(step.step_id, PlanStatus.COMPLETED)
            step.result = f"Step {step.step_id} executed successfully"
            
            self._metrics.steps_completed += 1
            
        except Exception as e:
            plan.update_step_status(step.step_id, PlanStatus.FAILED, str(e))
            raise

    async def cancel_plan(self, plan_id: str) -> bool:
        """
        Cancel a plan.
        
        Args:
            plan_id: ID of the plan to cancel.
        
        Returns:
            True if plan was cancelled, False if not found.
        """
        plan = self._plans.get(plan_id)
        if not plan:
            return False
        
        if plan.is_complete or plan.is_failed:
            return False
        
        plan.status = PlanStatus.CANCELLED
        plan.updated_at = datetime.utcnow()
        return True

    async def delete_plan(self, plan_id: str) -> bool:
        """
        Delete a plan.
        
        Args:
            plan_id: ID of the plan to delete.
        
        Returns:
            True if plan was deleted, False if not found.
        """
        if plan_id not in self._plans:
            return False
        
        del self._plans[plan_id]
        return True

    async def get_plan_status(self, plan_id: str) -> Optional[Dict[str, Any]]:
        """
        Get the status of a plan.
        
        Args:
            plan_id: ID of the plan.
        
        Returns:
            Dictionary with plan status information, or None if not found.
        """
        plan = self._plans.get(plan_id)
        if not plan:
            return None
        
        return {
            "plan_id": plan.plan_id,
            "goal": plan.goal,
            "status": plan.status.value,
            "step_count": plan.step_count,
            "completed_steps": plan.completed_steps,
            "progress": plan.completed_steps / plan.step_count if plan.step_count > 0 else 0,
            "created_at": plan.created_at.isoformat(),
            "updated_at": plan.updated_at.isoformat(),
            "completed_at": plan.completed_at.isoformat() if plan.completed_at else None,
        }

    async def get_info(self) -> Dict[str, Any]:
        """
        Get information about the planning manager.
        
        Returns:
            Dictionary with planning manager information.
        """
        return {
            "status": "active" if self._initialized and self._started else "inactive",
            "plans": len(self._plans),
            "metrics": self._metrics.to_dict(),
            "config": {
                "use_hierarchical_planning": self._config.planning.use_hierarchical_planning,
                "use_parallel_planning": self._config.planning.use_parallel_planning,
                "use_adaptive_planning": self._config.planning.use_adaptive_planning,
                "max_plan_depth": self._config.planning.max_plan_depth,
                "max_plan_branches": self._config.planning.max_plan_branches,
                "max_plan_length": self._config.planning.max_plan_length,
            }
        }

    async def reset(self) -> None:
        """
        Reset the planning manager.
        
        This method clears all plans and resets all state.
        """
        logger.info("Resetting PlanningManager...")
        
        self._plans.clear()
        self._metrics = PlanningManagerMetrics()
        self._initialized = False
        self._started = False
        
        logger.info("PlanningManager reset successfully")

    def __repr__(self) -> str:
        """Return string representation."""
        return (
            f"PlanningManager("
            f"initialized={self._initialized}, "
            f"started={self._started}, "
            f"plans={len(self._plans)})"
        )
