"""
Session Manager for TangkuAgentOS AI Foundation Framework.

This module manages AI sessions, including conversation history, model selection, and context.
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


class SessionManager:
    """Manages AI sessions for TangkuAgentOS."""

    def __init__(self):
        self._sessions: Dict[UUID, AISession] = {}

    def create_session(
        self,
        model: AIModel,
        provider: BaseProvider,
        context: Optional[Dict[str, Any]] = None,
    ) -> AISession:
        """Create a new AI session."""
        session_id = UUID(int=datetime.utcnow().timestamp())
        session = AISession(
            session_id=session_id,
            model=model,
            provider=provider,
            context=context or {},
        )
        self._sessions[session_id] = session
        return session

    def get_session(self, session_id: UUID) -> Optional[AISession]:
        """Retrieve an AI session by its ID."""
        return self._sessions.get(session_id)

    def update_session(
        self,
        session_id: UUID,
        **kwargs: Any,
    ) -> Optional[AISession]:
        """Update an AI session."""
        session = self._sessions.get(session_id)
        if session:
            for key, value in kwargs.items():
                setattr(session, key, value)
            session.updated_at = datetime.utcnow()
        return session

    def delete_session(self, session_id: UUID) -> bool:
        """Delete an AI session."""
        if session_id in self._sessions:
            del self._sessions[session_id]
            return True
        return False

    def list_sessions(self) -> List[AISession]:
        """List all active AI sessions."""
        return list(self._sessions.values())
