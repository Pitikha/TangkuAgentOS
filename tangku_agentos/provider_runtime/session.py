"""Session management for the TangkuAgentOS Provider Runtime."""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from threading import RLock
from typing import Any, Dict, List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from .types import ModelID, ProviderID, SessionID, SessionState

from .exceptions import SessionExpiredError, SessionNotFoundError
from .interfaces import ProviderSession


@dataclass
class SessionState:
    """State of a provider session."""

    session_id: SessionID
    provider_id: ProviderID
    model_id: ModelID
    context: List[Dict[str, Any]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: float = field(default_factory=time.time)
    last_used_at: float = field(default_factory=time.time)
    expires_at: Optional[float] = None


class ProviderSessionManager(ProviderSession):
    """
    Manages conversation sessions with:
    - Context preservation
    - Provider switching
    - Streaming
    - Cancellation
    - Recovery
    """

    def __init__(self) -> None:
        self._sessions: Dict[SessionID, SessionState] = {}
        self._lock = RLock()
        self._default_ttl = 3600.0  # 1 hour

    def start(
        self,
        provider_id: ProviderID,
        model_id: Optional[ModelID] = None,
        ttl: Optional[float] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> SessionID:
        """
        Start a new session with a provider.
        Supports optional TTL and metadata.
        """
        session_id = str(uuid.uuid4())
        expires_at = time.time() + (ttl or self._default_ttl)
        with self._lock:
            self._sessions[session_id] = SessionState(
                session_id=session_id,
                provider_id=provider_id,
                model_id=model_id or "default",
                metadata=metadata or {},
                expires_at=expires_at,
            )
        return session_id

    def end(self, session_id: SessionID) -> None:
        """End a session by ID."""
        with self._lock:
            self._sessions.pop(session_id, None)

    def get_session(self, session_id: SessionID) -> SessionState:
        """
        Get a session by ID.
        Raises SessionNotFoundError if the session is not found.
        Raises SessionExpiredError if the session has expired.
        """
        with self._lock:
            session = self._sessions.get(session_id)
            if session is None:
                raise SessionNotFoundError(f"Session {session_id} not found")
            if session.expires_at is not None and session.expires_at < time.time():
                raise SessionExpiredError(f"Session {session_id} has expired")
            session.last_used_at = time.time()
            return session

    def update_session(
        self,
        session_id: SessionID,
        context: Optional[List[Dict[str, Any]]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Update a session's context or metadata."""
        with self._lock:
            session = self._sessions.get(session_id)
            if session is None:
                raise SessionNotFoundError(f"Session {session_id} not found")
            if context is not None:
                session.context = context
            if metadata is not None:
                session.metadata.update(metadata)
            session.last_used_at = time.time()

    def add_message(
        self,
        session_id: SessionID,
        role: str,
        content: Any,
    ) -> None:
        """Add a message to a session's context."""
        with self._lock:
            session = self._sessions.get(session_id)
            if session is None:
                raise SessionNotFoundError(f"Session {session_id} not found")
            session.context.append({"role": role, "content": content})
            session.last_used_at = time.time()

    def get_context(self, session_id: SessionID) -> List[Dict[str, Any]]:
        """Get the context for a session."""
        session = self.get_session(session_id)
        return session.context

    def switch_provider(
        self,
        session_id: SessionID,
        new_provider_id: ProviderID,
        new_model_id: Optional[ModelID] = None,
    ) -> None:
        """Switch the provider for a session."""
        with self._lock:
            session = self._sessions.get(session_id)
            if session is None:
                raise SessionNotFoundError(f"Session {session_id} not found")
            session.provider_id = new_provider_id
            if new_model_id is not None:
                session.model_id = new_model_id
            session.last_used_at = time.time()

    def extend_session(self, session_id: SessionID, ttl: float) -> None:
        """Extend a session's TTL."""
        with self._lock:
            session = self._sessions.get(session_id)
            if session is None:
                raise SessionNotFoundError(f"Session {session_id} not found")
            session.expires_at = time.time() + ttl

    def cleanup_expired(self) -> int:
        """Remove expired sessions. Returns the number of sessions removed."""
        with self._lock:
            current_time = time.time()
            expired = [
                session_id
                for session_id, session in self._sessions.items()
                if session.expires_at is not None and session.expires_at < current_time
            ]
            for session_id in expired:
                del self._sessions[session_id]
            return len(expired)

    def list_sessions(self) -> List[SessionState]:
        """List all active sessions."""
        with self._lock:
            return list(self._sessions.values())

    def list_sessions_for_provider(self, provider_id: ProviderID) -> List[SessionState]:
        """List all sessions for a provider."""
        with self._lock:
            return [
                session
                for session in self._sessions.values()
                if session.provider_id == provider_id
            ]

    def get_session_info(self, session_id: SessionID) -> Dict[str, Any]:
        """Get info for a session."""
        session = self.get_session(session_id)
        return {
            "session_id": session.session_id,
            "provider_id": session.provider_id,
            "model_id": session.model_id,
            "context_length": len(session.context),
            "created_at": session.created_at,
            "last_used_at": session.last_used_at,
            "expires_at": session.expires_at,
            "metadata": session.metadata,
        }
