"""
Conversation Manager for TangkuAgentOS AI Foundation Framework.

This module manages conversation history, branching, summarization, and compression.
"""

from typing import Any, Optional, Dict, List, UUID
from dataclasses import dataclass, field
from datetime import datetime
from ..sessions.session_manager import AISession


@dataclass
class Conversation:
    """Represents a conversation within an AI session."""
    conversation_id: UUID
    session_id: UUID
    messages: List[Dict[str, Any]] = field(default_factory=list)
    summary: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)


class ConversationManager:
    """Manages conversations for TangkuAgentOS."""

    def __init__(self, session_manager: "SessionManager"):
        self._session_manager = session_manager
        self._conversations: Dict[UUID, Conversation] = {}

    def create_conversation(
        self,
        session_id: UUID,
        initial_message: Optional[Dict[str, Any]] = None,
    ) -> Conversation:
        """Create a new conversation for a session."""
        conversation_id = UUID(int=datetime.utcnow().timestamp())
        conversation = Conversation(
            conversation_id=conversation_id,
            session_id=session_id,
        )
        if initial_message:
            conversation.messages.append(initial_message)
        self._conversations[conversation_id] = conversation
        return conversation

    def get_conversation(self, conversation_id: UUID) -> Optional[Conversation]:
        """Retrieve a conversation by its ID."""
        return self._conversations.get(conversation_id)

    def add_message(
        self,
        conversation_id: UUID,
        message: Dict[str, Any],
    ) -> Optional[Conversation]:
        """Add a message to a conversation."""
        conversation = self._conversations.get(conversation_id)
        if conversation:
            conversation.messages.append(message)
            conversation.updated_at = datetime.utcnow()
        return conversation

    def summarize_conversation(
        self,
        conversation_id: UUID,
        model: Any,  # AIModel or similar
    ) -> Optional[str]:
        """Generate a summary of a conversation using an AI model."""
        conversation = self._conversations.get(conversation_id)
        if conversation:
            messages = [{"role": "user", "content": str(conversation.messages)}]
            response = model.chat(messages, max_tokens=500)
            summary = response.get("choices", [{}])[0].get("message", {}).get("content", "")
            conversation.summary = summary
            conversation.updated_at = datetime.utcnow()
            return summary
        return None

    def compress_conversation(
        self,
        conversation_id: UUID,
        max_tokens: int,
        model: Any,  # AIModel or similar
    ) -> Optional[List[Dict[str, Any]]]:
        """Compress a conversation to fit within a token budget."""
        conversation = self._conversations.get(conversation_id)
        if conversation:
            # Simple compression: Keep the last N messages
            compressed = conversation.messages[-max_tokens:]
            conversation.messages = compressed
            conversation.updated_at = datetime.utcnow()
            return compressed
        return None
