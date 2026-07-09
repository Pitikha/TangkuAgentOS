"""
Conversation Summarization for TangkuAgentOS AI Foundation Framework.

This module handles summarization of conversations.
"""

from typing import Any, Optional, Dict, List, UUID
from dataclasses import dataclass, field
from datetime import datetime
from ..models.base_model import AIModel


@dataclass
class ConversationSummary:
    """Represents a summary of a conversation."""
    conversation_id: UUID
    summary: str
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)


class ConversationSummarizer:
    """Handles summarization of conversations for TangkuAgentOS."""

    def __init__(self, model: AIModel):
        self._model = model

    async def summarize(
        self,
        conversation_id: UUID,
        messages: List[Dict[str, Any]],
        max_tokens: int = 500,
    ) -> ConversationSummary:
        """Generate a summary of a conversation."""
        prompt = f"Summarize the following conversation:\n\n{messages}\n\nProvide a concise summary."
        response = await self._model.generate(prompt, max_tokens=max_tokens)
        return ConversationSummary(
            conversation_id=conversation_id,
            summary=response,
        )

    async def update_summary(
        self,
        summary: ConversationSummary,
        new_messages: List[Dict[str, Any]],
    ) -> ConversationSummary:
        """Update a conversation summary with new messages."""
        prompt = f"Update the following summary with new messages:\n\nSummary: {summary.summary}\n\nNew Messages: {new_messages}\n\nProvide an updated summary."
        response = await self._model.generate(prompt, max_tokens=500)
        summary.summary = response
        summary.updated_at = datetime.utcnow()
        return summary
