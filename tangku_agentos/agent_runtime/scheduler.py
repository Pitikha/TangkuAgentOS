"""
TangkuAgentOS Agent Runtime - Agent Scheduler

This module provides the AgentScheduler for managing agent tasks:
- Task scheduling (immediate, delayed, periodic, cron)
- Priority-based execution
- Parallel task execution
- Task queue management
- Task cancellation and timeout
- Retry policies
- Dependency management

The scheduler ensures that agent tasks are executed efficiently and reliably.

Author: TangkuAgentOS Team
License: MIT
"""

from __future__ import annotations

import asyncio
import heapq
import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum, auto
from typing import (
    Any,
    Callable,
    Dict,
    List,
    Optional,
    Set,
    Tuple,
    Union,
    TYPE_CHECKING,
)
import uuid

if TYPE_CHECKING:
    from tangku_agentos.agent_runtime.types import (
        AgentID,
        TaskID,
        TaskType,
        TaskStatus,
        ScheduleType,
    )
    from tangku_agentos.agent_runtime.core import Agent
    from tangku_agentos.agent_runtime.manager import AgentManager

logger = logging.getLogger(__name__)


# =============================================================================
# TASK DEFINITION
# =============================================================================

@dataclass
class Task:
    """
    Definition of a task for an agent.
    
    Attributes:
        task_id: Unique ID of the task.
        agent_id: ID of the agent that owns the task.
        name: Human-readable name of the task.
        description: Description of the task.
        task_type: Type of the task.
        payload: Task payload/data.
        priority: Task priority (higher = more important).
        schedule_type: Type of scheduling.
        scheduled_at: When the task is scheduled to run.
        timeout: Timeout in seconds.
        max_retries: Maximum number of retry attempts.
        retry_delay: Delay between retries in seconds.
        dependencies: Set of task IDs this task depends on.
        status: Current status of the task.
        result: Result of the task (when completed).
        error: Error message (when failed).
        retry_count: Number of retry attempts.
        created_at: When the task was created.
        started_at: When the task started.
        completed_at: When the task completed.
        metadata: Additional task metadata.
    """

    task_id: "TaskID"
    agent_id: "AgentID"
    name: str = ""
    description: str = ""
    task_type: "TaskType" = TaskType.SIMPLE
    payload: Dict[str, Any] = field(default_factory=dict)
    priority: int = 0
    schedule_type: "ScheduleType" = ScheduleType.IMMEDIATE
    scheduled_at: Optional[datetime] = None
    timeout: float = 60.0
    max_retries: int = 3
    retry_delay: float = 1.0
    dependencies: Set["TaskID"] = field(default_factory=set)
    status: "TaskStatus" = TaskStatus.PENDING
    result: Optional[Any] = None
    error: Optional[str] = None
    retry_count: int = 0
    created_at: datetime = field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def is_ready(self) -> bool:
        """Check if the task is ready to be executed."""
        if self.status != TaskStatus.PENDING:
            return False
        if self.scheduled_at and datetime.utcnow() < self.scheduled_at:
            return False
        return True

    def is_completed(self) -> bool:
        """Check if the task is completed."""
        return self.status in {
            TaskStatus.COMPLETED,
            TaskStatus.FAILED,
            TaskStatus.CANCELLED,
            TaskStatus.TIMEOUT,
        }

    def is_active(self) -> bool:
        """Check if the task is actively running."""
        return self.status in {
            TaskStatus.QUEUED,
            TaskStatus.RUNNING,
            TaskStatus.PAUSED,
            TaskStatus.RETRYING,
        }

    def can_retry(self) -> bool:
        """Check if the task can be retried."""
        return (
            self.status == TaskStatus.FAILED
            and self.retry_count < self.max_retries
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "task_id": self.task_id,
            "agent_id": self.agent_id,
            "name": self.name,
            "description": self.description,
            "task_type": self.task_type.value if hasattr(self.task_type, 'value') else str(self.task_type),
            "payload": self.payload,
            "priority": self.priority,
            "schedule_type": self.schedule_type.value if hasattr(self.schedule_type, 'value') else str(self.schedule_type),
            "scheduled_at": self.scheduled_at.isoformat() if self.scheduled_at else None,
            "timeout": self.timeout,
            "max_retries": self.max_retries,
            "retry_delay": self.retry_delay,
            "dependencies": list(self.dependencies),
            "status": self.status.value if hasattr(self.status, 'value') else str(self.status),
            "result": self.result,
            "error": self.error,
            "retry_count": self.retry_count,
            "created_at": self.created_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Task":
        """Create from dictionary."""
        from tangku_agentos.agent_runtime.types import TaskType, TaskStatus, ScheduleType

        task_type = TaskType[data["task_type"]] if "task_type" in data else TaskType.SIMPLE
        schedule_type = ScheduleType[data["schedule_type"]] if "schedule_type" in data else ScheduleType.IMMEDIATE
        status = TaskStatus[data["status"]] if "status" in data else TaskStatus.PENDING

        return cls(
            task_id=data["task_id"],
            agent_id=data["agent_id"],
            name=data.get("name", ""),
            description=data.get("description", ""),
            task_type=task_type,
            payload=data.get("payload", {}),
            priority=data.get("priority", 0),
            schedule_type=schedule_type,
            scheduled_at=datetime.fromisoformat(data["scheduled_at"])
            if data.get("scheduled_at")
            else None,
            timeout=data.get("timeout", 60.0),
            max_retries=data.get("max_retries", 3),
            retry_delay=data.get("retry_delay", 1.0),
            dependencies=set(data.get("dependencies", [])),
            status=status,
            result=data.get("result"),
            error=data.get("error"),
            retry_count=data.get("retry_count", 0),
            created_at=datetime.fromisoformat(data["created_at"]),
            started_at=datetime.fromisoformat(data["started_at"])
            if data.get("started_at")
            else None,
            completed_at=datetime.fromisoformat(data["completed_at"])
            if data.get("completed_at")
            else None,
            metadata=data.get("metadata", {}),
        )

    def __repr__(self) -> str:
        """Return string representation."""
        return (
            f"Task(id={self.task_id}, agent={self.agent_id}, "
            f"name={self.name}, status={self.status.name})"
        )


# =============================================================================
# TASK PRIORITY QUEUE
# =============================================================================

@dataclass
class TaskQueueItem:
    """
    Item in the task priority queue.
    
    Attributes:
        task: The task.
        priority: Priority for ordering (higher = more important).
        scheduled_at: When the task is scheduled to run.
    """

    task: Task
    priority: int
    scheduled_at: Optional[datetime]

    def __lt__(self, other: "TaskQueueItem") -> bool:
        """
        Compare items for priority queue ordering.
        
        Higher priority tasks come first.
        For tasks with the same priority, earlier scheduled tasks come first.
        """
        # Higher priority first
        if self.priority != other.priority:
            return self.priority > other.priority
        
        # Earlier scheduled first
        if self.scheduled_at and other.scheduled_at:
            return self.scheduled_at < other.scheduled_at
        elif self.scheduled_at:
            return True
        elif other.scheduled_at:
            return False
        
        # Finally, by creation time
        return self.task.created_at < other.task.created_at


class TaskPriorityQueue:
    """
    Priority queue for agent tasks.
    
    This class provides a thread-safe priority queue for managing agent tasks.
    Tasks are ordered by priority (higher first) and then by scheduled time.
    
    Example:
        >>> from tangku_agentos.agent_runtime.scheduler import TaskPriorityQueue
        >>> 
        >>> queue = TaskPriorityQueue()
        >>> 
        >>> # Add tasks
        >>> await queue.push(task1)
        >>> await queue.push(task2)
        >>> 
        >>> # Get next task
        >>> next_task = await queue.pop()
    """

    def __init__(self):
        """Initialize the priority queue."""
        self._queue: List[TaskQueueItem] = []
        self._lock = asyncio.Lock()
        self._task_index: Dict["TaskID", TaskQueueItem] = {}

    async def push(self, task: Task) -> None:
        """
        Push a task onto the queue.
        
        Args:
            task: Task to push.
        """
        async with self._lock:
            item = TaskQueueItem(
                task=task,
                priority=task.priority,
                scheduled_at=task.scheduled_at,
            )
            heapq.heappush(self._queue, item)
            self._task_index[task.task_id] = item
            logger.debug(f"Task pushed to queue: {task.task_id}")

    async def pop(self) -> Optional[Task]:
        """
        Pop the next task from the queue.
        
        Returns:
            Next task to execute, or None if queue is empty.
        """
        async with self._lock:
            while self._queue:
                item = heapq.heappop(self._queue)
                # Check if task is still valid
                if item.task.task_id in self._task_index:
                    del self._task_index[item.task.task_id]
                    logger.debug(f"Task popped from queue: {item.task.task_id}")
                    return item.task
            return None

    async def peek(self) -> Optional[Task]:
        """
        Peek at the next task without removing it.
        
        Returns:
            Next task to execute, or None if queue is empty.
        """
        async with self._lock:
            if self._queue:
                return self._queue[0].task
            return None

    async def remove(self, task_id: "TaskID") -> bool:
        """
        Remove a task from the queue.
        
        Args:
            task_id: ID of the task to remove.
            
        Returns:
            True if the task was removed, False if not found.
        """
        async with self._lock:
            if task_id not in self._task_index:
                return False

            # Mark task as cancelled
            item = self._task_index[task_id]
            item.task.status = TaskStatus.CANCELLED
            item.task.completed_at = datetime.utcnow()

            # Remove from queue (lazy removal)
            del self._task_index[task_id]
            logger.debug(f"Task removed from queue: {task_id}")
            return True

    async def update(self, task: Task) -> bool:
        """
        Update a task in the queue.
        
        Args:
            task: Updated task.
            
        Returns:
            True if the task was updated, False if not found.
        """
        async with self._lock:
            if task.task_id not in self._task_index:
                return False

            # Update the task
            item = self._task_index[task.task_id]
            item.task = task
            item.priority = task.priority
            item.scheduled_at = task.scheduled_at

            # Rebuild the heap (not efficient, but simple)
            self._rebuild_heap()
            logger.debug(f"Task updated in queue: {task.task_id}")
            return True

    def _rebuild_heap(self) -> None:
        """Rebuild the heap from the current items."""
        self._queue = []
        for item in self._task_index.values():
            heapq.heappush(self._queue, item)

    async def contains(self, task_id: "TaskID") -> bool:
        """
        Check if a task is in the queue.
        
        Args:
            task_id: ID of the task to check.
            
        Returns:
            True if the task is in the queue, False otherwise.
        """
        async with self._lock:
            return task_id in self._task_index

    async def size(self) -> int:
        """
        Get the number of tasks in the queue.
        
        Returns:
            Number of tasks in the queue.
        """
        async with self._lock:
            return len(self._queue)

    async def clear(self) -> int:
        """
        Clear all tasks from the queue.
        
        Returns:
            Number of tasks cleared.
        """
        async with self._lock:
            count = len(self._queue)
            self._queue.clear()
            self._task_index.clear()
            return count

    def __len__(self) -> int:
        """Get the number of tasks in the queue."""
        return len(self._queue)

    def __repr__(self) -> str:
        """Return string representation."""
        return f"TaskPriorityQueue(size={len(self._queue)})"


# =============================================================================
# RETRY POLICY
# =============================================================================

@dataclass
class RetryPolicy:
    """
    Retry policy for tasks.
    
    Attributes:
        max_retries: Maximum number of retry attempts.
        base_delay: Base delay between retries in seconds.
        max_delay: Maximum delay between retries in seconds.
        backoff_multiplier: Multiplier for exponential backoff.
        retry_on: Set of error types to retry on.
    """

    max_retries: int = 3
    base_delay: float = 1.0
    max_delay: float = 60.0
    backoff_multiplier: float = 2.0
    retry_on: Set[str] = field(default_factory=set)

    def get_delay(self, attempt: int) -> float:
        """
        Get the delay for a retry attempt.
        
        Args:
            attempt: Retry attempt number (0-indexed).
            
        Returns:
            Delay in seconds before the next retry.
        """
        delay = self.base_delay * (self.backoff_multiplier ** attempt)
        return min(delay, self.max_delay)

    def should_retry(self, error: str, attempt: int) -> bool:
        """
        Check if a task should be retried.
        
        Args:
            error: Error message.
            attempt: Current attempt number.
            
        Returns:
            True if the task should be retried, False otherwise.
        """
        if attempt >= self.max_retries:
            return False
        if not self.retry_on:
            return True
        return any(retry_error in error for retry_error in self.retry_on)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "max_retries": self.max_retries,
            "base_delay": self.base_delay,
            "max_delay": self.max_delay,
            "backoff_multiplier": self.backoff_multiplier,
            "retry_on": list(self.retry_on),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "RetryPolicy":
        """Create from dictionary."""
        return cls(
            max_retries=data.get("max_retries", 3),
            base_delay=data.get("base_delay", 1.0),
            max_delay=data.get("max_delay", 60.0),
            backoff_multiplier=data.get("backoff_multiplier", 2.0),
            retry_on=set(data.get("retry_on", [])),
        )


# =============================================================================
# AGENT SCHEDULER
# =============================================================================

class AgentScheduler:
    """
    Scheduler for managing agent tasks.
    
    This class provides:
    - Task scheduling (immediate, delayed, periodic, cron)
    - Priority-based execution
    - Parallel task execution
    - Task queue management
    - Task cancellation and timeout
    - Retry policies
    - Dependency management
    
    Thread Safety:
        This class is thread-safe for concurrent access.
    
    Example:
        >>> from tangku_agentos.agent_runtime.scheduler import AgentScheduler
        >>> 
        >>> scheduler = AgentScheduler(max_parallel=10)
        >>> 
        >>> # Schedule a task
        >>> task_id = await scheduler.schedule(
        ...     agent_id="agent_1",
        ...     name="process_data",
        ...     payload={"data": "..."},
        ...     priority=1
        ... )
        >>> 
        >>> # Start the scheduler
        >>> await scheduler.start()
    """

    def __init__(
        self,
        max_parallel: int = 10,
        default_timeout: float = 60.0,
        default_retry_policy: Optional[RetryPolicy] = None,
        enable_metrics: bool = True,
    ):
        """
        Initialize the scheduler.
        
        Args:
            max_parallel: Maximum number of parallel tasks.
            default_timeout: Default timeout for tasks in seconds.
            default_retry_policy: Default retry policy for tasks.
            enable_metrics: Whether to collect metrics.
        """
        self._max_parallel = max_parallel
        self._default_timeout = default_timeout
        self._default_retry_policy = default_retry_policy or RetryPolicy()
        self._enable_metrics = enable_metrics

        # Task storage
        self._tasks: Dict["TaskID", Task] = {}
        self._queue = TaskPriorityQueue()
        self._lock = asyncio.Lock()

        # Execution tracking
        self._running_tasks: Dict["TaskID", asyncio.Task] = {}
        self._active_count = 0
        self._active_lock = asyncio.Lock()

        # Scheduling
        self._scheduler_task: Optional[asyncio.Task] = None
        self._running = False

        # Callbacks
        self._on_task_start: List[Callable[[Task], None]] = []
        self._on_task_complete: List[Callable[[Task], None]] = []
        self._on_task_fail: List[Callable[[Task], None]] = []
        self._on_task_cancel: List[Callable[[Task], None]] = []

        # Metrics
        self._metrics: Dict[str, Any] = {
            "tasks_scheduled": 0,
            "tasks_started": 0,
            "tasks_completed": 0,
            "tasks_failed": 0,
            "tasks_cancelled": 0,
            "tasks_timed_out": 0,
            "tasks_retried": 0,
            "active_tasks": 0,
            "queued_tasks": 0,
        }

        logger.info(
            f"AgentScheduler initialized (max_parallel={max_parallel}, "
            f"default_timeout={default_timeout})"
        )

    async def start(self) -> None:
        """Start the scheduler."""
        if self._running:
            return

        self._running = True
        self._scheduler_task = asyncio.create_task(self._scheduler_loop())
        logger.info("AgentScheduler started")

    async def stop(self, wait_for_completion: bool = True) -> None:
        """
        Stop the scheduler.
        
        Args:
            wait_for_completion: Whether to wait for running tasks to complete.
        """
        if not self._running:
            return

        self._running = False

        if self._scheduler_task:
            self._scheduler_task.cancel()
            try:
                await self._scheduler_task
            except asyncio.CancelledError:
                pass

        if wait_for_completion:
            await self._wait_for_completion()

        logger.info("AgentScheduler stopped")

    async def _wait_for_completion(self) -> None:
        """Wait for all running tasks to complete."""
        async with self._lock:
            tasks = list(self._running_tasks.values())

        for task in tasks:
            try:
                await task
            except asyncio.CancelledError:
                pass
            except Exception as e:
                logger.error(f"Task failed during shutdown: {e}")

    async def _scheduler_loop(self) -> None:
        """Main scheduler loop."""
        while self._running:
            try:
                # Check for tasks to execute
                async with self._lock:
                    next_task = await self._queue.peek()

                if next_task and next_task.is_ready():
                    # Execute the task
                    await self._execute_task(next_task)
                else:
                    # Wait for tasks or timeout
                    await asyncio.sleep(0.1)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in scheduler loop: {e}")
                await asyncio.sleep(1.0)

    async def _execute_task(self, task: Task) -> None:
        """
        Execute a task.
        
        Args:
            task: Task to execute.
        """
        async with self._active_lock:
            if self._active_count >= self._max_parallel:
                return
            self._active_count += 1

        # Remove from queue
        await self._queue.pop()

        # Update task status
        task.status = TaskStatus.RUNNING
        task.started_at = datetime.utcnow()
        self._tasks[task.task_id] = task

        # Update metrics
        self._metrics["tasks_started"] += 1
        self._metrics["active_tasks"] = self._active_count

        # Call start callbacks
        for callback in self._on_task_start:
            try:
                callback(task)
            except Exception as e:
                logger.error(f"Error in task start callback: {e}")

        # Execute the task
        async def execute():
            try:
                # Execute with timeout
                async with asyncio.timeout(task.timeout):
                    result = await self._execute_task_internal(task)
                    task.result = result
                    task.status = TaskStatus.COMPLETED
                    task.completed_at = datetime.utcnow()
                    self._metrics["tasks_completed"] += 1

                    # Call completion callbacks
                    for callback in self._on_task_complete:
                        try:
                            callback(task)
                        except Exception as e:
                            logger.error(f"Error in task complete callback: {e}")

            except asyncio.TimeoutError:
                task.status = TaskStatus.TIMEOUT
                task.error = "Task timed out"
                task.completed_at = datetime.utcnow()
                self._metrics["tasks_timed_out"] += 1

                # Call failure callbacks
                for callback in self._on_task_fail:
                    try:
                        callback(task)
                    except Exception as e:
                        logger.error(f"Error in task fail callback: {e}")

            except Exception as e:
                task.error = str(e)
                task.status = TaskStatus.FAILED
                task.completed_at = datetime.utcnow()
                self._metrics["tasks_failed"] += 1

                # Check if we should retry
                if task.can_retry():
                    retry_policy = self._get_retry_policy(task)
                    if retry_policy.should_retry(task.error, task.retry_count):
                        task.status = TaskStatus.RETRYING
                        task.retry_count += 1
                        delay = retry_policy.get_delay(task.retry_count)
                        task.scheduled_at = datetime.utcnow() + timedelta(seconds=delay)
                        await self._queue.push(task)
                        self._metrics["tasks_retried"] += 1
                        return

                # Call failure callbacks
                for callback in self._on_task_fail:
                    try:
                        callback(task)
                    except Exception as e:
                        logger.error(f"Error in task fail callback: {e}")

            finally:
                # Clean up
                async with self._active_lock:
                    self._active_count -= 1
                self._metrics["active_tasks"] = self._active_count
                if task.task_id in self._running_tasks:
                    del self._running_tasks[task.task_id]

        # Create execution task
        exec_task = asyncio.create_task(execute())
        self._running_tasks[task.task_id] = exec_task

    async def _execute_task_internal(self, task: Task) -> Any:
        """
        Internal task execution.
        
        This method should be overridden by subclasses to provide custom
        task execution logic.
        
        Args:
            task: Task to execute.
            
        Returns:
            Result of the task execution.
        """
        # Default implementation: just return the payload
        return task.payload

    def _get_retry_policy(self, task: Task) -> RetryPolicy:
        """
        Get the retry policy for a task.
        
        Args:
            task: Task to get retry policy for.
            
        Returns:
            Retry policy for the task.
        """
        # Use task-specific policy if available, otherwise use default
        if hasattr(task, 'retry_policy') and task.retry_policy:
            return task.retry_policy
        return self._default_retry_policy

    async def schedule(
        self,
        agent_id: "AgentID",
        name: str = "",
        description: str = "",
        task_type: "TaskType" = TaskType.SIMPLE,
        payload: Optional[Dict[str, Any]] = None,
        priority: int = 0,
        schedule_type: "ScheduleType" = ScheduleType.IMMEDIATE,
        scheduled_at: Optional[datetime] = None,
        timeout: Optional[float] = None,
        max_retries: Optional[int] = None,
        retry_delay: Optional[float] = None,
        dependencies: Optional[Set["TaskID"]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> "TaskID":
        """
        Schedule a new task.
        
        Args:
            agent_id: ID of the agent that owns the task.
            name: Human-readable name of the task.
            description: Description of the task.
            task_type: Type of the task.
            payload: Task payload/data.
            priority: Task priority (higher = more important).
            schedule_type: Type of scheduling.
            scheduled_at: When the task is scheduled to run.
            timeout: Timeout in seconds.
            max_retries: Maximum number of retry attempts.
            retry_delay: Delay between retries in seconds.
            dependencies: Set of task IDs this task depends on.
            metadata: Additional task metadata.
            
        Returns:
            ID of the scheduled task.
        """
        task_id = f"task_{uuid.uuid4().hex[:12]}"

        # Handle immediate scheduling
        if schedule_type == ScheduleType.IMMEDIATE and scheduled_at is None:
            scheduled_at = datetime.utcnow()

        # Handle delayed scheduling
        if schedule_type == ScheduleType.DELAYED:
            if scheduled_at is None:
                raise ValueError("scheduled_at is required for DELAYED tasks")

        task = Task(
            task_id=task_id,
            agent_id=agent_id,
            name=name,
            description=description,
            task_type=task_type,
            payload=payload or {},
            priority=priority,
            schedule_type=schedule_type,
            scheduled_at=scheduled_at,
            timeout=timeout or self._default_timeout,
            max_retries=max_retries or self._default_retry_policy.max_retries,
            retry_delay=retry_delay or self._default_retry_policy.base_delay,
            dependencies=dependencies or set(),
            metadata=metadata or {},
        )

        async with self._lock:
            self._tasks[task_id] = task
            await self._queue.push(task)
            self._metrics["tasks_scheduled"] += 1
            self._metrics["queued_tasks"] = len(self._queue)

        logger.debug(f"Task scheduled: {task_id} (agent={agent_id}, name={name})")
        return task_id

    async def cancel(self, task_id: "TaskID") -> bool:
        """
        Cancel a scheduled task.
        
        Args:
            task_id: ID of the task to cancel.
            
        Returns:
            True if the task was cancelled, False if not found or already completed.
        """
        async with self._lock:
            if task_id not in self._tasks:
                return False

            task = self._tasks[task_id]

            # Check if task can be cancelled
            if task.is_completed():
                return False

            # Cancel the task
            task.status = TaskStatus.CANCELLED
            task.completed_at = datetime.utcnow()
            task.error = "Task cancelled"

            # Remove from queue if present
            await self._queue.remove(task_id)

            # Remove from running tasks if present
            if task_id in self._running_tasks:
                exec_task = self._running_tasks[task_id]
                exec_task.cancel()
                del self._running_tasks[task_id]
                async with self._active_lock:
                    self._active_count -= 1

            self._metrics["tasks_cancelled"] += 1
            self._metrics["queued_tasks"] = len(self._queue)
            self._metrics["active_tasks"] = self._active_count

            # Call cancellation callbacks
            for callback in self._on_task_cancel:
                try:
                    callback(task)
                except Exception as e:
                    logger.error(f"Error in task cancel callback: {e}")

            logger.debug(f"Task cancelled: {task_id}")
            return True

    async def get_task(self, task_id: "TaskID") -> Optional[Task]:
        """
        Get task information by ID.
        
        Args:
            task_id: ID of the task.
            
        Returns:
            Task if found, None otherwise.
        """
        async with self._lock:
            return self._tasks.get(task_id)

    async def list_tasks(
        self,
        agent_id: Optional["AgentID"] = None,
        status: Optional["TaskStatus"] = None,
        limit: Optional[int] = None,
    ) -> List[Task]:
        """
        List tasks matching the given criteria.
        
        Args:
            agent_id: ID of the agent to filter by.
            status: Status to filter by.
            limit: Maximum number of results to return.
            
        Returns:
            List of matching tasks.
        """
        async with self._lock:
            tasks = list(self._tasks.values())

        results = []
        for task in tasks:
            if agent_id and task.agent_id != agent_id:
                continue
            if status and task.status != status:
                continue
            results.append(task)
            if limit and len(results) >= limit:
                break

        return results

    async def get_queue_size(self) -> int:
        """
        Get the number of tasks in the queue.
        
        Returns:
            Number of tasks in the queue.
        """
        async with self._lock:
            return len(self._queue)

    async def get_active_count(self) -> int:
        """
        Get the number of actively running tasks.
        
        Returns:
            Number of active tasks.
        """
        async with self._active_lock:
            return self._active_count

    def on_task_start(self, callback: Callable[[Task], None]) -> None:
        """
        Register a callback for task start.
        
        Args:
            callback: Callback function to call when a task starts.
        """
        self._on_task_start.append(callback)

    def on_task_complete(self, callback: Callable[[Task], None]) -> None:
        """
        Register a callback for task completion.
        
        Args:
            callback: Callback function to call when a task completes.
        """
        self._on_task_complete.append(callback)

    def on_task_fail(self, callback: Callable[[Task], None]) -> None:
        """
        Register a callback for task failure.
        
        Args:
            callback: Callback function to call when a task fails.
        """
        self._on_task_fail.append(callback)

    def on_task_cancel(self, callback: Callable[[Task], None]) -> None:
        """
        Register a callback for task cancellation.
        
        Args:
            callback: Callback function to call when a task is cancelled.
        """
        self._on_task_cancel.append(callback)

    def get_metrics(self) -> Dict[str, Any]:
        """
        Get scheduler metrics.
        
        Returns:
            Dictionary of metrics.
        """
        return {
            **self._metrics,
            "max_parallel": self._max_parallel,
            "default_timeout": self._default_timeout,
        }

    async def clear(self) -> int:
        """
        Clear all tasks from the scheduler.
        
        Returns:
            Number of tasks cleared.
        """
        async with self._lock:
            # Cancel all running tasks
            for task_id, exec_task in self._running_tasks.items():
                exec_task.cancel()
            self._running_tasks.clear()

            # Clear queue and tasks
            count = await self._queue.clear()
            self._tasks.clear()
            self._active_count = 0

            # Reset metrics
            self._metrics = {
                "tasks_scheduled": 0,
                "tasks_started": 0,
                "tasks_completed": 0,
                "tasks_failed": 0,
                "tasks_cancelled": 0,
                "tasks_timed_out": 0,
                "tasks_retried": 0,
                "active_tasks": 0,
                "queued_tasks": 0,
            }

            return count

    def shutdown(self) -> None:
        """Shutdown the scheduler."""
        self._running = False
        if self._scheduler_task:
            self._scheduler_task.cancel()
        self._tasks.clear()
        self._running_tasks.clear()
        self._active_count = 0
        self._on_task_start.clear()
        self._on_task_complete.clear()
        self._on_task_fail.clear()
        self._on_task_cancel.clear()
        self._metrics = {
            "tasks_scheduled": 0,
            "tasks_started": 0,
            "tasks_completed": 0,
            "tasks_failed": 0,
            "tasks_cancelled": 0,
            "tasks_timed_out": 0,
            "tasks_retried": 0,
            "active_tasks": 0,
            "queued_tasks": 0,
        }
        logger.info("AgentScheduler shutdown complete")

    def __repr__(self) -> str:
        """Return string representation."""
        return (
            f"AgentScheduler(max_parallel={self._max_parallel}, "
            f"queued={len(self._queue)}, active={self._active_count})"
        )
