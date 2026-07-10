"""
Tool Validation for TangkuAgentOS AI Foundation Framework.

Validates tool inputs, outputs, and permissions.
"""
from typing import Any, Callable, Dict, List, Optional, Union
from dataclasses import dataclass, field
import logging
from enum import Enum

logger = logging.getLogger(__name__)


class ValidationType(Enum):
    """Types of validation."""
    INPUT = "input"
    OUTPUT = "output"
    PERMISSION = "permission"
    SCHEMA = "schema"


@dataclass
class ValidationResult:
    """Result of a validation operation."""
    is_valid: bool
    validation_type: ValidationType
    message: str
    details: Optional[Dict[str, Any]] = None


class ToolValidator:
    """Validates tools for TangkuAgentOS.

    This class provides methods for validating tool inputs, outputs,
    permissions, and schemas to ensure safe and correct tool usage.
    """

    def __init__(self):
        """Initialize the ToolValidator."""
        self._validators: Dict[ValidationType, List[Callable]] = {
            ValidationType.INPUT: [],
            ValidationType.OUTPUT: [],
            ValidationType.PERMISSION: [],
            ValidationType.SCHEMA: [],
        }
        logger.info("ToolValidator initialized.")

    def add_validator(
        self,
        validation_type: ValidationType,
        validator: Callable,
    ) -> None:
        """Add a custom validator.

        Args:
            validation_type: The type of validation.
            validator: The validator function.
        """
        self._validators[validation_type].append(validator)
        logger.info(f"Added validator for {validation_type.value}")

    async def validate_input(
        self,
        tool_name: str,
        args: List[Any],
        kwargs: Dict[str, Any],
    ) -> ValidationResult:
        """Validate tool input arguments.

        Args:
            tool_name: The name of the tool.
            args: Positional arguments for the tool.
            kwargs: Keyword arguments for the tool.

        Returns:
            ValidationResult indicating whether the input is valid.
        """
        for validator in self._validators[ValidationType.INPUT]:
            try:
                result = validator(tool_name, args, kwargs)
                if not result.is_valid:
                    return result
            except Exception as e:
                return ValidationResult(
                    is_valid=False,
                    validation_type=ValidationType.INPUT,
                    message=f"Validation error: {e}",
                )
        return ValidationResult(
            is_valid=True,
            validation_type=ValidationType.INPUT,
            message="Input validation passed",
        )

    async def validate_output(
        self,
        tool_name: str,
        result: Any,
    ) -> ValidationResult:
        """Validate tool output.

        Args:
            tool_name: The name of the tool.
            result: The output of the tool.

        Returns:
            ValidationResult indicating whether the output is valid.
        """
        for validator in self._validators[ValidationType.OUTPUT]:
            try:
                result = validator(tool_name, result)
                if not result.is_valid:
                    return result
            except Exception as e:
                return ValidationResult(
                    is_valid=False,
                    validation_type=ValidationType.OUTPUT,
                    message=f"Validation error: {e}",
                )
        return ValidationResult(
            is_valid=True,
            validation_type=ValidationType.OUTPUT,
            message="Output validation passed",
        )

    async def validate_permission(
        self,
        tool_name: str,
        user_permissions: List[str],
    ) -> ValidationResult:
        """Validate user permissions for a tool.

        Args:
            tool_name: The name of the tool.
            user_permissions: List of permissions the user has.

        Returns:
            ValidationResult indicating whether the user has permission.
        """
        for validator in self._validators[ValidationType.PERMISSION]:
            try:
                result = validator(tool_name, user_permissions)
                if not result.is_valid:
                    return result
            except Exception as e:
                return ValidationResult(
                    is_valid=False,
                    validation_type=ValidationType.PERMISSION,
                    message=f"Permission validation error: {e}",
                )
        return ValidationResult(
            is_valid=True,
            validation_type=ValidationType.PERMISSION,
            message="Permission validation passed",
        )

    async def validate_schema(
        self,
        tool_name: str,
        data: Any,
        schema: Dict[str, Any],
    ) -> ValidationResult:
        """Validate data against a schema.

        Args:
            tool_name: The name of the tool.
            data: The data to validate.
            schema: The schema to validate against.

        Returns:
            ValidationResult indicating whether the data matches the schema.
        """
        for validator in self._validators[ValidationType.SCHEMA]:
            try:
                result = validator(tool_name, data, schema)
                if not result.is_valid:
                    return result
            except Exception as e:
                return ValidationResult(
                    is_valid=False,
                    validation_type=ValidationType.SCHEMA,
                    message=f"Schema validation error: {e}",
                )
        return ValidationResult(
            is_valid=True,
            validation_type=ValidationType.SCHEMA,
            message="Schema validation passed",
        )

    @staticmethod
    def validate_input_types(
        tool_name: str,
        args: List[Any],
        kwargs: Dict[str, Any],
    ) -> ValidationResult:
        """Validate that input arguments have the correct types.

        Args:
            tool_name: The name of the tool.
            args: Positional arguments for the tool.
            kwargs: Keyword arguments for the tool.

        Returns:
            ValidationResult indicating whether the input types are valid.
        """
        # Placeholder: In a real implementation, this would check against expected types
        return ValidationResult(
            is_valid=True,
            validation_type=ValidationType.INPUT,
            message="Input type validation passed",
        )

    @staticmethod
    def validate_output_type(
        tool_name: str,
        result: Any,
    ) -> ValidationResult:
        """Validate that the output has the correct type.

        Args:
            tool_name: The name of the tool.
            result: The output of the tool.

        Returns:
            ValidationResult indicating whether the output type is valid.
        """
        # Placeholder: In a real implementation, this would check against expected types
        return ValidationResult(
            is_valid=True,
            validation_type=ValidationType.OUTPUT,
            message="Output type validation passed",
        )

    @staticmethod
    def validate_permissions(
        tool_name: str,
        user_permissions: List[str],
    ) -> ValidationResult:
        """Validate that the user has the required permissions for the tool.

        Args:
            tool_name: The name of the tool.
            user_permissions: List of permissions the user has.

        Returns:
            ValidationResult indicating whether the user has permission.
        """
        # Placeholder: In a real implementation, this would check against tool permissions
        return ValidationResult(
            is_valid=True,
            validation_type=ValidationType.PERMISSION,
            message="Permission validation passed",
        )
