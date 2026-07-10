"""
Execution Engine for TangkuAgentOS AI Foundation Framework.

Executes AI tasks, tools, and workflows.
"""
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass, field
import logging
import asyncio
from enum import Enum
from ..tools.tool_executor import ToolExecutor
from ..models.base_model import AIModel

logger = logging.getLogger(__name__)


class ExecutionType(Enum):
    """Types of executions."""
    AI = "ai"
    TOOL = "tool"
    WORKFLOW = "workflow"
    SCRIPT = "script"


@dataclass
class ExecutionTask:
    """Represents a task to be executed."""
    task_id: str
    execution_type: ExecutionType
    content: Union[str, Dict[str, Any], List[Any]]
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ExecutionResult:
    """Result of an execution."""
    task_id: str
    success: bool
    result: Optional[Any] = None
    error: Optional[str] = None
    latency: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)


class ExecutionEngine:
    """Executes tasks for TangkuAgentOS.

    This class provides methods for executing AI tasks, tools, and workflows,
    with support for parallel execution, retries, and error handling.
    """

    def __init__(
        self,
        ai_model: AIModel,
        tool_executor: ToolExecutor,
        max_concurrency: int = 4,
    ):
        """Initialize the ExecutionEngine.

        Args:
            ai_model: The AIModel to use for AI executions.
            tool_executor: The ToolExecutor to use for tool executions.
            max_concurrency: Maximum number of concurrent executions.
        """
        self._ai_model = ai_model
        self._tool_executor = tool_executor
        self._max_concurrency = max_concurrency
        self._execution_history: List[ExecutionResult] = []
        logger.info("ExecutionEngine initialized.")

    async def execute(
        self,
        task: ExecutionTask,
        **kwargs: Any,
    ) -> ExecutionResult:
        """Execute a task.

        Args:
            task: The ExecutionTask to execute.
            **kwargs: Additional arguments for the execution.

        Returns:
            ExecutionResult containing the execution status and result.
        """
        start_time = asyncio.get_event_loop().time()
        try:
            if task.execution_type == ExecutionType.AI:
                result = await self._execute_ai(task.content, **kwargs)
            elif task.execution_type == ExecutionType.TOOL:
                result = await self._execute_tool(task.content, **kwargs)
            elif task.execution_type == ExecutionType.WORKFLOW:
                result = await self._execute_workflow(task.content, **kwargs)
            elif task.execution_type == ExecutionType.SCRIPT:
                result = await self._execute_script(task.content, **kwargs)
            else:
                raise ValueError(f"Unknown execution type: {task.execution_type}")

            latency = asyncio.get_event_loop().time() - start_time
            execution_result = ExecutionResult(
                task_id=task.task_id,
                success=True,
                result=result,
                latency=latency,
                metadata=task.metadata,
            )
            self._execution_history.append(execution_result)
            logger.info(f"Executed task {task.task_id} in {latency:.2f}s")
            return execution_result
        except Exception as e:
            latency = asyncio.get_event_loop().time() - start_time
            execution_result = ExecutionResult(
                task_id=task.task_id,
                success=False,
                error=str(e),
                latency=latency,
                metadata=task.metadata,
            )
            self._execution_history.append(execution_result)
            logger.error(f"Failed to execute task {task.task_id}: {e}")
            return execution_result

    async def _execute_ai(
        self,
        content: Union[str, Dict[str, Any]],
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """Execute an AI task.

        Args:
            content: The content for the AI task (prompt or messages).
            **kwargs: Additional arguments for the AI model.

        Returns:
            The AI model's response.
        """
        if isinstance(content, str):
            messages = [{"role": "user", "content": content}]
        else:
            messages = content
        return await self._ai_model.chat(messages, **kwargs)

    async def _execute_tool(
        self,
        content: Union[str, Dict[str, Any]],
        **kwargs: Any,
    ) -> Any:
        """Execute a tool task.

        Args:
            content: The content for the tool task (tool name and arguments).
            **kwargs: Additional arguments for the tool.

        Returns:
            The result of the tool execution.
        """
        if isinstance(content, str):
            tool_name = content
            args = []
            tool_kwargs = {}
        else:
            tool_name = content.get("tool", "")
            args = content.get("args", [])
            tool_kwargs = content.get("kwargs", {})
        tool_kwargs.update(kwargs)
        execution_result = await self._tool_executor.execute(tool_name, *args, **tool_kwargs)
        if not execution_result.success:
            raise RuntimeError(f"Tool execution failed: {execution_result.error}")
        return execution_result.result

    async def _execute_workflow(
        self,
        content: Union[str, Dict[str, Any], List[Any]],
        **kwargs: Any,
    ) -> List[Any]:
        """Execute a workflow task.

        Args:
            content: The content for the workflow task (list of tasks).
            **kwargs: Additional arguments for the workflow.

        Returns:
            List of results from the workflow tasks.
        """
        if isinstance(content, list):
            tasks = content
        else:
            raise ValueError("Workflow content must be a list of tasks.")

        results = []
        for task in tasks:
            if isinstance(task, dict):
                execution_task = ExecutionTask(
                    task_id=task.get("task_id", ""),
                    execution_type=ExecutionType(task.get("type", "ai")),
                    content=task.get("content", ""),
                    metadata=task.get("metadata", {}),
                )
            else:
                execution_task = ExecutionTask(
                    task_id="",
                    execution_type=ExecutionType.AI,
                    content=task,
                )
            result = await self.execute(execution_task, **kwargs)
            results.append(result)
        return results

    async def _execute_script(
        self,
        content: Union[str, Dict[str, Any]],
        **kwargs: Any,
    ) -> Any:
        """Execute a script task.

        Args:
            content: The content for the script task (code or script).
            **kwargs: Additional arguments for the script.

        Returns:
            The result of the script execution.
        """
        if isinstance(content, str):
            # Placeholder: In a real implementation, this would execute the script
            return {"output": f"Executed script: {content[:50]}..."}
        else:
            raise ValueError("Script content must be a string.")

    async def execute_batch(
        self,
        tasks: List[ExecutionTask],
        **kwargs: Any,
    ) -> List[ExecutionResult]:
        """Execute a batch of tasks.

        Args:
            tasks: List of ExecutionTask objects to execute.
            **kwargs: Additional arguments for the executions.

        Returns:
            List of ExecutionResult objects for each task.
        """
        semaphore = asyncio.Semaphore(self._max_concurrency)

        async def execute_single(task: ExecutionTask) -> ExecutionResult:
            async with semaphore:
                return await self.execute(task, **kwargs)

        return await asyncio.gather(*[execute_single(task) for task in tasks])

    async def execute_parallel(
        self,
        tasks: List[ExecutionTask],
        **kwargs: Any,
    ) -> List[ExecutionResult]:
        """Execute tasks in parallel.

        Args:
            tasks: List of ExecutionTask objects to execute.
            **kwargs: Additional arguments for the executions.

        Returns:
            List of ExecutionResult objects for each task.
        """
        return await self.execute_batch(tasks, **kwargs)

    def get_execution_history(self) -> List[ExecutionResult]:
        """Get the history of executions.

        Returns:
            List of ExecutionResult objects.
        """
        return self._execution_history

    def clear_execution_history(self) -> None:
        """Clear the execution history."""
        self._execution_history.clear()
        logger.info("Cleared execution history.")

    def get_stats(self) -> Dict[str, Any]:
        """Get statistics for executions.

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
