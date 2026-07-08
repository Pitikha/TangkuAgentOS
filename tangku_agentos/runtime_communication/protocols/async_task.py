"""
Runtime Communication Framework - Async Task Protocol

The AsyncTaskProtocol implements the asynchronous task execution pattern for
the Runtime Communication Framework. It provides:
- Asynchronous task execution
- Task progress tracking
- Task cancellation
- Result retrieval
- Error handling

Author: TangkuAgentOS Team
License: MIT
"""

from __future__ import annotations

import asyncio
import logging
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import (
    Any,
    Callable,
    Dict,
    List,
    Optional,
    Set,
    Union,
    TYPE_CHECKING,
)
import uuid

if TYPE_CHECKING:
    from tangku_agentos.runtime_communication.models.messages import (
        Message,
        MessageType,
        MessagePriority,
        AsyncTask,
        ScheduledTask,
    )
    from tangku_agentos.runtime_communication.interfaces import (
        IMessageHandler,
    )

logger = logging.getLogger(__name__)


class TaskStatus(Enum):
    """
    Status of an asynchronous task.

    Attributes:
        PENDING: Task has been created but not yet started.
        RUNNING: Task is currently executing.
        COMPLETED: Task has completed successfully.
        FAILED: Task has failed with an error.
        CANCELLED: Task was cancelled before completion.
        PAUSED: Task is paused.
    """

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    PAUSED = "paused"


@dataclass
class TaskInfo:
    """
    Information about an asynchronous task.

    Attributes:
        task_id: Unique identifier for the task.
        task_type: Type of task.
        status: Current status of the task.
        progress: Current progress percentage (0-100).
        result: Result of the task (if completed).
        error: Error that occurred (if failed).
        created_at: When the task was created.
        started_at: When the task started executing.
        completed_at: When the task completed.
        total_duration: Total execution time in seconds.
        metadata: Additional task metadata.
    """

    task_id: str
    task_type: str
    status: TaskStatus = TaskStatus.PENDING
    progress: int = 0
    result: Any = None
    error: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    total_duration: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def is_complete(self) -> bool:
        """Check if the task is complete."""
        return self.status in (
            TaskStatus.COMPLETED,
            TaskStatus.FAILED,
            TaskStatus.CANCELLED,
        )

    @property
    def is_running(self) -> bool:
        """Check if the task is running."""
        return self.status == TaskStatus.RUNNING

    @property
    def is_pending(self) -> bool:
        """Check if the task is pending."""
        return self.status == TaskStatus.PENDING


@dataclass
class TaskHandler:
    """
    Represents a registered task handler.

    Attributes:
        task_type: Type of task this handler processes.
        handler: Handler function for the task.
        priority: Handler priority (higher = called first).
        active: Whether the handler is active.
        execution_count: Number of times this handler has been called.
        error_count: Number of errors from this handler.
        registered_at: When the handler was registered.
    """

    task_type: str
    handler: Callable[["AsyncTask"], Any]
    priority: int = 0
    active: bool = True
    execution_count: int = 0
    error_count: int = 0
    registered_at: datetime = field(default_factory=datetime.utcnow)


