"""
AI Foundation Framework - Conversation

This module defines the Conversation class for managing AI conversations.
"""

from __future__ import annotations

import hashlib
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from typing import Any, Dict, List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from tangku_agentos.ai_foundation.models.message import Message, MessageRole

logger = logging.getLogger(__name__)


class ConversationStatus(Enum):
    """Status of a conversation."""
    CREATED = auto()
    ACTIVE = auto()
    PAUSED = auto()
    COMPLETED = auto()
    ARCHIVED = auto()


@dataclass
class ConversationMetrics:
    """Metrics for a conversation."""
    messages: int = 0
    tokens: int = 0
    cost: float = 0.0
    latency_ms: float = 0.0
    tool_calls: int = 0
    errors: int = 0
    last_message_time: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "messages": self.messages,
            "tokens": self.tokens,
            "cost": self.cost,
            "latency_ms": self.latency_ms,
            "tool_calls": self.tool_calls,
            "errors": self.errors,
            "last_message_time": self.last_message_time.isoformat() if self.last_message_time else None,
        }


@dataclass
class Conversation:
    """
    Represents an AI conversation.
    
    A conversation manages a sequence of messages between a user and an AI.
    It tracks the conversation history, state, and metrics.
    
    Attributes:
        conversation_id: Unique identifier for the conversation.
        session_id: ID of the session this conversation belongs to.
        user_id: ID of the user participating in the conversation.
        model: Model used for the conversation.
        provider: Provider used for the conversation.
        messages: List of messages in the conversation.
        status: Current status of the conversation.
        created_at: When the conversation was created.
        updated_at: When the conversation was last updated.
        expires_at: When the conversation expires.
        metrics: Conversation metrics.
        metadata: Additional metadata.
    """

    conversation_id: str
    session_id: Optional[str] = None
    user_id: Optional[str] = None
    model: Optional[str] = None
    provider: Optional[str] = None
    messages: List["Message"] = field(default_factory=list)
    status: ConversationStatus = ConversationStatus.CREATED
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None
    metrics: ConversationMetrics = field(default_factory=ConversationMetrics)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Post-initialization processing."""
        if not self.conversation_id:
            self.conversation_id = self._generate_id()
        if self.expires_at is None:
            # Default expiration: 24 hours from creation
            self.expires_at = self.created_at + datetime.timedelta(hours=24)

    def _generate_id(self) -> str:
        """Generate a unique conversation ID."""
        import time
        unique_str = f"{self.session_id or 'no_session'}:{self.user_id or 'unknown'}:{time.time()}"
        return f"conv_{hashlib.sha256(unique_str.encode()).hexdigest()[:16]}"

    @property
    def is_active(self) -> bool:
        """Check if the conversation is active."""
        return self.status == ConversationStatus.ACTIVE

    @property
    def is_expired(self) -> bool:
        """Check if the conversation is expired."""
        if self.expires_at is None:
            return False
        return datetime.utcnow() > self.expires_at

    @property
    def is_completed(self) -> bool:
        """Check if the conversation is completed."""
        return self.status == ConversationStatus.COMPLETED

    @property
    def message_count(self) -> int:
        """Get the number of messages in the conversation."""
        return len(self.messages)

    @property
    def token_count(self) -> int:
        """Get the total token count for the conversation."""
        return sum(msg.token_count for msg in self.messages)

    def activate(self) -> None:
        """Activate the conversation."""
        self.status = ConversationStatus.ACTIVE
        self.updated_at = datetime.utcnow()

    def pause(self) -> None:
        """Pause the conversation."""
        self.status = ConversationStatus.PAUSED
        self.updated_at = datetime.utcnow()

    def complete(self) -> None:
        """Mark the conversation as completed."""
        self.status = ConversationStatus.COMPLETED
        self.updated_at = datetime.utcnow()

    def archive(self) -> None:
        """Archive the conversation."""
        self.status = ConversationStatus.ARCHIVED
        self.updated_at = datetime.utcnow()

    def extend(self, hours: float = 24.0) -> None:
        """Extend the conversation expiration."""
        if self.expires_at:
            self.expires_at = datetime.utcnow() + datetime.timedelta(hours=hours)
        else:
            self.expires_at = datetime.utcnow() + datetime.timedelta(hours=hours)
        self.updated_at = datetime.utcnow()

    def add_message(self, message: "Message") -> None:
        """Add a message to the conversation."""
        self.messages.append(message)
        self.metrics.messages += 1
        self.metrics.tokens += message.token_count
        self.metrics.last_message_time = datetime.utcnow()
        self.updated_at = datetime.utcnow()

    def get_messages(self, limit: Optional[int] = None) -> List["Message"]:
        """Get messages from the conversation."""
        if limit is None:
            return self.messages.copy()
        return self.messages[-limit:]

    def get_last_message(self) -> Optional["Message"]:
        """Get the last message in the conversation."""
        return self.messages[-1] if self.messages else None

    def clear_messages(self) -> None:
        """Clear all messages from the conversation."""
        self.messages.clear()
        self.metrics.messages = 0
        self.metrics.tokens = 0
        self.updated_at = datetime.utcnow()

    def remove_last_message(self) -> Optional["Message"]:
        """Remove the last message from the conversation."""
        if self.messages:
            message = self.messages.pop()
            self.metrics.messages -= 1
            self.metrics.tokens -= message.token_count
            self.updated_at = datetime.utcnow()
            return message
        return None

    def update_model(self, model: str, provider: Optional[str] = None) -> None:
        """Update the model for the conversation."""
        self.model = model
        if provider:
            self.provider = provider
        self.updated_at = datetime.utcnow()

    def update_metadata(self, metadata: Dict[str, Any]) -> None:
        """Update the conversation metadata."""
        self.metadata.update(metadata)
        self.updated_at = datetime.utcnow()

    def record_tool_call(self, cost: float = 0.0, latency: float = 0.0) -> None:
        """Record a tool call in the conversation."""
        self.metrics.tool_calls += 1
        self.metrics.cost += cost
        self.metrics.latency_ms += latency
        self.updated_at = datetime.utcnow()

    def record_error(self, error: str) -> None:
        """Record an error in the conversation."""
        self.metrics.errors += 1
        self.metadata["last_error"] = error
        self.updated_at = datetime.utcnow()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "conversation_id": self.conversation_id,
            "session_id": self.session_id,
            "user_id": self.user_id,
            "model": self.model,
            "provider": self.provider,
            "messages": [m.to_dict() for m in self.messages],
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "metrics": self.metrics.to_dict(),
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Conversation":
        """Create from dictionary."""
        from tangku_agentos.ai_foundation.models.message import Message
        
        status = ConversationStatus.CREATED
        if "status" in data and data["status"]:
            try:
                status = ConversationStatus(data["status"])
            except ValueError:
                pass

        return cls(
            conversation_id=data.get("conversation_id", ""),
            session_id=data.get("session_id"),
            user_id=data.get("user_id"),
            model=data.get("model"),
            provider=data.get("provider"),
            messages=[Message.from_dict(m) for m in data.get("messages", [])],
            status=status,
            created_at=datetime.fromisoformat(data.get("created_at", datetime.utcnow().isoformat())),
            updated_at=datetime.fromisoformat(data.get("updated_at", datetime.utcnow().isoformat())),
            expires_at=datetime.fromisoformat(data.get("expires_at")) if data.get("expires_at") else None,
            metrics=ConversationMetrics(**data.get("metrics", {})),
            metadata=data.get("metadata", {}),
        )

    def __repr__(self) -> str:
        """Return string representation."""
        return (
            f"Conversation("
            f"id={self.conversation_id}, "
            f"session={self.session_id}, "
            f"messages={len(self.messages)}, "
            f"status={self.status.value})"
        )
