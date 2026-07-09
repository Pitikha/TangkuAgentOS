"""
Conversation Compression for TangkuAgentOS AI Foundation Framework.

This module handles compression of conversations to fit within token budgets.
"""

from typing import Any, Optional, Dict, List, UUID
from dataclasses import dataclass, field
from datetime import datetime
from ..models.base_model import AIModel


@dataclass
class CompressionResult:
    """Result of a conversation compression operation."""
    original_length: int
    compressed_length: int
    compressed_messages: List[Dict[str, Any]]
    removed_messages: List[Dict[str, Any]]


class ConversationCompressor:
    """Handles compression of conversations for TangkuAgentOS."""

    def __init__(self, model: AIModel):
        self._model = model

    def compress_by_length(
        self,
        messages: List[Dict[str, Any]],
        max_tokens: int,
    ) -> CompressionResult:
        """Compress a conversation by keeping the most recent messages."""
        original_length = len(messages)
        if original_length <= max_tokens:
            return CompressionResult(
                original_length=original_length,
                compressed_length=original_length,
                compressed_messages=messages,
                removed_messages=[],
            )
        compressed_messages = messages[-max_tokens:]
        removed_messages = messages[:-max_tokens]
        return CompressionResult(
            original_length=original_length,
            compressed_length=len(compressed_messages),
            compressed_messages=compressed_messages,
            removed_messages=removed_messages,
        )

    async def compress_by_summary(
        self,
        messages: List[Dict[str, Any]],
        max_tokens: int,
    ) -> CompressionResult:
        """Compress a conversation by summarizing older messages."""
        if len(messages) <= max_tokens:
            return CompressionResult(
                original_length=len(messages),
                compressed_length=len(messages),
                compressed_messages=messages,
                removed_messages=[],
            )
        # Summarize the first half of the messages
        half = len(messages) // 2
        summary_prompt = f"Summarize the following messages:\n\n{messages[:half]}\n\nProvide a concise summary."
        summary = await self._model.generate(summary_prompt, max_tokens=200)
        # Replace the first half with the summary
        compressed_messages = [
            {"role": "system", "content": f"Summary of earlier messages: {summary}"}
        ] + messages[half:]
        return CompressionResult(
            original_length=len(messages),
            compressed_length=len(compressed_messages),
            compressed_messages=compressed_messages,
            removed_messages=messages[:half],
        )
