"""
Prompt Validator for TangkuAgentOS AI Foundation Framework.

Validates prompts for safety, correctness, and compliance.
"""
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
import logging
import re

logger = logging.getLogger(__name__)


@dataclass
class PromptValidationResult:
    """Result of a prompt validation operation."""
    is_valid: bool
    prompt: str
    message: str
    details: Optional[Dict[str, Any]] = None


class PromptValidator:
    """Validates prompts for TangkuAgentOS.

    This class provides methods for validating prompts to ensure they
    meet safety, correctness, and compliance standards.
    """

    def __init__(self):
        """Initialize the PromptValidator."""
        self._unsafe_patterns = [
            r"ignore\s+previous\s+instructions",
            r"system\s+override",
            r"jailbreak",
            r"prompt\s+injection",
            r"DAN\s+mode",
            r"developer\s+mode",
        ]
        self._max_length = 10000
        logger.info("PromptValidator initialized.")

    def validate(self, prompt: str) -> PromptValidationResult:
        """Validate a prompt.

        Args:
            prompt: The prompt to validate.

        Returns:
            PromptValidationResult indicating whether the prompt is valid.
        """
        # Check for unsafe patterns
        unsafe_result = self.validate_safety(prompt)
        if not unsafe_result.is_valid:
            return unsafe_result

        # Check length
        length_result = self.validate_length(prompt)
        if not length_result.is_valid:
            return length_result

        # Check for empty prompt
        empty_result = self.validate_not_empty(prompt)
        if not empty_result.is_valid:
            return empty_result

        return PromptValidationResult(
            is_valid=True,
            prompt=prompt,
            message="Prompt is valid.",
        )

    def validate_safety(self, prompt: str) -> PromptValidationResult:
        """Validate that the prompt does not contain unsafe patterns.

        Args:
            prompt: The prompt to validate.

        Returns:
            PromptValidationResult indicating whether the prompt is safe.
        """
        prompt_lower = prompt.lower()
        for pattern in self._unsafe_patterns:
            if re.search(pattern, prompt_lower):
                return PromptValidationResult(
                    is_valid=False,
                    prompt=prompt,
                    message=f"Unsafe pattern detected: {pattern}",
                )
        return PromptValidationResult(
            is_valid=True,
            prompt=prompt,
            message="Prompt is safe.",
        )

    def validate_length(self, prompt: str, max_length: Optional[int] = None) -> PromptValidationResult:
        """Validate that the prompt does not exceed a maximum length.

        Args:
            prompt: The prompt to validate.
            max_length: Optional maximum allowed length for the prompt.

        Returns:
            PromptValidationResult indicating whether the prompt length is valid.
        """
        max_length = max_length or self._max_length
        if len(prompt) > max_length:
            return PromptValidationResult(
                is_valid=False,
                prompt=prompt,
                message=f"Prompt exceeds maximum length of {max_length} characters.",
            )
        return PromptValidationResult(
            is_valid=True,
            prompt=prompt,
            message="Prompt length is valid.",
        )

    def validate_not_empty(self, prompt: str) -> PromptValidationResult:
        """Validate that the prompt is not empty.

        Args:
            prompt: The prompt to validate.

        Returns:
            PromptValidationResult indicating whether the prompt is not empty.
        """
        if not prompt or not prompt.strip():
            return PromptValidationResult(
                is_valid=False,
                prompt=prompt,
                message="Prompt is empty.",
            )
        return PromptValidationResult(
            is_valid=True,
            prompt=prompt,
            message="Prompt is not empty.",
        )

    def add_unsafe_pattern(self, pattern: str) -> None:
        """Add an unsafe pattern to check for.

        Args:
            pattern: The regex pattern to add.
        """
        self._unsafe_patterns.append(pattern)
        logger.info(f"Added unsafe pattern: {pattern}")

    def remove_unsafe_pattern(self, pattern: str) -> bool:
        """Remove an unsafe pattern.

        Args:
            pattern: The regex pattern to remove.

        Returns:
            True if the pattern was removed, False otherwise.
        """
        if pattern in self._unsafe_patterns:
            self._unsafe_patterns.remove(pattern)
            logger.info(f"Removed unsafe pattern: {pattern}")
            return True
        return False

    def set_max_length(self, max_length: int) -> None:
        """Set the maximum allowed prompt length.

        Args:
            max_length: The maximum allowed length.
        """
        self._max_length = max_length
        logger.info(f"Set max prompt length to: {max_length}")
