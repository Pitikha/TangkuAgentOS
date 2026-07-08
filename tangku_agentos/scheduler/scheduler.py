"""
Core Scheduler Implementation with Dependency Resolution

Implements task scheduling with:
- Priority-based execution
- Dependency graph resolution
- Delayed execution support
- Retry logic with exponential backoff
- Task lifecycle management
"""

from typing import Dict, List, Optional, Any, Callable
from datetime import datetime, timedelta
import asyncio
import logging
from collections import defaultdict, deque

from tangku_agentos.scheduler.task import Task, TaskState, TaskPriority, TaskDependency
from tangku_agentos.scheduler.queue import TaskQueue, DeadLetterQueue
from tangku_agentos.scheduler.executors import ExecutorPool

logger = logging.getLogger(__name__)


class DependencyResolver:
    """Resolves task dependencies and validates dependency graphs."""

    def __init__(self):
        self.task_graph: Dict[str, List[str]] = defaultdict(list)
        self.reverse_graph: Dict[str, List[str]] = defaultdict(list)

    def add_dependency(self, task_id: str, depends_on: str) -> None:
        """Add dependency edge: task_id depends on depends_on."""
        self.task_graph[task_id].append(depends_on)
        self.reverse_graph[depends_on].append(task_id)

    def can_execute(
        self,
        task: Task,
        completed_tasks: set,
    ) -> bool:
        """Check if all dependencies are satisfied."""
        for dep in task.dependencies:
            if dep.depends_on_task_id not in completed_tasks:
                return False
        return True

    def get_dependents(self, task_id: str) -> List[str]:
        """Get all tasks that depend on this task."""
        return self.reverse_graph.get(task_id, [])

    def has_circular_dependency(self) -> bool:
        """Detect circular dependencies using DFS."""
        visited = set()
        rec_stack = set()

        def dfs(node: str) -> bool:
            visited.add(node)
            rec_stack.add(node)

            for neighbor in self.task_graph.get(node, []):
                if neighbor not in visited:
                    if dfs(neighbor):
                        return True
                elif neighbor in rec_stack:
                    return True

            rec_stack.remove(node)
            return False

        for node in self.task_graph:
            if node not in visited:
                if dfs(node):
                    return True
        return False

    def topological_sort(self) -> List[str]:
        """Get topological order of tasks (for analysis only)."""
        visited = set()
        stack = []

        def dfs(node: str):
            visited.add(node)
            for neighbor in self.task_graph.get(node, []):
                if neighbor not in visited:
                    dfs(neighbor)
            stack.append(node)

        for node in self.task_graph:
            if node not in visited:
                dfs(node)

        return stack[::-1]