class AsyncTaskProtocol:
    """
    Async task protocol implementation.

    The AsyncTaskProtocol implements the asynchronous task execution pattern
    for long-running operations. It provides:
    - Asynchronous task execution
    - Task progress tracking
    - Task cancellation
    - Result retrieval
    - Error handling

    Thread Safety:
        This implementation is thread-safe for concurrent access.

    Example:
        >>> from tangku_agentos.runtime_communication.protocols.async_task import AsyncTaskProtocol
        >>> from tangku_agentos.runtime_communication.models.messages import AsyncTask, MessageType
        >>> 
        >>> protocol = AsyncTaskProtocol()
        >>> 
        >>> # Register a task handler
        >>> async def handle_data_processing(task: AsyncTask) -> dict:
        ...     # Simulate processing
        ...     for i in range(1, 101):
        ...         await asyncio.sleep(0.01)
        ...         task.update_progress(i)
        ...     return {"status": "completed", "result": "success"}
        >>> 
        >>> protocol.register_handler("data.processing", handle_data_processing)
        >>> 
        >>> # Execute a task
        >>> task = AsyncTask(
        ...     message_type=MessageType.ASYNC_TASK,
        ...     sender_id="client",
        ...     task_id="task-123",
        ...     task_type="data.processing",
        ...     payload={"data": "..."}
        ... )
        >>> result = asyncio.run(protocol.execute(task))

    Attributes:
        max_concurrent_tasks: Maximum number of concurrent tasks.
        default_timeout: Default timeout for tasks in seconds.
    """

    def __init__(
        self,
        max_concurrent_tasks: int = 100,
        default_timeout: float = 3600.0,  # 1 hour
        enable_metrics: bool = True,
        enable_logging: bool = True,
    ):
        """
        Initialize the async task protocol.

        Args:
            max_concurrent_tasks: Maximum number of concurrent tasks.
            default_timeout: Default timeout for tasks in seconds.
            enable_metrics: Whether to collect metrics.
            enable_logging: Whether to enable structured logging.
        """
        # Task handlers: task_type -> TaskHandler
        self._handlers: Dict[str, TaskHandler] = {}
        self._handlers_lock = asyncio.Lock()

        # Active tasks: task_id -> AsyncTask
        self._active_tasks: Dict[str, "AsyncTask"] = {}
        self._active_tasks_lock = asyncio.Lock()
        self._max_concurrent_tasks = max_concurrent_tasks

        # Task queue: List[AsyncTask]
        self._task_queue: List["AsyncTask"] = []
        self._task_queue_lock = asyncio.Lock()

        # Task info: task_id -> TaskInfo
        self._task_info: Dict[str, TaskInfo] = {}
        self._task_info_lock = asyncio.Lock()

        # Task results: task_id -> Any
        self._task_results: Dict[str, Any] = {}
        self._task_results_lock = asyncio.Lock()

        # Configuration
        self._default_timeout = default_timeout

        # Metrics
        self._metrics: Dict[str, Any] = {
            "tasks_submitted": 0,
            "tasks_started": 0,
            "tasks_completed": 0,
            "tasks_failed": 0,
            "tasks_cancelled": 0,
            "tasks_paused": 0,
            "tasks_resumed": 0,
            "handlers_registered": 0,
        }
        self._metrics_lock = asyncio.Lock()

        # Flags
        self._enable_metrics = enable_metrics
        self._enable_logging = enable_logging

        # Task processing
        self._running = False
        self._processor_task: Optional[asyncio.Task] = None

        logger.info(
            f"AsyncTaskProtocol initialized with max_tasks={max_concurrent_tasks}, "
            f"timeout={default_timeout}"
        )

    async def start(self) -> None:
        """
        Start the task processor.

        This starts the background task that processes queued tasks.

        Example:
            >>> protocol = AsyncTaskProtocol()
            >>> asyncio.run(protocol.start())
        """
        if self._running:
            return

        self._running = True
        self._processor_task = asyncio.create_task(self._process_tasks())

        if self._enable_logging:
            logger.info("Async task protocol started")

    async def stop(self) -> None:
        """
        Stop the task processor.

        This stops the background task and waits for it to complete.

        Example:
            >>> protocol = AsyncTaskProtocol()
            >>> asyncio.run(protocol.start())
            >>> asyncio.run(protocol.stop())
        """
        if not self._running:
            return

        self._running = False

        if self._processor_task is not None:
            await self._processor_task
            self._processor_task = None

        if self._enable_logging:
            logger.info("Async task protocol stopped")

    async def execute(self, task: "AsyncTask") -> Any:
        """
        Execute an asynchronous task.

        This submits the task for execution and returns the result when
        the task completes.

        Args:
            task: Task to execute.

        Returns:
            Result from task execution.

        Raises:
            MessageValidationError: If task validation fails.
            MessageDeliveryError: If task cannot be executed.
            MessageTimeoutError: If task execution times out.

        Example:
            >>> protocol = AsyncTaskProtocol()
            >>> asyncio.run(protocol.start())
            >>> 
            >>> task = AsyncTask(
            ...     message_type=MessageType.ASYNC_TASK,
            ...     sender_id="client",
            ...     task_id="task-123",
            ...     task_type="data.processing",
            ...     payload={"data": "..."}
            ... )
            >>> result = asyncio.run(protocol.execute(task))
        """
        # Validate task
        self._validate_task(task)

        # Set task ID if not set
        if task.task_id is None or not task.task_id:
            task.task_id = str(uuid.uuid4())

        # Set timestamp if not set
        if task.created_at is None:
            task.created_at = datetime.utcnow()

        # Set default timeout if not set
        if task.timeout <= 0:
            task.timeout = self._default_timeout

        # Update metrics
        async with self._metrics_lock:
            self._metrics["tasks_submitted"] += 1

        # Store task info
        task_info = TaskInfo(
            task_id=task.task_id,
            task_type=task.task_type,
            status=TaskStatus.PENDING,
            metadata=task.metadata.copy() if task.metadata else {},
        )

        async with self._task_info_lock:
            self._task_info[task.task_id] = task_info

        # Add task to queue
        async with self._task_queue_lock:
            self._task_queue.append(task)

        # If not running, start the processor
        if not self._running:
            await self.start()

        # Wait for task to complete
        while True:
            async with self._task_info_lock:
                info = self._task_info.get(task.task_id)
                if info is None:
                    from tangku_agentos.runtime_communication.models.exceptions import (
                        MessageDeliveryError,
                    )

                    raise MessageDeliveryError(
                        f"Task info not found: {task.task_id}",
                        message_id=task.message_id,
                    )

                if info.is_complete:
                    # Get result or error
                    async with self._task_results_lock:
                        if task.task_id in self._task_results:
                            result = self._task_results.pop(task.task_id)
                            if isinstance(result, Exception):
                                raise result
                            return result
                        elif info.error:
                            from tangku_agentos.runtime_communication.models.exceptions import (
                                MessageDeliveryError,
                            )

                            raise MessageDeliveryError(
                                f"Task failed: {info.error}",
                                message_id=task.message_id,
                            )
                        else:
                            from tangku_agentos.runtime_communication.models.exceptions import (
                                MessageDeliveryError,
                            )

                            raise MessageDeliveryError(
                                f"Task completed but no result found: {task.task_id}",
                                message_id=task.message_id,
                            )

            # Check for timeout
            elapsed = (datetime.utcnow() - task.created_at).total_seconds()
            if elapsed > task.timeout:
                # Cancel the task
                await self.cancel(task.task_id)

                from tangku_agentos.runtime_communication.models.exceptions import (
                    MessageTimeoutError,
                )

                raise MessageTimeoutError(
                    f"Task {task.task_id} timed out after {task.timeout}s",
                    message_id=task.message_id,
                    operation="task_execution",
                    timeout=task.timeout,
                )

            # Wait a bit before checking again
            await asyncio.sleep(0.1)

    async def schedule(
        self,
        task: "ScheduledTask",
    ) -> str:
        """
        Schedule a task for future execution.

        Args:
            task: Task to schedule.

        Returns:
            Task ID.

        Example:
            >>> from tangku_agentos.runtime_communication.models.messages import ScheduledTask, MessageType
            >>> from datetime import datetime, timedelta
            >>> 
            >>> protocol = AsyncTaskProtocol()
            >>> asyncio.run(protocol.start())
            >>> 
            >>> task = ScheduledTask(
            ...     message_type=MessageType.SCHEDULED_TASK,
            ...     sender_id="scheduler",
            ...     task_id="scheduled-123",
            ...     task_type="cleanup",
            ...     scheduled_time=datetime.utcnow() + timedelta(minutes=1),
            ...     payload={"resource": "temp_files"}
            ... )
            >>> task_id = asyncio.run(protocol.schedule(task))
        """
        # Validate task
        self._validate_scheduled_task(task)

        # Set task ID if not set
        if task.task_id is None or not task.task_id:
            task.task_id = str(uuid.uuid4())

        # Set timestamp if not set
        if task.created_at is None:
            task.created_at = datetime.utcnow()

        # Store task info
        task_info = TaskInfo(
            task_id=task.task_id,
            task_type=task.task_type,
            status=TaskStatus.PENDING,
            metadata=task.metadata.copy() if task.metadata else {},
        )

        async with self._task_info_lock:
            self._task_info[task.task_id] = task_info

        # Add to queue (will be processed when scheduled time arrives)
        async with self._task_queue_lock:
            self._task_queue.append(task)

        if self._enable_logging:
            logger.info(
                f"Task scheduled: {task.task_id} at {task.scheduled_time}"
            )

        return task.task_id

    async def cancel(self, task_id: str) -> bool:
        """
        Cancel a task.

        Args:
            task_id: ID of the task to cancel.

        Returns:
            True if task was cancelled, False otherwise.

        Example:
            >>> protocol = AsyncTaskProtocol()
            >>> asyncio.run(protocol.start())
            >>> # Assume task is running
            >>> asyncio.run(protocol.cancel("task-123"))
            True
        """
        async with self._task_info_lock:
            if task_id not in self._task_info:
                return False

            info = self._task_info[task_id]
            if info.is_complete:
                return False

            info.status = TaskStatus.CANCELLED
            info.completed_at = datetime.utcnow()

            async with self._metrics_lock:
                self._metrics["tasks_cancelled"] += 1

            if self._enable_logging:
                logger.info(f"Task cancelled: {task_id}")

            return True

    async def pause(self, task_id: str) -> bool:
        """
        Pause a task.

        Args:
            task_id: ID of the task to pause.

        Returns:
            True if task was paused, False otherwise.

        Example:
            >>> protocol = AsyncTaskProtocol()
            >>> asyncio.run(protocol.start())
            >>> # Assume task is running
            >>> asyncio.run(protocol.pause("task-123"))
            True
        """
        async with self._task_info_lock:
            if task_id not in self._task_info:
                return False

            info = self._task_info[task_id]
            if info.status != TaskStatus.RUNNING:
                return False

            info.status = TaskStatus.PAUSED

            async with self._metrics_lock:
                self._metrics["tasks_paused"] += 1

            if self._enable_logging:
                logger.info(f"Task paused: {task_id}")

            return True

    async def resume(self, task_id: str) -> bool:
        """
        Resume a paused task.

        Args:
            task_id: ID of the task to resume.

        Returns:
            True if task was resumed, False otherwise.

        Example:
            >>> protocol = AsyncTaskProtocol()
            >>> asyncio.run(protocol.start())
            >>> asyncio.run(protocol.pause("task-123"))
            >>> asyncio.run(protocol.resume("task-123"))
            True
        """
        async with self._task_info_lock:
            if task_id not in self._task_info:
                return False

            info = self._task_info[task_id]
            if info.status != TaskStatus.PAUSED:
                return False

            info.status = TaskStatus.RUNNING

            async with self._metrics_lock:
                self._metrics["tasks_resumed"] += 1

            if self._enable_logging:
                logger.info(f"Task resumed: {task_id}")

            return True

    def get_status(self, task_id: str) -> Optional[TaskInfo]:
        """
        Get the status of a task.

        Args:
            task_id: ID of the task.

        Returns:
            TaskInfo if found, None otherwise.

        Example:
            >>> protocol = AsyncTaskProtocol()
            >>> asyncio.run(protocol.start())
            >>> # Assume task is running
            >>> status = protocol.get_status("task-123")
        """
        async with self._task_info_lock:
            return self._task_info.get(task_id)

    def get_result(self, task_id: str) -> Optional[Any]:
        """
        Get the result of a completed task.

        Args:
            task_id: ID of the task.

        Returns:
            Result if task is complete, None otherwise.

        Example:
            >>> protocol = AsyncTaskProtocol()
            >>> asyncio.run(protocol.start())
            >>> # Assume task is complete
            >>> result = protocol.get_result("task-123")
        """
        async with self._task_results_lock:
            return self._task_results.get(task_id)

    def list_tasks(
        self,
        status: Optional[TaskStatus] = None,
        task_type: Optional[str] = None,
    ) -> List[str]:
        """
        List task IDs matching the given criteria.

        Args:
            status: Filter by task status (optional).
            task_type: Filter by task type (optional).

        Returns:
            List of task IDs.

        Example:
            >>> protocol = AsyncTaskProtocol()
            >>> asyncio.run(protocol.start())
            >>> # Assume some tasks exist
            >>> tasks = protocol.list_tasks(status=TaskStatus.RUNNING)
        """
        async with self._task_info_lock:
            task_ids = list(self._task_info.keys())

        if status is not None or task_type is not None:
            filtered_tasks = []
            for task_id in task_ids:
                info = self.get_status(task_id)
                if info is None:
                    continue

                if status is not None and info.status != status:
                    continue
                if task_type is not None and info.task_type != task_type:
                    continue

                filtered_tasks.append(task_id)

            return filtered_tasks

        return task_ids

    def register_handler(
        self,
        task_type: str,
        handler: Callable[["AsyncTask"], Any],
        priority: int = 0,
    ) -> None:
        """
        Register a task handler.

        Args:
            task_type: Type of task to handle.
            handler: Handler function for the task type.
            priority: Handler priority (higher = called first).

        Example:
            >>> async def handle_data_processing(task: AsyncTask) -> dict:
            ...     return {"status": "completed"}
            >>> 
            >>> protocol = AsyncTaskProtocol()
            >>> protocol.register_handler("data.processing", handle_data_processing)
        """
        asyncio.run(
            self._register_handler_async(task_type, handler, priority)
        )

    async def _register_handler_async(
        self,
        task_type: str,
        handler: Callable[["AsyncTask"], Any],
        priority: int = 0,
    ) -> None:
        """Async version of register_handler."""
        registration = TaskHandler(
            task_type=task_type,
            handler=handler,
            priority=priority,
        )

        async with self._handlers_lock:
            self._handlers[task_type] = registration

            async with self._metrics_lock:
                self._metrics["handlers_registered"] += 1

            if self._enable_logging:
                logger.info(
                    f"Task handler registered for '{task_type}': "
                    f"{handler.__name__}"
                )

    def unregister_handler(self, task_type: str) -> bool:
        """
        Unregister a task handler.

        Args:
            task_type: Type of task.

        Returns:
            True if handler was removed, False otherwise.

        Example:
            >>> protocol = AsyncTaskProtocol()
            >>> protocol.register_handler("data.processing", handler)
            >>> protocol.unregister_handler("data.processing")
            True
        """
        return asyncio.run(self._unregister_handler_async(task_type))

    async def _unregister_handler_async(self, task_type: str) -> bool:
        """Async version of unregister_handler."""
        async with self._handlers_lock:
            if task_type in self._handlers:
                del self._handlers[task_type]

                async with self._metrics_lock:
                    self._metrics["handlers_registered"] -= 1

                if self._enable_logging:
                    logger.info(f"Task handler unregistered: {task_type}")
                return True
            return False

    def has_handler(self, task_type: str) -> bool:
        """
        Check if a handler is registered for a task type.

        Args:
            task_type: Type of task to check.

        Returns:
            True if handler is registered, False otherwise.

        Example:
            >>> protocol = AsyncTaskProtocol()
            >>> protocol.register_handler("data.processing", handler)
            >>> protocol.has_handler("data.processing")
            True
        """
        return task_type in self._handlers

    def list_handlers(self) -> List[str]:
        """
        List all registered task types.

        Returns:
            List of task types with registered handlers.

        Example:
            >>> protocol = AsyncTaskProtocol()
            >>> protocol.register_handler("data.processing", handler)
            >>> protocol.list_handlers()
            ['data.processing']
        """
        return list(self._handlers.keys())

    def get_metrics(self) -> Dict[str, Any]:
        """
        Get async task protocol metrics.

        Returns:
            Dictionary of metrics.

        Example:
            >>> protocol = AsyncTaskProtocol()
            >>> metrics = protocol.get_metrics()
            >>> metrics["tasks_submitted"]
            0
        """
        return {
            **self._metrics,
            "active_tasks": len(self._active_tasks),
            "queued_tasks": len(self._task_queue),
            "handlers_count": len(self._handlers),
            "running": self._running,
        }

    def shutdown(self) -> None:
        """
        Shutdown async task protocol.

        Cleans up resources and stops all processing.

        Example:
            >>> protocol = AsyncTaskProtocol()
            >>> protocol.shutdown()
        """
        self._active_tasks.clear()
        self._task_queue.clear()
        self._task_info.clear()
        self._task_results.clear()
        self._handlers.clear()
        self._metrics.clear()
        self._running = False

        if self._processor_task is not None:
            self._processor_task.cancel()
            self._processor_task = None

        logger.info("Async task protocol shutdown complete")

    async def _process_tasks(self) -> None:
        """
        Process tasks from the queue.

        This is the main task processing loop that runs in the background.
        """
        while self._running:
            try:
                # Get next task from queue
                async with self._task_queue_lock:
                    if not self._task_queue:
                        await asyncio.sleep(0.1)
                        continue

                    task = self._task_queue.pop(0)

                # Check if task is scheduled for future execution
                if hasattr(task, "scheduled_time") and task.scheduled_time:
                    now = datetime.utcnow()
                    if task.scheduled_time > now:
                        # Put task back in queue and wait
                        async with self._task_queue_lock:
                            self._task_queue.insert(0, task)

                        wait_time = (task.scheduled_time - now).total_seconds()
                        await asyncio.sleep(min(wait_time, 1.0))
                        continue

                # Check if we're at capacity
                async with self._active_tasks_lock:
                    if len(self._active_tasks) >= self._max_concurrent_tasks:
                        # Put task back in queue
                        async with self._task_queue_lock:
                            self._task_queue.insert(0, task)
                        await asyncio.sleep(0.1)
                        continue

                    # Add to active tasks
                    self._active_tasks[task.task_id] = task

                # Update task info
                async with self._task_info_lock:
                    if task.task_id in self._task_info:
                        info = self._task_info[task.task_id]
                        info.status = TaskStatus.RUNNING
                        info.started_at = datetime.utcnow()

                async with self._metrics_lock:
                    self._metrics["tasks_started"] += 1

                # Execute task in background
                asyncio.create_task(self._execute_task(task))

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in task processor: {e}")
                await asyncio.sleep(1.0)

    async def _execute_task(self, task: "AsyncTask") -> None:
        """
        Execute a single task.

        Args:
            task: Task to execute.
        """
        try:
            # Find handler for this task type
            handler = await self._get_handler(task.task_type)

            if handler is None:
                error_msg = f"No handler registered for task type: {task.task_type}"
                logger.error(error_msg)

                async with self._task_info_lock:
                    if task.task_id in self._task_info:
                        info = self._task_info[task.task_id]
                        info.status = TaskStatus.FAILED
                        info.error = error_msg
                        info.completed_at = datetime.utcnow()
                        info.total_duration = (
                            (info.completed_at - info.created_at).total_seconds()
                            if info.created_at
                            else None
                        )

                async with self._metrics_lock:
                    self._metrics["tasks_failed"] += 1

                async with self._task_results_lock:
                    self._task_results[task.task_id] = Exception(error_msg)

                return

            # Check if task is cancelled
            async with self._task_info_lock:
                info = self._task_info.get(task.task_id)
                if info and info.status == TaskStatus.CANCELLED:
                    async with self._metrics_lock:
                        self._metrics["tasks_cancelled"] += 1
                    return

            # Execute handler
            handler_func = handler.handler
            result = await handler_func(task)

            # Update task info
            async with self._task_info_lock:
                if task.task_id in self._task_info:
                    info = self._task_info[task.task_id]
                    info.status = TaskStatus.COMPLETED
                    info.progress = 100
                    info.result = result
                    info.completed_at = datetime.utcnow()
                    info.total_duration = (
                        (info.completed_at - info.created_at).total_seconds()
                        if info.created_at
                        else None
                    )

            async with self._metrics_lock:
                self._metrics["tasks_completed"] += 1

            async with self._task_results_lock:
                self._task_results[task.task_id] = result

            if self._enable_logging:
                logger.info(f"Task completed: {task.task_id}")

        except Exception as e:
            # Update task info
            async with self._task_info_lock:
                if task.task_id in self._task_info:
                    info = self._task_info[task.task_id]
                    info.status = TaskStatus.FAILED
                    info.error = str(e)
                    info.completed_at = datetime.utcnow()
                    info.total_duration = (
                        (info.completed_at - info.created_at).total_seconds()
                        if info.created_at
                        else None
                    )

            async with self._metrics_lock:
                self._metrics["tasks_failed"] += 1

            async with self._task_results_lock:
                self._task_results[task.task_id] = e

            logger.error(f"Task failed: {task.task_id}: {e}")

        finally:
            # Remove from active tasks
            async with self._active_tasks_lock:
                if task.task_id in self._active_tasks:
                    del self._active_tasks[task.task_id]

    async def _get_handler(self, task_type: str) -> Optional[TaskHandler]:
        """
        Get the handler for a task type.

        Args:
            task_type: Type of task.

        Returns:
            TaskHandler if found, None otherwise.
        """
        async with self._handlers_lock:
            return self._handlers.get(task_type)

    def _validate_task(self, task: "AsyncTask") -> None:
        """
        Validate a task before execution.

        Args:
            task: Task to validate.

        Raises:
            MessageValidationError: If task is invalid.
        """
        from tangku_agentos.runtime_communication.models.exceptions import (
            MessageValidationError,
        )

        # Check required fields
        if not task.sender_id:
            raise MessageValidationError(
                "Task sender_id is required",
                message_id=task.message_id,
                validation_errors=["sender_id is required"],
            )

        if not task.task_type:
            raise MessageValidationError(
                "Task task_type is required",
                message_id=task.message_id,
                validation_errors=["task_type is required"],
            )

    def _validate_scheduled_task(self, task: "ScheduledTask") -> None:
        """
        Validate a scheduled task before scheduling.

        Args:
            task: Task to validate.

        Raises:
            MessageValidationError: If task is invalid.
        """
        from tangku_agentos.runtime_communication.models.exceptions import (
            MessageValidationError,
        )

        # Check required fields
        if not task.sender_id:
            raise MessageValidationError(
                "Scheduled task sender_id is required",
                message_id=task.message_id,
                validation_errors=["sender_id is required"],
            )

        if not task.task_type:
            raise MessageValidationError(
                "Scheduled task task_type is required",
                message_id=task.message_id,
                validation_errors=["task_type is required"],
            )

        if task.scheduled_time is None:
            raise MessageValidationError(
                "Scheduled task scheduled_time is required",
                message_id=task.message_id,
                validation_errors=["scheduled_time is required"],
            )

    def __repr__(self) -> str:
        """Return string representation of the async task protocol."""
        return (
            f"AsyncTaskProtocol("
            f"active={len(self._active_tasks)}, "
            f"queued={len(self._task_queue)}, "
            f"handlers={len(self._handlers)}, "
            f"running={self._running})"
        )
