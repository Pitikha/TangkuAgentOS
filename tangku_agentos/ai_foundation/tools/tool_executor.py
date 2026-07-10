"""
Tool Executor for TangkuAgentOS AI Foundation Framework.

Executes tools with validation, error handling, and metrics.
"""
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
import logging
import asyncio
from .tool_registry import ToolRegistry, Tool

logger = logging.getLogger(__name__)


@dataclass
class ExecutionResult:
    """Result of a tool execution."""
    tool_name: str
    success: bool
    result: Optional[Any] = None
    error: Optional[str] = None
    latency: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)


class ToolExecutor:
    """Executes tools for TangkuAgentOS.

    This class provides methods for executing tools with validation,
    error handling, retries, and metrics collection.
    """

    def __init__(
        self,
        tool_registry: ToolRegistry,
        max_retries: int = 3,
    ):
        """Initialize the ToolExecutor.

        Args:
            tool_registry: The ToolRegistry instance to use.
            max_retries: Maximum number of retries for failed executions.
        """
        self._tool_registry = tool_registry
        self._max_retries = max_retries
        self._execution_history: List[ExecutionResult] = []
        logger.info("ToolExecutor initialized.")

    async def execute(
        self,
        tool_name: str,
        *args: Any,
        max_retries: Optional[int] = None,
        **kwargs: Any,
    ) -> ExecutionResult:
        """Execute a tool with retries and error handling.

        Args:
            tool_name: The name of the tool to execute.
            *args: Positional arguments for the tool.
            max_retries: Optional maximum number of retries.
            **kwargs: Keyword arguments for the tool.

        Returns:
            ExecutionResult containing the execution status and result.
        """
        max_retries = max_retries or self._max_retries
        tool = self._tool_registry.get_tool(tool_name)
        if not tool:
            return ExecutionResult(
                tool_name=tool_name,
                success=False,
                error=f"Tool '{tool_name}' not found.",
            )

        for attempt in range(max_retries):
            start_time = asyncio.get_event_loop().time()
            try:
                result = await tool.function(*args, **kwargs)
                latency = asyncio.get_event_loop().time() - start_time
                execution_result = ExecutionResult(
                    tool_name=tool_name,
                    success=True,
                    result=result,
                    latency=latency,
                    metadata={"attempt": attempt + 1},
                )
                self._execution_history.append(execution_result)
                logger.info(f"Tool {tool_name} executed successfully in {latency:.2f}s")
                return execution_result
            except Exception as e:
                latency = asyncio.get_event_loop().time() - start_time
                logger.warning(f"Attempt {attempt + 1} failed for tool {tool_name}: {e}")
                if attempt == max_retries - 1:
                    execution_result = ExecutionResult(
                        tool_name=tool_name,
                        success=False,
                        error=str(e),
                        latency=latency,
                        metadata={"attempts": max_retries},
                    )
                    self._execution_history.append(execution_result)
                    logger.error(f"Tool {tool_name} failed after {max_retries} attempts: {e}")
                    return execution_result

    async def execute_batch(
        self,
        tool_name: str,
        args_list: List[List[Any]],
        kwargs_list: Optional[List[Dict[str, Any]]] = None,
        max_concurrency: int = 4,
    ) -> List[ExecutionResult]:
        """Execute a tool multiple times with different arguments.

        Args:
            tool_name: The name of the tool to execute.
            args_list: List of argument lists for each execution.
            kwargs_list: Optional list of keyword argument dictionaries for each execution.
            max_concurrency: Maximum number of concurrent executions.

        Returns:
            List of ExecutionResult objects for each execution.
        """
        kwargs_list = kwargs_list or [{}] * len(args_list)
        semaphore = asyncio.Semaphore(max_concurrency)

        async def execute_single(args: List[Any], kwargs: Dict[str, Any]) -> ExecutionResult:
            async with semaphore:
                return await self.execute(tool_name, *args, **kwargs)

        tasks = [
            execute_single(args, kwargs)
            for args, kwargs in zip(args_list, kwargs_list)
        ]
        return await asyncio.gather(*tasks)

    async def execute_with_validation(
        self,
        tool_name: str,
        validator: Optional[Callable[[Any], bool]] = None,
        *args: Any,
        **kwargs: Any,
    ) -> ExecutionResult:
        """Execute a tool and validate the result.

        Args:
            tool_name: The name of the tool to execute.
            validator: Optional function to validate the result.
            *args: Positional arguments for the tool.
            **kwargs: Keyword arguments for the tool.

        Returns:
            ExecutionResult containing the execution status and result.
        """
        execution_result = await self.execute(tool_name, *args, **kwargs)
        if not execution_result.success:
            return execution_result

        if validator and not validator(execution_result.result):
            execution_result.success = False
            execution_result.error = "Validation failed"
            logger.warning(f"Validation failed for tool {tool_name}")

        return execution_result

    def get_execution_history(self) -> List[ExecutionResult]:
        """Get the history of tool executions.

        Returns:
            List of ExecutionResult objects.
        """
        return self._execution_history

    def clear_execution_history(self) -> None:
        """Clear the execution history."""
        self._execution_history.clear()
        logger.info("Cleared execution history.")

    def get_stats(self) -> Dict[str, Any]:
        """Get statistics for tool executions.

        Returns:
            Dictionary containing execution statistics.
        """
        total = len(self._execution_history)
        successful = sum(1 for r in self._execution_history if r.success)
        failed = total - successful
        avg_latency = (
            sum(r.latency for r in self._execution_history) / total
            if total > 0 else 0.0
        )
        return {
            "total_executions": total,
            "successful": successful,
            "failed": failed,
            "avg_latency": avg_latency,
        }
