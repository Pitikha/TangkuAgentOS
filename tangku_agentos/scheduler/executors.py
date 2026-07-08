"""
Execution Backends for Multiple Execution Models

Supports threads, processes, asyncio, and extensible interface for distributed execution.
"""

from typing import Any, Callable, Optional, List
from abc import ABC, abstractmethod
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
from concurrent.futures import Future as ConcurrentFuture
import asyncio
import logging
from datetime import datetime

from tangku_agentos.scheduler.task import Task

logger = logging.getLogger(__name__)


class ExecutorBackend(ABC):
    """Abstract base for execution backends."""

    @abstractmethod
    async def execute(self, task: Task) -> Any:
        """
        Execute task and return result.
        
        Args:
            task: Task to execute
            
        Returns:
            Task result
            
        Raises:
            Exception: If task execution fails
        """
        pass

    @abstractmethod
    def shutdown(self, wait: bool = True) -> None:
        """Shutdown executor."""
        pass


class ThreadExecutor(ExecutorBackend):
    """Execute tasks in thread pool."""

    def __init__(self, max_workers: int = 10):
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.max_workers = max_workers
        self.active_count = 0

    async def execute(self, task: Task) -> Any:
        """Execute task in thread pool."""
        if task.task_func is None:
            raise ValueError(f"Task {task.task_id} has no function")

        loop = asyncio.get_event_loop()
        self.active_count += 1

        try:
            result = await loop.run_in_executor(
                self.executor,
                lambda: task.task_func(*task.args, **task.kwargs),
            )
            return result
        finally:
            self.active_count -= 1

    def shutdown(self, wait: bool = True) -> None:
        """Shutdown thread pool."""
        self.executor.shutdown(wait=wait)
        logger.info("Thread executor shutdown")


class ProcessExecutor(ExecutorBackend):
    """Execute tasks in process pool (for CPU-intensive work)."""

    def __init__(self, max_workers: int = 4):
        self.executor = ProcessPoolExecutor(max_workers=max_workers)
        self.max_workers = max_workers
        self.active_count = 0

    async def execute(self, task: Task) -> Any:
        """Execute task in process pool."""
        if task.task_func is None:
            raise ValueError(f"Task {task.task_id} has no function")

        loop = asyncio.get_event_loop()
        self.active_count += 1

        try:
            result = await loop.run_in_executor(
                self.executor,
                lambda: task.task_func(*task.args, **task.kwargs),
            )
            return result
        finally:
            self.active_count -= 1

    def shutdown(self, wait: bool = True) -> None:
        """Shutdown process pool."""
        self.executor.shutdown(wait=wait)
        logger.info("Process executor shutdown")


class AsyncioExecutor(ExecutorBackend):
    """Execute async tasks directly in asyncio event loop."""

    def __init__(self):
        self.active_count = 0

    async def execute(self, task: Task) -> Any:
        """Execute async task."""
        if task.task_func is None:
            raise ValueError(f"Task {task.task_id} has no function")

        self.active_count += 1

        try:
            # Check if task_func is a coroutine function
            if asyncio.iscoroutinefunction(task.task_func):
                result = await task.task_func(*task.args, **task.kwargs)
            else:
                # Wrap sync function in executor
                loop = asyncio.get_event_loop()
                result = await loop.run_in_executor(
                    None,
                    lambda: task.task_func(*task.args, **task.kwargs),
                )
            return result
        finally:
            self.active_count -= 1

    def shutdown(self, wait: bool = True) -> None:
        """Asyncio executor doesn't need shutdown."""
        logger.info("Asyncio executor shutdown")


class ExecutorFactory:
    """Factory for creating executor backends."""

    _executors = {
        "thread": ThreadExecutor,
        "process": ProcessExecutor,
        "asyncio": AsyncioExecutor,
    }

    @classmethod
    def create(
        cls,
        backend: str = "thread",
        **kwargs
    ) -> ExecutorBackend:
        """
        Create executor backend.

        Args:
            backend: Backend type (thread, process, asyncio)
            **kwargs: Backend-specific arguments

        Returns:
            ExecutorBackend instance

        Raises:
            ValueError: If backend type not found
        """
        executor_class = cls._executors.get(backend)
        if not executor_class:
            raise ValueError(
                f"Unknown executor backend: {backend}. "
                f"Available: {list(cls._executors.keys())}"
            )

        return executor_class(**kwargs)

    @classmethod
    def register(cls, name: str, executor_class: type) -> None:
        """Register custom executor backend."""
        cls._executors[name] = executor_class
        logger.info(f"Registered executor backend: {name}")


class ExecutorPool:
    """
    Pool of executors for managing different execution backends.
    """

    def __init__(self):
        self.executors: dict[str, ExecutorBackend] = {}

    def get_or_create(
        self,
        backend: str = "thread",
        **kwargs
    ) -> ExecutorBackend:
        """Get or create executor for backend."""
        if backend not in self.executors:
            self.executors[backend] = ExecutorFactory.create(backend, **kwargs)
        return self.executors[backend]

    async def execute(self, task: Task) -> Any:
        """Execute task using appropriate backend."""
        backend = task.executor_backend or "thread"
        executor = self.get_or_create(backend)
        return await executor.execute(task)

    def shutdown_all(self, wait: bool = True) -> None:
        """Shutdown all executors."""
        for backend, executor in self.executors.items():
            try:
                executor.shutdown(wait=wait)
            except Exception as e:
                logger.error(f"Error shutting down {backend} executor: {e}")

        self.executors.clear()
        logger.info("All executors shutdown")

    def get_stats(self) -> dict[str, Any]:
        """Get statistics for all executors."""
        stats = {}
        for name, executor in self.executors.items():
            stats[name] = {
                "active_count": getattr(executor, "active_count", 0),
            }
        return stats
