"""
Core Task Model for Scheduler

Defines task structure, priority, state, and lifecycle management.
"""

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, Optional, List
from datetime import datetime, timedelta
from enum import Enum
import uuid


class TaskState(Enum):
    """Task execution states."""
    PENDING = "pending"
    QUEUED = "queued"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRYING = "retrying"
    CANCELLED = "cancelled"


class TaskPriority(Enum):
    """Task priority levels."""
    LOWEST = 4
    LOW = 3
    NORMAL = 2
    HIGH = 1
    CRITICAL = 0


@dataclass
class TaskDependency:
    """Task dependency tracking."""
    depends_on_task_id: str = ""
    dependency_type: str = "blocking"  # blocking, soft, data_flow
    required_status: str = "completed"  # completed, succeeded, any


@dataclass
class Task:
    """
    Core task model for scheduler.
    
    Supports:
    - Priority-based execution
    - Dependency graphs
    - Delayed execution
    - Recurring tasks
    - Retry logic
    - Cancellation tokens
    - Timeout handling
    """
    task_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    task_func: Optional[Callable] = None
    args: tuple = field(default_factory=tuple)
    kwargs: Dict[str, Any] = field(default_factory=dict)
    
    # Priority and Scheduling
    priority: TaskPriority = TaskPriority.NORMAL
    created_at: datetime = field(default_factory=datetime.utcnow)
    scheduled_for: Optional[datetime] = None  # For delayed tasks
    
    # State Management
    state: TaskState = TaskState.PENDING
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    # Dependencies
    dependencies: List[TaskDependency] = field(default_factory=list)
    dependent_tasks: List[str] = field(default_factory=list)
    
    # Retry and Recovery
    max_retries: int = 3
    retry_count: int = 0
    retry_delay: timedelta = field(default_factory=lambda: timedelta(seconds=5))
    retry_backoff: float = 1.5  # Exponential backoff multiplier
    last_error: Optional[str] = None
    
    # Timeout and Cancellation
    timeout: Optional[timedelta] = None
    cancellation_token: Optional[str] = None
    
    # Execution Context
    executor_backend: str = "thread"  # thread, process, asyncio
    result: Any = None
    group_id: Optional[str] = None  # For task grouping/batching
    
    # Metadata
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def is_due(self) -> bool:
        """Check if task is ready to execute."""
        if self.scheduled_for is None:
            return True
        return datetime.utcnow() >= self.scheduled_for

    def can_retry(self) -> bool:
        """Check if task can be retried."""
        return (
            self.state == TaskState.FAILED
            and self.retry_count < self.max_retries
        )

    def should_timeout(self) -> bool:
        """Check if task has exceeded timeout."""
        if self.timeout is None or self.started_at is None:
            return False
        elapsed = datetime.utcnow() - self.started_at
        return elapsed > self.timeout

    def get_next_retry_delay(self) -> timedelta:
        """Calculate next retry delay with exponential backoff."""
        base_seconds = self.retry_delay.total_seconds()
        backoff_seconds = base_seconds * (self.retry_backoff ** self.retry_count)
        return timedelta(seconds=backoff_seconds)

    def add_dependency(
        self,
        task_id: str,
        dependency_type: str = "blocking",
        required_status: str = "completed",
    ) -> None:
        """Add task dependency."""
        dep = TaskDependency(
            depends_on_task_id=task_id,
            dependency_type=dependency_type,
            required_status=required_status,
        )
        self.dependencies.append(dep)

    def add_tag(self, tag: str) -> None:
        """Add metadata tag."""
        if tag not in self.tags:
            self.tags.append(tag)

    def duration_seconds(self) -> float:
        """Get task execution duration in seconds."""
        if self.started_at is None:
            return 0.0
        end = self.completed_at or datetime.utcnow()
        delta = end - self.started_at
        return delta.total_seconds()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "task_id": self.task_id,
            "name": self.name,
            "priority": self.priority.name,
            "state": self.state.value,
            "created_at": self.created_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "retry_count": self.retry_count,
            "duration_seconds": self.duration_seconds(),
            "tags": self.tags,
            "metadata": self.metadata,
        }
