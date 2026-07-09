"""
Conversation History for TangkuAgentOS AI Foundation Framework.

This module manages the history of conversations.
"""

from typing import Any, Optional, Dict, List, UUID
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class ConversationHistory:
    """Manages the history of a conversation."""
    conversation_id: UUID
    history: List[Dict[str, Any]] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    def add_message(self, message: Dict[str, Any]) -> None:
        """Add a message to the conversation history."""
        self.history.append(message)
        self.updated_at = datetime.utcnow()

    def get_history(self) -> List[Dict[str, Any]]:
        """Retrieve the full conversation history."""
        return self.history

    def clear_history(self) -> None:
        """Clear the conversation history."""
        self.history.clear()
        self.updated_at = datetime.utcnow()

    def get_last_message(self) -> Optional[Dict[str, Any]]:
        """Retrieve the last message in the conversation history."""
        return self.history[-1] if self.history else None

    def get_messages_since(self, timestamp: datetime) -> List[Dict[str, Any]]:
        """Retrieve messages since a specific timestamp."""
        return [msg for msg in self.history if msg.get("timestamp", datetime.min) >= timestamp]
