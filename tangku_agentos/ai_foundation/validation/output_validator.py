"""
Output Validator for TangkuAgentOS AI Foundation Framework.

Validates AI model outputs for correctness and safety.
"""
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
import logging
import json

logger = logging.getLogger(__name__)


class ValidationResult(Enum):
    """Result of a validation check."""
    VALID = "valid"
    INVALID = "invalid"
    WARNING = "warning"


@dataclass
class ValidationReport:
    """Report of a validation check."""
    result: ValidationResult
    message: str
    details: Optional[Dict[str, Any]] = None


class OutputValidator:
    """Validates AI model outputs for TangkuAgentOS.

    This class provides methods for validating AI model outputs to ensure
    they meet quality, correctness, and safety standards.
    """

    def __init__(self):
        """Initialize the OutputValidator."""
        self._validators = []
        logger.info("OutputValidator initialized.")

    def add_validator(self, validator: callable) -> None:
        """Add a custom validator.

        Args:
            validator: The validator function.
        """
        self._validators.append(validator)
        logger.info("Added custom output validator.")

    def validate(self, output: Any) -> ValidationReport:
        """Validate an AI model output.

        Args:
            output: The output to validate.

        Returns:
            ValidationReport containing the validation result.
        """
        for validator in self._validators:
            try:
                report = validator(output)
                if report.result == ValidationResult.INVALID:
                    return report
            except Exception as e:
                return ValidationReport(
                    result=ValidationResult.INVALID,
                    message=f"Validation error: {e}",
                )
        return ValidationReport(
            result=ValidationResult.VALID,
            message="Output is valid.",
        )

    @staticmethod
    def validate_json(output: Any) -> ValidationReport:
        """Validate that the output is valid JSON.

        Args:
            output: The output to validate.

        Returns:
            ValidationReport indicating whether the output is valid JSON.
        """
        try:
            if isinstance(output, str):
                json.loads(output)
            elif isinstance(output, dict):
                json.dumps(output)
            return ValidationReport(
                result=ValidationResult.VALID,
                message="Output is valid JSON.",
            )
        except (json.JSONDecodeError, TypeError):
            return ValidationReport(
                result=ValidationResult.INVALID,
                message="Output is not valid JSON.",
            )

    @staticmethod
    def validate_structure(output: Any, schema: Dict[str, Any]) -> ValidationReport:
        """Validate that the output matches a schema.

        Args:
            output: The output to validate.
            schema: The schema to validate against.

        Returns:
            ValidationReport indicating whether the output matches the schema.
        """
        if not isinstance(output, dict):
            return ValidationReport(
                result=ValidationResult.INVALID,
                message="Output is not a dictionary.",
            )
        for key, value in schema.items():
            if key not in output:
                return ValidationReport(
                    result=ValidationResult.INVALID,
                    message=f"Missing required key: {key}",
                )
        return ValidationReport(
            result=ValidationResult.VALID,
            message="Output matches schema.",
        )

    @staticmethod
    def validate_type(output: Any, expected_type: type) -> ValidationReport:
        """Validate that the output is of the expected type.

        Args:
            output: The output to validate.
            expected_type: The expected type of the output.

        Returns:
            ValidationReport indicating whether the output is of the expected type.
        """
        if not isinstance(output, expected_type):
            return ValidationReport(
                result=ValidationResult.INVALID,
                message=f"Output is not of type {expected_type.__name__}.",
            )
        return ValidationReport(
            result=ValidationResult.VALID,
            message=f"Output is of type {expected_type.__name__}.",
        )

    @staticmethod
    def validate_not_empty(output: Any) -> ValidationReport:
        """Validate that the output is not empty.

        Args:
            output: The output to validate.

        Returns:
            ValidationReport indicating whether the output is not empty.
        """
        if output is None:
            return ValidationReport(
                result=ValidationResult.INVALID,
                message="Output is None.",
            )
        if isinstance(output, (str, list, dict)) and not output:
            return ValidationReport(
                result=ValidationResult.INVALID,
                message="Output is empty.",
            )
        return ValidationReport(
            result=ValidationResult.VALID,
            message="Output is not empty.",
        )