class Scheduler:
    """
    Production-grade task scheduler with dependency resolution,
    retry logic, and multiple execution backends.
    """

    def __init__(
        self,
        max_concurrent_tasks: int = 10,
        default_timeout: Optional[timedelta] = None,
    ):
        self.queue = TaskQueue(name="main")
        self.delayed_queue = TaskQueue(name="delayed")
        self.retry_queue = TaskQueue(name="retry")
        self.dead_letter_queue = DeadLetterQueue()
        
        self.tasks: Dict[str, Task] = {}
        self.completed_tasks: set = set()
        self.running_tasks: Dict[str, asyncio.Task] = {}
        self.paused_tasks: set = set()
        
        self.dependency_resolver = DependencyResolver()
        self.executor_pool = ExecutorPool()
        
        self.max_concurrent_tasks = max_concurrent_tasks
        self.default_timeout = default_timeout
        
        self.is_running = False
        self.metrics = {
            "tasks_submitted": 0,
            "tasks_completed": 0,
            "tasks_failed": 0,
            "tasks_retried": 0,
            "tasks_cancelled": 0,
        }

    def submit(
        self,
        task_func: Callable,
        args: tuple = (),
        kwargs: Optional[Dict[str, Any]] = None,
        priority: TaskPriority = TaskPriority.NORMAL,
        name: str = "",
        delay: Optional[timedelta] = None,
        timeout: Optional[timedelta] = None,
        max_retries: int = 3,
        tags: Optional[List[str]] = None,
    ) -> str:
        """
        Submit task for scheduling.

        Returns:
            Task ID
        """
        task = Task(
            name=name or task_func.__name__,
            task_func=task_func,
            args=args,
            kwargs=kwargs or {},
            priority=priority,
            timeout=timeout or self.default_timeout,
            max_retries=max_retries,
        )

        if tags:
            task.tags = tags

        if delay:
            task.scheduled_for = datetime.utcnow() + delay

        self.tasks[task.task_id] = task
        self.metrics["tasks_submitted"] += 1

        # Queue in appropriate queue
        if task.scheduled_for:
            self.delayed_queue.enqueue(task)
            task.state = TaskState.QUEUED
            logger.info(
                f"Task {task.task_id} scheduled for {task.scheduled_for}"
            )
        else:
            self.queue.enqueue(task)
            task.state = TaskState.QUEUED
            logger.info(f"Task {task.task_id} submitted")

        return task.task_id

    def submit_with_dependencies(
        self,
        task_func: Callable,
        depends_on: Optional[List[str]] = None,
        **kwargs
    ) -> str:
        """Submit task with dependencies."""
        task_id = self.submit(task_func, **kwargs)
        task = self.tasks[task_id]

        if depends_on:
            for dep_id in depends_on:
                dep_task = self.tasks.get(dep_id)
                if dep_task:
                    task.add_dependency(dep_id)
                    self.dependency_resolver.add_dependency(task_id, dep_id)

        return task_id

    async def start(self) -> None:
        """Start scheduler."""
        self.is_running = True
        logger.info("Scheduler started")

        try:
            while self.is_running:
                # Move due delayed tasks to main queue
                await self._process_delayed_queue()

                # Check for tasks ready to run
                ready_tasks = []
                for _ in range(self.max_concurrent_tasks - len(self.running_tasks)):
                    task = self.queue.dequeue()
                    if task:
                        ready_tasks.append(task)

                # Execute ready tasks
                for task in ready_tasks:
                    await self._execute_task(task)

                # Process completed tasks
                await self._process_completed_tasks()

                # Check paused tasks
                await self._process_paused_tasks()

                # Check retry queue
                await self._process_retry_queue()

                await asyncio.sleep(0.1)
        except Exception as e:
            logger.error(f"Scheduler error: {e}")
            raise

    async def _process_delayed_queue(self) -> None:
        """Move due delayed tasks to main queue."""
        while not self.delayed_queue.is_empty():
            task = self.delayed_queue.peek()
            if task and task.is_due():
                self.delayed_queue.dequeue()
                self.queue.enqueue(task)
            else:
                break

    async def _execute_task(self, task: Task) -> None:
        """Execute task if dependencies are met."""
        # Check dependencies
        if not self.dependency_resolver.can_execute(task, self.completed_tasks):
            self.queue.enqueue(task)
            return

        task.state = TaskState.RUNNING
        task.started_at = datetime.utcnow()
        logger.info(f"Task {task.task_id} started")

        async def run_task():
            try:
                # Check timeout
                if task.should_timeout():
                    raise TimeoutError(f"Task {task.task_id} exceeded timeout")

                # Execute
                result = await self.executor_pool.execute(task)
                task.result = result
                task.state = TaskState.COMPLETED
                task.completed_at = datetime.utcnow()
                self.completed_tasks.add(task.task_id)
                self.metrics["tasks_completed"] += 1

                logger.info(
                    f"Task {task.task_id} completed in "
                    f"{task.duration_seconds():.2f}s"
                )

            except Exception as e:
                logger.error(f"Task {task.task_id} failed: {e}")
                task.last_error = str(e)
                task.state = TaskState.FAILED
                self.metrics["tasks_failed"] += 1

                # Check if can retry
                if task.can_retry():
                    task.retry_count += 1
                    task.state = TaskState.RETRYING
                    delay = task.get_next_retry_delay()
                    task.scheduled_for = datetime.utcnow() + delay
                    self.retry_queue.enqueue(task)
                    self.metrics["tasks_retried"] += 1
                    logger.info(
                        f"Task {task.task_id} scheduled for retry "
                        f"({task.retry_count}/{task.max_retries})"
                    )
                else:
                    self.dead_letter_queue.add(task, reason=str(e))

            finally:
                if task.task_id in self.running_tasks:
                    del self.running_tasks[task.task_id]

        task_obj = asyncio.create_task(run_task())
        self.running_tasks[task.task_id] = task_obj

    async def _process_completed_tasks(self) -> None:
        """Process completed tasks and wake dependents."""
        completed_ids = [
            task_id
            for task_id, task_obj in list(self.running_tasks.items())
            if task_obj.done()
        ]

        for task_id in completed_ids:
            del self.running_tasks[task_id]

    async def _process_paused_tasks(self) -> None:
        """Process paused tasks (resume if resumed flag set)."""
        pass  # Implement resume logic

    async def _process_retry_queue(self) -> None:
        """Move due retry tasks to main queue."""
        while not self.retry_queue.is_empty():
            task = self.retry_queue.peek()
            if task and task.is_due():
                self.retry_queue.dequeue()
                self.queue.enqueue(task)
            else:
                break

    def pause_task(self, task_id: str) -> bool:
        """Pause a running task."""
        if task_id in self.running_tasks:
            self.paused_tasks.add(task_id)
            return True
        return False

    def resume_task(self, task_id: str) -> bool:
        """Resume a paused task."""
        if task_id in self.paused_tasks:
            self.paused_tasks.remove(task_id)
            return True
        return False

    def cancel_task(self, task_id: str) -> bool:
        """Cancel a task."""
        task = self.tasks.get(task_id)
        if not task:
            return False

        if task_id in self.running_tasks:
            self.running_tasks[task_id].cancel()
            del self.running_tasks[task_id]

        task.state = TaskState.CANCELLED
        self.metrics["tasks_cancelled"] += 1
        logger.info(f"Task {task_id} cancelled")
        return True

    def get_task(self, task_id: str) -> Optional[Task]:
        """Get task by ID."""
        return self.tasks.get(task_id)

    def get_task_status(self, task_id: str) -> Optional[str]:
        """Get task status."""
        task = self.tasks.get(task_id)
        return task.state.value if task else None

    def get_metrics(self) -> Dict[str, Any]:
        """Get scheduler metrics."""
        return {
            **self.metrics,
            "queue_depth": self.queue.size(),
            "delayed_queue_depth": self.delayed_queue.size(),
            "retry_queue_depth": self.retry_queue.size(),
            "dlq_depth": self.dead_letter_queue.size(),
            "running_tasks": len(self.running_tasks),
            "paused_tasks": len(self.paused_tasks),
            "completed_tasks": len(self.completed_tasks),
        }

    def stop(self) -> None:
        """Stop scheduler."""
        self.is_running = False
        self.executor_pool.shutdown_all()
        logger.info("Scheduler stopped")
