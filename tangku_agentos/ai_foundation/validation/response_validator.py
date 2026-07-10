"""
Response Validator for TangkuAgentOS AI Foundation Framework.

Validates AI model responses for correctness, safety, and compliance.
"""
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
import logging
import json

logger = logging.getLogger(__name__)


@dataclass
class ResponseValidationResult:
    """Result of a response validation operation."""
    is_valid: bool
    response: Dict[str, Any]
    message: str
    details: Optional[Dict[str, Any]] = None


class ResponseValidator:
    """Validates AI model responses for TangkuAgentOS.

    This class provides methods for validating AI model responses to ensure
    they meet quality, correctness, safety, and compliance standards.
    """

    def __init__(self):
        """Initialize the ResponseValidator."""
        self._validators = []
        logger.info("ResponseValidator initialized.")

    def add_validator(self, validator: callable) -> None:
        """Add a custom validator.

        Args:
            validator: The validator function.
        """
        self._validators.append(validator)
        logger.info("Added custom response validator.")

    def validate(self, response: Dict[str, Any]) -> ResponseValidationResult:
        """Validate an AI model response.

        Args:
            response: The response to validate.

        Returns:
            ResponseValidationResult indicating whether the response is valid.
        """
        for validator in self._validators:
            try:
                result = validator(response)
                if not result.is_valid:
                    return result
            except Exception as e:
                return ResponseValidationResult(
                    is_valid=False,
                    response=response,
                    message=f"Validation error: {e}",
                )
        return ResponseValidationResult(
            is_valid=True,
            response=response,
            message="Response is valid.",
        )

    @staticmethod
    def validate_structure(response: Dict[str, Any]) -> ResponseValidationResult:
        """Validate that the response has the expected structure.

        Args:
            response: The response to validate.

        Returns:
            ResponseValidationResult indicating whether the response structure is valid.
        """
        if "choices" not in response:
            return ResponseValidationResult(
                is_valid=False,
                response=response,
                message="Response does not contain 'choices' key.",
            )
        if not isinstance(response["choices"], list):
            return ResponseValidationResult(
                is_valid=False,
                response=response,
                message="Response 'choices' is not a list.",
            )
        if not response["choices"]:
            return ResponseValidationResult(
                is_valid=False,
                response=response,
                message="Response 'choices' is empty.",
            )
        return ResponseValidationResult(
            is_valid=True,
            response=response,
            message="Response structure is valid.",
        )

    @staticmethod
    def validate_content(response: Dict[str, Any]) -> ResponseValidationResult:
        """Validate that the response contains valid content.

        Args:
            response: The response to validate.

        Returns:
            ResponseValidationResult indicating whether the response content is valid.
        """
        choices = response.get("choices", [])
        for choice in choices:
            message = choice.get("message", {})
            content = message.get("content", "")
            if not content:
                return ResponseValidationResult(
                    is_valid=False,
                    response=response,
                    message="Response contains empty content.",
                )
        return ResponseValidationResult(
            is_valid=True,
            response=response,
            message="Response content is valid.",
        )

    @staticmethod
    def validate_safety(response: Dict[str, Any]) -> ResponseValidationResult:
        """Validate that the response does not contain unsafe content.

        Args:
            response: The response to validate.

        Returns:
            ResponseValidationResult indicating whether the response is safe.
        """
        unsafe_patterns = [
            "prompt injection",
            "ignore previous",
            "system override",
            "jailbreak",
        ]
        choices = response.get("choices", [])
        for choice in choices:
            message = choice.get("message", {})
            content = message.get("content", "").lower()
            for pattern in unsafe_patterns:
                if pattern in content:
                    return ResponseValidationResult(
                        is_valid=False,
                        response=response,
                        message=f"Unsafe content detected: {pattern}",
                    )
        return ResponseValidationResult(
            is_valid=True,
            response=response,
            message="Response is safe.",
        )

    @staticmethod
    def validate_json(response: Dict[str, Any]) -> ResponseValidationResult:
        """Validate that the response contains valid JSON.

        Args:
            response: The response to validate.

        Returns:
            ResponseValidationResult indicating whether the response contains valid JSON.
        """
        choices = response.get("choices", [])
        for choice in choices:
            message = choice.get("message", {})
            content = message.get("content", "")
            try:
                if content:
                    json.loads(content)
            except json.JSONDecodeError:
                return ResponseValidationResult(
                    is_valid=False,
                    response=response,
                    message="Response does not contain valid JSON.",
                )
        return ResponseValidationResult(
            is_valid=True,
            response=response,
            message="Response contains valid JSON.",
        )
