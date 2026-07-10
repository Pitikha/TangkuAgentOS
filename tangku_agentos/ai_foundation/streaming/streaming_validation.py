"""
Streaming Validation for TangkuAgentOS AI Foundation Framework.

Validates streaming responses for correctness and safety.
"""
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
import logging
from .streaming_manager import StreamChunk

logger = logging.getLogger(__name__)


@dataclass
class ValidationResult:
    """Result of a streaming validation operation."""
    is_valid: bool
    chunk: StreamChunk
    message: str
    details: Optional[Dict[str, Any]] = None


class StreamingValidator:
    """Validates streaming responses for TangkuAgentOS.

    This class provides methods for validating streaming responses
    to ensure they meet quality, safety, and correctness standards.
    """

    def __init__(self):
        """Initialize the StreamingValidator."""
        self._validators = []
        logger.info("StreamingValidator initialized.")

    async def validate_chunk(
        self,
        chunk: StreamChunk,
    ) -> ValidationResult:
        """Validate a single streaming chunk.

        Args:
            chunk: The StreamChunk to validate.

        Returns:
            ValidationResult indicating whether the chunk is valid.
        """
        for validator in self._validators:
            try:
                result = await validator(chunk)
                if not result.is_valid:
                    return result
            except Exception as e:
                return ValidationResult(
                    is_valid=False,
                    chunk=chunk,
                    message=f"Validation error: {e}",
                )
        return ValidationResult(
            is_valid=True,
            chunk=chunk,
            message="Chunk validation passed",
        )

    async def validate_stream(
        self,
        chunks: List[StreamChunk],
    ) -> List[ValidationResult]:
        """Validate a list of streaming chunks.

        Args:
            chunks: List of StreamChunk objects to validate.

        Returns:
            List of ValidationResult objects for each chunk.
        """
        return await asyncio.gather(*[self.validate_chunk(chunk) for chunk in chunks])

    def add_validator(self, validator: callable) -> None:
        """Add a custom validator.

        Args:
            validator: The validator function.
        """
        self._validators.append(validator)
        logger.info("Added custom streaming validator.")

    @staticmethod
    async def validate_content(chunk: StreamChunk) -> ValidationResult:
        """Validate that the chunk content is not empty.

        Args:
            chunk: The StreamChunk to validate.

        Returns:
            ValidationResult indicating whether the content is valid.
        """
        if not chunk.content:
            return ValidationResult(
                is_valid=False,
                chunk=chunk,
                message="Chunk content is empty",
            )
        return ValidationResult(
            is_valid=True,
            chunk=chunk,
            message="Content validation passed",
        )

    @staticmethod
    async def validate_safety(chunk: StreamChunk) -> ValidationResult:
        """Validate that the chunk content is safe.

        Args:
            chunk: The StreamChunk to validate.

        Returns:
            ValidationResult indicating whether the content is safe.
        """
        unsafe_patterns = [
            "prompt injection",
            "ignore previous",
            "system override",
            "jailbreak",
        ]
        content_lower = chunk.content.lower()
        for pattern in unsafe_patterns:
            if pattern in content_lower:
                return ValidationResult(
                    is_valid=False,
                    chunk=chunk,
                    message=f"Unsafe content detected: {pattern}",
                )
        return ValidationResult(
            is_valid=True,
            chunk=chunk,
            message="Safety validation passed",
        )

    @staticmethod
    async def validate_length(chunk: StreamChunk, max_length: int = 1000) -> ValidationResult:
        """Validate that the chunk content does not exceed a maximum length.

        Args:
            chunk: The StreamChunk to validate.
            max_length: Maximum allowed length for the chunk content.

        Returns:
            ValidationResult indicating whether the length is valid.
        """
        if len(chunk.content) > max_length:
            return ValidationResult(
                is_valid=False,
                chunk=chunk,
                message=f"Chunk content exceeds maximum length of {max_length}",
            )
        return ValidationResult(
            is_valid=True,
            chunk=chunk,
            message="Length validation passed",
        )
