"""
Execution Recovery for TangkuAgentOS AI Foundation Framework.

Handles recovery from execution failures.
"""
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
import logging
from .execution_engine import ExecutionEngine, ExecutionTask, ExecutionResult

logger = logging.getLogger(__name__)


@dataclass
class RecoveryStrategy:
    """Represents a recovery strategy."""
    name: str
    max_retries: int = 3
    fallback_tasks: Optional[List[ExecutionTask]] = None
    retry_delay: float = 1.0


@dataclass
class RecoveryResult:
    """Result of a recovery operation."""
    original_task: ExecutionTask
    recovery_strategy: RecoveryStrategy
    execution_results: List[ExecutionResult]
    success: bool
    metadata: Dict[str, Any] = field(default_factory=dict)


class ExecutionRecovery:
    """Handles recovery from execution failures in TangkuAgentOS.

    This class provides methods for recovering from execution failures,
    including retries, fallbacks, and alternative strategies.
    """

    def __init__(
        self,
        execution_engine: ExecutionEngine,
    ):
        """Initialize the ExecutionRecovery.

        Args:
            execution_engine: The ExecutionEngine instance to use.
        """
        self._execution_engine = execution_engine
        self._recovery_strategies: Dict[str, RecoveryStrategy] = {}
        logger.info("ExecutionRecovery initialized.")

    async def recover(
        self,
        task: ExecutionTask,
        strategy_name: str = "default",
        **kwargs: Any,
    ) -> RecoveryResult:
        """Attempt to recover from a failed execution.

        Args:
            task: The ExecutionTask that failed.
            strategy_name: The name of the recovery strategy to use.
            **kwargs: Additional arguments for the recovery.

        Returns:
            RecoveryResult containing the recovery status and results.
        """
        strategy = self._recovery_strategies.get(strategy_name)
        if not strategy:
            strategy = RecoveryStrategy(name="default", max_retries=3)

        execution_results = []
        success = False

        # Try retries
        for attempt in range(strategy.max_retries):
            result = await self._execution_engine.execute(task, **kwargs)
            execution_results.append(result)
            if result.success:
                success = True
                break
            if attempt < strategy.max_retries - 1:
                import asyncio
                await asyncio.sleep(strategy.retry_delay)

        # Try fallback tasks if retries failed
        if not success and strategy.fallback_tasks:
            for fallback_task in strategy.fallback_tasks:
                result = await self._execution_engine.execute(fallback_task, **kwargs)
                execution_results.append(result)
                if result.success:
                    success = True
                    break

        logger.info(f"Recovery for task {task.task_id} {'succeeded' if success else 'failed'}")
        return RecoveryResult(
            original_task=task,
            recovery_strategy=strategy,
            execution_results=execution_results,
            success=success,
            metadata={"attempts": len(execution_results)},
        )

    def add_recovery_strategy(
        self,
        name: str,
        strategy: RecoveryStrategy,
    ) -> None:
        """Add a recovery strategy.

        Args:
            name: The name of the strategy.
            strategy: The RecoveryStrategy to add.
        """
        self._recovery_strategies[name] = strategy
        logger.info(f"Added recovery strategy: {name}")

    def remove_recovery_strategy(self, name: str) -> bool:
        """Remove a recovery strategy.

        Args:
            name: The name of the strategy to remove.

        Returns:
            True if the strategy was removed, False otherwise.
        """
        if name in self._recovery_strategies:
            del self._recovery_strategies[name]
            logger.info(f"Removed recovery strategy: {name}")
            return True
        return False

    def get_recovery_strategy(self, name: str) -> Optional[RecoveryStrategy]:
        """Get a recovery strategy by name.

        Args:
            name: The name of the strategy.

        Returns:
            The RecoveryStrategy if found, otherwise None.
        """
        return self._recovery_strategies.get(name)

    def list_recovery_strategies(self) -> List[str]:
        """List all recovery strategies.

        Returns:
            List of strategy names.
        """
        return list(self._recovery_strategies.keys())

    async def recover_batch(
        self,
        tasks: List[ExecutionTask],
        strategy_name: str = "default",
        **kwargs: Any,
    ) -> List[RecoveryResult]:
        """Attempt to recover from failed executions for a batch of tasks.

        Args:
            tasks: List of ExecutionTask objects that failed.
            strategy_name: The name of the recovery strategy to use.
            **kwargs: Additional arguments for the recovery.

        Returns:
            List of RecoveryResult objects for each task.
        """
        return await asyncio.gather(
            *[self.recover(task, strategy_name, **kwargs) for task in tasks]
        )
