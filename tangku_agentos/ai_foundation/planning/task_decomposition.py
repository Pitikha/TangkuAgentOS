"""
Task Decomposition for TangkuAgentOS AI Foundation Framework.

Decomposes complex tasks into smaller, manageable subtasks.
"""
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
import logging
from ..reasoning.reasoning_engine import ReasoningEngine

logger = logging.getLogger(__name__)


@dataclass
class DecompositionResult:
    """Result of a task decomposition operation."""
    task: str
    subtasks: List[str]
    dependencies: Dict[str, List[str]]
    metadata: Dict[str, Any] = field(default_factory=dict)


class TaskDecomposer:
    """Decomposes tasks into subtasks for TangkuAgentOS.

    This class provides methods for breaking down complex tasks into
    smaller, actionable subtasks with dependencies.
    """

    def __init__(self, reasoning_engine: ReasoningEngine):
        """Initialize the TaskDecomposer.

        Args:
            reasoning_engine: The ReasoningEngine instance to use for decomposition.
        """
        self._reasoning_engine = reasoning_engine
        logger.info("TaskDecomposer initialized.")

    async def decompose(
        self,
        task: str,
        max_subtasks: int = 10,
        **kwargs: Any,
    ) -> DecompositionResult:
        """Decompose a task into subtasks.

        Args:
            task: The task to decompose.
            max_subtasks: Maximum number of subtasks to generate.
            **kwargs: Additional arguments for the reasoning engine.

        Returns:
            DecompositionResult containing the subtasks and dependencies.
        """
        reasoning_result = await self._reasoning_engine.decompose_task(task, **kwargs)
        subtasks = reasoning_result.output if isinstance(reasoning_result.output, list) else []
        dependencies = self._infer_dependencies(subtasks)
        logger.info(f"Decomposed task into {len(subtasks)} subtasks.")
        return DecompositionResult(
            task=task,
            subtasks=subtasks,
            dependencies=dependencies,
            metadata={"confidence": reasoning_result.confidence},
        )

    def _infer_dependencies(self, subtasks: List[str]) -> Dict[str, List[str]]:
        """Infer dependencies between subtasks.

        Args:
            subtasks: List of subtasks.

        Returns:
            Dictionary mapping subtask indices to their dependencies.
        """
        dependencies = {}
        for i, subtask in enumerate(subtasks):
            # Simple heuristic: Assume subtasks depend on the previous one
            if i > 0:
                dependencies[f"task_{i}"] = [f"task_{i-1}"]
            else:
                dependencies[f"task_{i}"] = []
        return dependencies

    async def decompose_with_context(
        self,
        task: str,
        context: Dict[str, Any],
        **kwargs: Any,
    ) -> DecompositionResult:
        """Decompose a task into subtasks with additional context.

        Args:
            task: The task to decompose.
            context: Additional context for decomposition.
            **kwargs: Additional arguments for the reasoning engine.

        Returns:
            DecompositionResult containing the subtasks and dependencies.
        """
        # Enhance the task with context
        enhanced_task = f"Task: {task}\nContext: {context}"
        return await self.decompose(enhanced_task, **kwargs)
