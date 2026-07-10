"""
Reasoning Engine for TangkuAgentOS AI Foundation Framework.

Handles reasoning tasks such as planning, reflection, verification, and decision-making.
"""
from typing import Any, Optional, Dict, List
from dataclasses import dataclass
from enum import Enum
from ..models.base_model import AIModel
import logging
import json

logger = logging.getLogger(__name__)


class ReasoningTask(Enum):
    PLANNING = "planning"
    REFLECTION = "reflection"
    VERIFICATION = "verification"
    CRITIQUE = "critique"
    DECISION_MAKING = "decision_making"
    MULTI_STEP = "multi_step"
    CONSTRAINT_SOLVING = "constraint_solving"
    TASK_DECOMPOSITION = "task_decomposition"
    CONFIDENCE_ESTIMATION = "confidence_estimation"


@dataclass
class ReasoningResult:
    task: ReasoningTask
    input: Any
    output: Any
    confidence: float
    steps: List[Dict[str, Any]]
    metadata: Dict[str, Any]


class ReasoningEngine:
    def __init__(self, model: AIModel):
        self._model = model
        logger.info("ReasoningEngine initialized.")

    async def plan(self, goal: str, constraints: Optional[List[str]] = None, **kwargs: Any) -> ReasoningResult:
        prompt = f"Create a step-by-step plan to achieve: {goal}"
        if constraints:
            prompt += f"\nConstraints: {', '.join(constraints)}"
        prompt += "\nRespond in JSON format with a 'plan' array."
        try:
            response = await self._model.chat([{"role": "user", "content": prompt}])
            output = self._extract_json(response)
            steps = output.get("plan", [])
            return ReasoningResult(
                task=ReasoningTask.PLANNING,
                input={"goal": goal, "constraints": constraints},
                output=output,
                confidence=0.9,
                steps=[{"step": i + 1, "action": s} for i, s in enumerate(steps)],
                metadata={"model": self._model.name}
            )
        except Exception as e:
            logger.error(f"Plan error: {e}")
            return ReasoningResult(
                task=ReasoningTask.PLANNING,
                input={"goal": goal},
                output={},
                confidence=0.0,
                steps=[],
                metadata={"error": str(e)}
            )

    async def reflect(self, experience: str, **kwargs: Any) -> ReasoningResult:
        prompt = f"Reflect on: {experience}\nProvide insights in JSON format."
        try:
            response = await self._model.chat([{"role": "user", "content": prompt}])
            output = self._extract_json(response)
            return ReasoningResult(
                task=ReasoningTask.REFLECTION,
                input={"experience": experience},
                output=output,
                confidence=0.85,
                steps=[{"step": 1, "action": "Reflection completed"}],
                metadata={"model": self._model.name}
            )
        except Exception as e:
            return ReasoningResult(
                task=ReasoningTask.REFLECTION,
                input={"experience": experience},
                output={},
                confidence=0.0,
                steps=[],
                metadata={"error": str(e)}
            )

    async def verify(self, statement: str, **kwargs: Any) -> ReasoningResult:
        prompt = f"Verify: {statement}\nRespond with JSON: {{'verdict': true/false, 'confidence': 0.0-1.0}}"
        try:
            response = await self._model.chat([{"role": "user", "content": prompt}])
            output = self._extract_json(response)
            return ReasoningResult(
                task=ReasoningTask.VERIFICATION,
                input={"statement": statement},
                output=output,
                confidence=output.get("confidence", 0.5),
                steps=[{"step": 1, "action": "Verification completed"}],
                metadata={"model": self._model.name}
            )
        except Exception as e:
            return ReasoningResult(
                task=ReasoningTask.VERIFICATION,
                input={"statement": statement},
                output={},
                confidence=0.0,
                steps=[],
                metadata={"error": str(e)}
            )

    async def decompose_task(self, task: str, **kwargs: Any) -> ReasoningResult:
        prompt = f"Decompose task: {task}\nRespond with JSON array of subtasks."
        try:
            response = await self._model.chat([{"role": "user", "content": prompt}])
            output = self._extract_json(response)
            return ReasoningResult(
                task=ReasoningTask.TASK_DECOMPOSITION,
                input={"task": task},
                output=output,
                confidence=0.9,
                steps=[{"step": i + 1, "action": s} for i, s in enumerate(output)],
                metadata={"model": self._model.name}
            )
        except Exception as e:
            return ReasoningResult(
                task=ReasoningTask.TASK_DECOMPOSITION,
                input={"task": task},
                output={},
                confidence=0.0,
                steps=[],
                metadata={"error": str(e)}
            )

    def _extract_json(self, response: Dict[str, Any]) -> Dict[str, Any]:
        content = response.get("choices", [{}])[0].get("message", {}).get("content", "{}")
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            return {}
