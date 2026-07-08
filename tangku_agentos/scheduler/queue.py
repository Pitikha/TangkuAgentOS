"""
Task Queue Management for Scheduler

Implements priority queues, FIFO ordering, and queue operations.
"""

from typing import List, Optional, Dict, Any, Callable
from dataclasses import dataclass, field
from datetime import datetime
from heapq import heappush, heappop
import logging

from tangku_agentos.scheduler.task import Task, TaskState, TaskPriority

logger = logging.getLogger(__name__)


@dataclass
class QueueMetrics:
    """Queue performance metrics."""
    total_enqueued: int = 0
    total_dequeued: int = 0
    peak_depth: int = 0
    current_depth: int = 0
    avg_wait_time_ms: float = 0.0
    total_wait_time_ms: float = 0.0


class TaskQueue:
    """
    Thread-safe priority queue for tasks.
    
    Supports:
    - Priority-based ordering
    - FIFO within same priority
    - Throttling and rate limiting
    - Queue depth monitoring
    """

    def __init__(
        self,
        name: str = "default",
        max_size: Optional[int] = None,
        throttle_rate: Optional[int] = None,
    ):
        self.name = name
        self.max_size = max_size
        self.throttle_rate = throttle_rate  # Tasks per second
        self.heap: List[tuple] = []  # (priority, sequence, task)
        self.sequence_counter = 0
        self.metrics = QueueMetrics()
        self.last_throttle_time: Optional[datetime] = None

    def enqueue(self, task: Task) -> bool:
        """
        Add task to queue.

        Returns:
            True if successful, False if queue full
        """
        if self.max_size and len(self.heap) >= self.max_size:
            logger.warning(f"Queue '{self.name}' is full")
            return False

        # Lower priority value = higher priority (execute first)
        priority_value = task.priority.value
        self.sequence_counter += 1

        heappush(
            self.heap,
            (priority_value, self.sequence_counter, task)
        )

        self.metrics.total_enqueued += 1
        self.metrics.current_depth = len(self.heap)
        if self.metrics.current_depth > self.metrics.peak_depth:
            self.metrics.peak_depth = self.metrics.current_depth

        logger.debug(f"Task {task.task_id} enqueued to '{self.name}'")
        return True

    def dequeue(self) -> Optional[Task]:
        """
        Remove and return highest priority task.

        Returns:
            Task if available, None if queue empty
        """
        if not self.heap:
            return None

        # Check throttling
        if self.throttle_rate and self.last_throttle_time:
            elapsed = (datetime.utcnow() - self.last_throttle_time).total_seconds()
            if elapsed < (1.0 / self.throttle_rate):
                return None  # Throttled

        priority_value, sequence, task = heappop(self.heap)

        self.metrics.total_dequeued += 1
        self.metrics.current_depth = len(self.heap)

        # Update wait time
        wait_time = (datetime.utcnow() - task.created_at).total_seconds() * 1000
        self.metrics.total_wait_time_ms += wait_time
        self.metrics.avg_wait_time_ms = (
            self.metrics.total_wait_time_ms / self.metrics.total_dequeued
        )

        self.last_throttle_time = datetime.utcnow()

        logger.debug(f"Task {task.task_id} dequeued from '{self.name}'")
        return task

    def peek(self) -> Optional[Task]:
        """Get highest priority task without removing."""
        if not self.heap:
            return None
        return self.heap[0][2]

    def size(self) -> int:
        """Get current queue depth."""
        return len(self.heap)

    def is_empty(self) -> bool:
        """Check if queue is empty."""
        return len(self.heap) == 0

    def clear(self) -> int:
        """Clear queue. Returns count of tasks cleared."""
        count = len(self.heap)
        self.heap.clear()
        self.metrics.current_depth = 0
        logger.info(f"Queue '{self.name}' cleared: {count} tasks")
        return count

    def find_task(self, task_id: str) -> Optional[Task]:
        """Find task in queue by ID."""
        for _, _, task in self.heap:
            if task.task_id == task_id:
                return task
        return None

    def remove_task(self, task_id: str) -> bool:
        """Remove specific task from queue."""
        original_size = len(self.heap)
        self.heap = [
            (p, s, t) for p, s, t in self.heap
            if t.task_id != task_id
        ]
        if len(self.heap) < original_size:
            logger.debug(f"Task {task_id} removed from queue '{self.name}'")
            return True
        return False

    def get_tasks_by_priority(
        self, priority: TaskPriority
    ) -> List[Task]:
        """Get all tasks with specific priority."""
        return [
            task for _, _, task in self.heap
            if task.priority == priority
        ]

    def get_metrics(self) -> Dict[str, Any]:
        """Get queue metrics."""
        return {
            "queue_name": self.name,
            "total_enqueued": self.metrics.total_enqueued,
            "total_dequeued": self.metrics.total_dequeued,
            "current_depth": self.metrics.current_depth,
            "peak_depth": self.metrics.peak_depth,
            "avg_wait_time_ms": self.metrics.avg_wait_time_ms,
        }


class DeadLetterQueue:
    """
    Separate queue for failed tasks.
    
    Stores tasks that have exhausted retries.
    """

    def __init__(self, max_size: int = 10000):
        self.max_size = max_size
        self.tasks: List[Task] = []

    def add(self, task: Task, reason: str = "max_retries_exceeded") -> bool:
        """Add failed task to dead-letter queue."""
        if len(self.tasks) >= self.max_size:
            logger.warning("Dead-letter queue is full")
            return False

        task.metadata["dlq_reason"] = reason
        task.metadata["dlq_added_at"] = datetime.utcnow().isoformat()
        self.tasks.append(task)

        logger.warning(
            f"Task {task.task_id} moved to DLQ: {reason}"
        )
        return True

    def get_tasks(self, limit: int = 100) -> List[Task]:
        """Get tasks from dead-letter queue."""
        return self.tasks[-limit:]

    def remove_task(self, task_id: str) -> bool:
        """Remove task from DLQ."""
        original_size = len(self.tasks)
        self.tasks = [t for t in self.tasks if t.task_id != task_id]
        return len(self.tasks) < original_size

    def clear(self) -> int:
        """Clear DLQ. Returns count of tasks cleared."""
        count = len(self.tasks)
        self.tasks.clear()
        return count

    def size(self) -> int:
        """Get DLQ size."""
        return len(self.tasks)
