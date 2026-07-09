"""
Session Model for TangkuAgentOS AI Foundation Framework.

This module defines the AISession model.
"""

from typing import Any, Optional, Dict, List, UUID
from dataclasses import dataclass, field
from datetime import datetime
from ..models.base_model import AIModel
from ..providers.base_provider import BaseProvider


@dataclass
class AISession:
    """Represents an AI session."""
    session_id: UUID
    model: AIModel
    provider: BaseProvider
    context: Dict[str, Any] = field(default_factory=dict)
    conversation_history: List[Dict[str, Any]] = field(default_factory=list)
    memory_references: List[str] = field(default_factory=list)
    knowledge_references: List[str] = field(default_factory=list)
    statistics: Dict[str, Any] = field(default_factory=dict)
    cost: float = 0.0
    latency: float = 0.0
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    def add_message(self, message: Dict[str, Any]) -> None:
        """Add a message to the session's conversation history."""
        self.conversation_history.append(message)
        self.updated_at = datetime.utcnow()

    def add_memory_reference(self, memory_id: str) -> None:
        """Add a memory reference to the session."""
        if memory_id not in self.memory_references:
            self.memory_references.append(memory_id)
        self.updated_at = datetime.utcnow()

    def add_knowledge_reference(self, knowledge_id: str) -> None:
        """Add a knowledge reference to the session."""
        if knowledge_id not in self.knowledge_references:
            self.knowledge_references.append(knowledge_id)
        self.updated_at = datetime.utcnow()

    def update_statistics(self, **kwargs: Any) -> None:
        """Update session statistics."""
        self.statistics.update(kwargs)
        self.updated_at = datetime.utcnow()
