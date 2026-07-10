"""
Reasoning Validation for TangkuAgentOS AI Foundation Framework.

Validates reasoning results for correctness, consistency, and completeness.
"""
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
import logging
from .reasoning_engine import ReasoningResult, ReasoningTask

logger = logging.getLogger(__name__)


@dataclass
class ValidationResult:
    """Result of a reasoning validation operation."""
    is_valid: bool
    reasoning_result: ReasoningResult
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


class ReasoningValidator:
    """Validates reasoning results for TangkuAgentOS.

    This class provides methods for validating reasoning results to ensure
    they meet quality, consistency, and completeness standards.
    """

    def __init__(self):
        """Initialize the ReasoningValidator."""
        self._validators = {
            ReasoningTask.PLANNING: self._validate_plan,
            ReasoningTask.REFLECTION: self._validate_reflection,
            ReasoningTask.VERIFICATION: self._validate_verification,
            ReasoningTask.TASK_DECOMPOSITION: self._validate_task_decomposition,
        }
        logger.info("ReasoningValidator initialized.")

    async def validate(self, reasoning_result: ReasoningResult) -> ValidationResult:
        """Validate a reasoning result.

        Args:
            reasoning_result: The reasoning result to validate.

        Returns:
            ValidationResult containing validation status and details.
        """
        validator = self._validators.get(reasoning_result.task)
        if validator:
            return await validator(reasoning_result)
        return ValidationResult(
            is_valid=False,
            reasoning_result=reasoning_result,
            errors=[f"No validator for task: {reasoning_result.task}"],
        )

    async def _validate_plan(self, reasoning_result: ReasoningResult) -> ValidationResult:
        """Validate a planning reasoning result."""
        errors = []
        warnings = []

        if not reasoning_result.output:
            errors.append("Plan output is empty.")
        elif not isinstance(reasoning_result.output, dict):
            errors.append("Plan output is not a dictionary.")
        elif "plan" not in reasoning_result.output:
            errors.append("Plan output does not contain a 'plan' key.")
        elif not reasoning_result.output["plan"]:
            warnings.append("Plan is empty.")

        return ValidationResult(
            is_valid=len(errors) == 0,
            reasoning_result=reasoning_result,
            errors=errors,
            warnings=warnings,
        )

    async def _validate_reflection(self, reasoning_result: ReasoningResult) -> ValidationResult:
        """Validate a reflection reasoning result."""
        errors = []
        warnings = []

        if not reasoning_result.output:
            errors.append("Reflection output is empty.")
        elif not isinstance(reasoning_result.output, dict):
            errors.append("Reflection output is not a dictionary.")

        return ValidationResult(
            is_valid=len(errors) == 0,
            reasoning_result=reasoning_result,
            errors=errors,
            warnings=warnings,
        )

    async def _validate_verification(self, reasoning_result: ReasoningResult) -> ValidationResult:
        """Validate a verification reasoning result."""
        errors = []
        warnings = []

        if not reasoning_result.output:
            errors.append("Verification output is empty.")
        elif not isinstance(reasoning_result.output, dict):
            errors.append("Verification output is not a dictionary.")
        elif "verdict" not in reasoning_result.output:
            errors.append("Verification output does not contain a 'verdict' key.")
        elif "confidence" not in reasoning_result.output:
            warnings.append("Verification output does not contain a 'confidence' key.")

        return ValidationResult(
            is_valid=len(errors) == 0,
            reasoning_result=reasoning_result,
            errors=errors,
            warnings=warnings,
        )

    async def _validate_task_decomposition(self, reasoning_result: ReasoningResult) -> ValidationResult:
        """Validate a task decomposition reasoning result."""
        errors = []
        warnings = []

        if not reasoning_result.output:
            errors.append("Task decomposition output is empty.")
        elif not isinstance(reasoning_result.output, list):
            errors.append("Task decomposition output is not a list.")
        elif len(reasoning_result.output) == 0:
            warnings.append("Task decomposition is empty.")

        return ValidationResult(
            is_valid=len(errors) == 0,
            reasoning_result=reasoning_result,
            errors=errors,
            warnings=warnings,
        )

    def add_validator(self, task: ReasoningTask, validator: Any) -> None:
        """Add a custom validator for a reasoning task.

        Args:
            task: The reasoning task to validate.
            validator: The validator function.
        """
        self._validators[task] = validator
        logger.info(f"Added validator for task: {task.value}")
