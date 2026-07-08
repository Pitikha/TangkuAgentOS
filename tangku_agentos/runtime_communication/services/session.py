"""
Runtime Communication Framework - Runtime Session Manager

The RuntimeSessionManager provides session management for TangkuAgentOS
runtime communication. It enables:
- Session creation and management
- Session tracking across runtimes
- Session state management
- Session cleanup
- Session-based authentication

Author: TangkuAgentOS Team
License: MIT
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import (
    Any,
    Callable,
    Dict,
    List,
    Optional,
    Set,
    TYPE_CHECKING,
)
import uuid

if TYPE_CHECKING:
    from tangku_agentos.runtime_communication.models.messages import Message
    from tangku_agentos.runtime_communication.services.context import Context

logger = logging.getLogger(__name__)


class SessionStatus(Enum):
    """
    Status of a session.

    Attributes:
        CREATED: Session has been created but not yet activated.
        ACTIVE: Session is active and in use.
        PAUSED: Session is paused.
        EXPIRED: Session has expired.
        TERMINATED: Session has been terminated.
        INVALID: Session is invalid.
    """

    CREATED = "created"
    ACTIVE = "active"
    PAUSED = "paused"
    EXPIRED = "expired"
    TERMINATED = "terminated"
    INVALID = "invalid"


@dataclass
class Session:
    """
    Represents a communication session between runtimes.

    A session maintains state and context for a series of related
    communications between runtimes.

    Attributes:
        session_id: Unique identifier for the session.
        runtime_id: ID of the runtime that owns the session.
        user_id: ID of the user associated with the session.
        client_id: ID of the client associated with the session.
        status: Current status of the session.
        created_at: When the session was created.
        activated_at: When the session was activated.
        last_used_at: When the session was last used.
        expires_at: When the session expires.
        context: Context associated with the session.
        metadata: Session metadata.
        state: Session state data.
        runtime_ids: Set of runtime IDs involved in the session.
        message_count: Number of messages sent in the session.
        byte_count: Number of bytes transferred in the session.
    """

    session_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    runtime_id: str = ""
    user_id: Optional[str] = None
    client_id: Optional[str] = None
    status: SessionStatus = SessionStatus.CREATED
    created_at: datetime = field(default_factory=datetime.utcnow)
    activated_at: Optional[datetime] = None
    last_used_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    context: Optional["Context"] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    state: Dict[str, Any] = field(default_factory=dict)
    runtime_ids: Set[str] = field(default_factory=set)
    message_count: int = 0
    byte_count: int = 0

    def is_active(self) -> bool:
        """Check if the session is active."""
        return self.status == SessionStatus.ACTIVE

    def is_expired(self) -> bool:
        """Check if the session has expired."""
        if self.expires_at is None:
            return False
        return datetime.utcnow() > self.expires_at

    def activate(self) -> None:
        """Activate the session."""
        self.status = SessionStatus.ACTIVE
        self.activated_at = datetime.utcnow()
        self.last_used_at = datetime.utcnow()

    def pause(self) -> None:
        """Pause the session."""
        self.status = SessionStatus.PAUSED

    def resume(self) -> None:
        """Resume the session."""
        if self.status == SessionStatus.PAUSED:
            self.status = SessionStatus.ACTIVE
            self.last_used_at = datetime.utcnow()

    def terminate(self) -> None:
        """Terminate the session."""
        self.status = SessionStatus.TERMINATED
        self.last_used_at = datetime.utcnow()

    def expire(self) -> None:
        """Expire the session."""
        self.status = SessionStatus.EXPIRED
        self.last_used_at = datetime.utcnow()

    def add_runtime(self, runtime_id: str) -> None:
        """Add a runtime to the session."""
        self.runtime_ids.add(runtime_id)

    def remove_runtime(self, runtime_id: str) -> bool:
        """Remove a runtime from the session."""
        if runtime_id in self.runtime_ids:
            self.runtime_ids.remove(runtime_id)
            return True
        return False

    def has_runtime(self, runtime_id: str) -> bool:
        """Check if a runtime is in the session."""
        return runtime_id in self.runtime_ids

    def increment_message_count(self, byte_count: int = 0) -> None:
        """Increment message count and byte count."""
        self.message_count += 1
        self.byte_count += byte_count
        self.last_used_at = datetime.utcnow()

    def to_dict(self) -> Dict[str, Any]:
        """Convert session to dictionary."""
        return {
            "session_id": self.session_id,
            "runtime_id": self.runtime_id,
            "user_id": self.user_id,
            "client_id": self.client_id,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "activated_at": self.activated_at.isoformat() if self.activated_at else None,
            "last_used_at": self.last_used_at.isoformat() if self.last_used_at else None,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "metadata": self.metadata,
            "state": self.state,
            "runtime_ids": list(self.runtime_ids),
            "message_count": self.message_count,
            "byte_count": self.byte_count,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Session":
        """Create session from dictionary."""
        session = cls(
            session_id=data.get("session_id", str(uuid.uuid4())),
            runtime_id=data.get("runtime_id", ""),
            user_id=data.get("user_id"),
            client_id=data.get("client_id"),
            status=SessionStatus(data.get("status", "created")),
            created_at=datetime.fromisoformat(data["created_at"])
            if "created_at" in data
            else datetime.utcnow(),
            activated_at=datetime.fromisoformat(data["activated_at"])
            if data.get("activated_at")
            else None,
            last_used_at=datetime.fromisoformat(data["last_used_at"])
            if data.get("last_used_at")
            else None,
            expires_at=datetime.fromisoformat(data["expires_at"])
            if data.get("expires_at")
            else None,
            metadata=data.get("metadata", {}),
            state=data.get("state", {}),
            runtime_ids=set(data.get("runtime_ids", [])),
            message_count=data.get("message_count", 0),
            byte_count=data.get("byte_count", 0),
        )
        return session


@dataclass
class SessionTemplate:
    """
    Template for creating sessions with default values.

    Attributes:
        name: Name of the template.
        default_metadata: Default session metadata.
        default_state: Default session state.
        ttl: Default time-to-live in seconds.
        max_messages: Maximum number of messages per session.
        max_bytes: Maximum number of bytes per session.
    """

    name: str
    default_metadata: Dict[str, Any] = field(default_factory=dict)
    default_state: Dict[str, Any] = field(default_factory=dict)
    ttl: float = 3600.0
    max_messages: int = 10000
    max_bytes: int = 1024 * 1024 * 100


class RuntimeSessionManager:
    """
    Session manager for TangkuAgentOS runtime communication.

    The RuntimeSessionManager provides session management capabilities
    for runtime communication.

    Thread Safety:
        This implementation is thread-safe for concurrent access.

    Example:
        >>> from tangku_agentos.runtime_communication.services.session import RuntimeSessionManager
        >>> session_manager = RuntimeSessionManager()
        >>> session = session_manager.create(runtime_id="kernel_runtime", user_id="user123")
        >>> session_manager.activate(session.session_id)

    Attributes:
        default_ttl: Default time-to-live for sessions in seconds.
        max_sessions: Maximum number of sessions to store.
        cleanup_interval: Interval between cleanup cycles in seconds.
    """

    def __init__(
        self,
        default_ttl: float = 3600.0,
        max_sessions: int = 10000,
        cleanup_interval: float = 300.0,
        enable_metrics: bool = True,
        enable_logging: bool = True,
    ):
        """
        Initialize the runtime session manager.

        Args:
            default_ttl: Default time-to-live for sessions in seconds.
            max_sessions: Maximum number of sessions to store.
            cleanup_interval: Interval between cleanup cycles in seconds.
            enable_metrics: Whether to collect metrics.
            enable_logging: Whether to enable structured logging.
        """
        self._sessions: Dict[str, Session] = {}
        self._sessions_lock = asyncio.Lock()
        self._max_sessions = max_sessions
        self._current_session: Optional[Session] = None
        self._templates: Dict[str, SessionTemplate] = {}
        self._templates_lock = asyncio.Lock()
        self._on_create: List[Callable[[Session], None]] = []
        self._on_activate: List[Callable[[Session], None]] = []
        self._on_destroy: List[Callable[[Session], None]] = []
        self._on_expire: List[Callable[[Session], None]] = []
        self._default_ttl = default_ttl
        self._cleanup_interval = cleanup_interval
        self._enable_metrics = enable_metrics
        self._enable_logging = enable_logging
        self._running = False
        self._cleanup_task: Optional[asyncio.Task] = None
        self._metrics: Dict[str, Any] = {
            "sessions_created": 0,
            "sessions_activated": 0,
            "sessions_destroyed": 0,
            "sessions_expired": 0,
            "sessions_paused": 0,
            "sessions_resumed": 0,
            "sessions_terminated": 0,
            "messages_sent": 0,
            "bytes_transferred": 0,
            "session_queries": 0,
        }
        self._metrics_lock = asyncio.Lock()
        logger.info(f"RuntimeSessionManager initialized with ttl={default_ttl}, max_sessions={max_sessions}")

    async def start(self) -> None:
        """Start the session manager background cleanup task."""
        if self._running:
            return
        self._running = True
        self._cleanup_task = asyncio.create_task(self._cleanup_loop())
        if self._enable_logging:
            logger.info("Runtime session manager started")

    async def stop(self) -> None:
        """Stop the session manager background cleanup task."""
        if not self._running:
            return
        self._running = False
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
            self._cleanup_task = None
        if self._enable_logging:
            logger.info("Runtime session manager stopped")

    def create(
        self,
        runtime_id: str = "",
        user_id: Optional[str] = None,
        client_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        state: Optional[Dict[str, Any]] = None,
        ttl: Optional[float] = None,
        template: Optional[str] = None,
    ) -> Session:
        """Create a new session."""
        if template:
            session_template = self.get_template(template)
            if not session_template:
                raise ValueError(f"Template not found: {template}")
            metadata = {**session_template.default_metadata, **(metadata or {})}
            state = {**session_template.default_state, **(state or {})}
            ttl = ttl or session_template.ttl
        else:
            metadata = metadata or {}
            state = state or {}

        session = Session(
            runtime_id=runtime_id,
            user_id=user_id,
            client_id=client_id,
            metadata=metadata,
            state=state,
        )
        if ttl is not None:
            session.expires_at = datetime.utcnow() + timedelta(seconds=ttl)
        elif self._default_ttl > 0:
            session.expires_at = datetime.utcnow() + timedelta(seconds=self._default_ttl)

        asyncio.run(self._store_session(session))
        for callback in self._on_create:
            try:
                callback(session)
            except Exception as e:
                logger.error(f"Error in session create callback: {e}")
        if self._enable_logging:
            logger.debug(f"Session created: {session.session_id}")
        return session

    async def _store_session(self, session: Session) -> None:
        """Store a session."""
        async with self._sessions_lock:
            if len(self._sessions) >= self._max_sessions:
                self._cleanup_expired()
            self._sessions[session.session_id] = session
            async with self._metrics_lock:
                self._metrics["sessions_created"] += 1

    def get(self, session_id: str) -> Optional[Session]:
        """Get a session by ID."""
        async with self._sessions_lock:
            async with self._metrics_lock:
                self._metrics["session_queries"] += 1
            return self._sessions.get(session_id)

    def get_current(self) -> Optional[Session]:
        """Get the current session."""
        return self._current_session

    def set_current(self, session: Optional[Session]) -> None:
        """Set the current session."""
        self._current_session = session

    def activate(self, session_id: str) -> bool:
        """Activate a session."""
        return asyncio.run(self._activate_async(session_id))

    async def _activate_async(self, session_id: str) -> bool:
        """Async version of activate."""
        async with self._sessions_lock:
            if session_id not in self._sessions:
                return False
            session = self._sessions[session_id]
            if session.status == SessionStatus.ACTIVE or session.is_expired():
                return False
            session.activate()
            async with self._metrics_lock:
                self._metrics["sessions_activated"] += 1
            for callback in self._on_activate:
                try:
                    callback(session)
                except Exception as e:
                    logger.error(f"Error in session activate callback: {e}")
            if self._enable_logging:
                logger.info(f"Session activated: {session_id}")
            return True

    def deactivate(self, session_id: str) -> bool:
        """Deactivate a session (pause it)."""
        return asyncio.run(self._deactivate_async(session_id))

    async def _deactivate_async(self, session_id: str) -> bool:
        """Async version of deactivate."""
        async with self._sessions_lock:
            if session_id not in self._sessions:
                return False
            session = self._sessions[session_id]
            if session.status != SessionStatus.ACTIVE:
                return False
            session.pause()
            async with self._metrics_lock:
                self._metrics["sessions_paused"] += 1
            if self._enable_logging:
                logger.info(f"Session deactivated: {session_id}")
            return True

    def resume(self, session_id: str) -> bool:
        """Resume a paused session."""
        return asyncio.run(self._resume_async(session_id))

    async def _resume_async(self, session_id: str) -> bool:
        """Async version of resume."""
        async with self._sessions_lock:
            if session_id not in self._sessions:
                return False
            session = self._sessions[session_id]
            if session.status != SessionStatus.PAUSED:
                return False
            session.resume()
            async with self._metrics_lock:
                self._metrics["sessions_resumed"] += 1
            if self._enable_logging:
                logger.info(f"Session resumed: {session_id}")
            return True

    def terminate(self, session_id: str) -> bool:
        """Terminate a session."""
        return asyncio.run(self._terminate_async(session_id))

    async def _terminate_async(self, session_id: str) -> bool:
        """Async version of terminate."""
        async with self._sessions_lock:
            if session_id not in self._sessions:
                return False
            session = self._sessions[session_id]
            if session.status in (SessionStatus.TERMINATED, SessionStatus.EXPIRED):
                return False
            session.terminate()
            async with self._metrics_lock:
                self._metrics["sessions_terminated"] += 1
            for callback in self._on_destroy:
                try:
                    callback(session)
                except Exception as e:
                    logger.error(f"Error in session destroy callback: {e}")
            if self._enable_logging:
                logger.info(f"Session terminated: {session_id}")
            return True

    def destroy(self, session_id: str) -> bool:
        """Destroy a session (remove from storage)."""
        return asyncio.run(self._destroy_async(session_id))

    async def _destroy_async(self, session_id: str) -> bool:
        """Async version of destroy."""
        async with self._sessions_lock:
            if session_id not in self._sessions:
                return False
            session = self._sessions[session_id]
            for callback in self._on_destroy:
                try:
                    callback(session)
                except Exception as e:
                    logger.error(f"Error in session destroy callback: {e}")
            del self._sessions[session_id]
            async with self._metrics_lock:
                self._metrics["sessions_destroyed"] += 1
            if self._enable_logging:
                logger.debug(f"Session destroyed: {session_id}")
            return True

    def add_runtime(self, session_id: str, runtime_id: str) -> bool:
        """Add a runtime to a session."""
        return asyncio.run(self._add_runtime_async(session_id, runtime_id))

    async def _add_runtime_async(self, session_id: str, runtime_id: str) -> bool:
        """Async version of add_runtime."""
        async with self._sessions_lock:
            if session_id not in self._sessions:
                return False
            session = self._sessions[session_id]
            if runtime_id in session.runtime_ids:
                return False
            session.add_runtime(runtime_id)
            return True

    def remove_runtime(self, session_id: str, runtime_id: str) -> bool:
        """Remove a runtime from a session."""
        return asyncio.run(self._remove_runtime_async(session_id, runtime_id))

    async def _remove_runtime_async(self, session_id: str, runtime_id: str) -> bool:
        """Async version of remove_runtime."""
        async with self._sessions_lock:
            if session_id not in self._sessions:
                return False
            return self._sessions[session_id].remove_runtime(runtime_id)

    def record_message(self, session_id: str, byte_count: int = 0) -> bool:
        """Record a message sent in a session."""
        return asyncio.run(self._record_message_async(session_id, byte_count))

    async def _record_message_async(self, session_id: str, byte_count: int = 0) -> bool:
        """Async version of record_message."""
        async with self._sessions_lock:
            if session_id not in self._sessions:
                return False
            session = self._sessions[session_id]
            session.increment_message_count(byte_count)
            async with self._metrics_lock:
                self._metrics["messages_sent"] += 1
                self._metrics["bytes_transferred"] += byte_count
            return True

    def cleanup(self) -> int:
        """Clean up expired sessions."""
        return asyncio.run(self._cleanup_async())

    async def _cleanup_async(self) -> int:
        """Async version of cleanup."""
        count = 0
        async with self._sessions_lock:
            expired = [sid for sid, session in self._sessions.items() if session.is_expired()]
            for sid in expired:
                session = self._sessions[sid]
                for callback in self._on_expire:
                    try:
                        callback(session)
                    except Exception as e:
                        logger.error(f"Error in session expire callback: {e}")
                del self._sessions[sid]
                async with self._metrics_lock:
                    self._metrics["sessions_expired"] += 1
                count += 1
        if count > 0 and self._enable_logging:
            logger.info(f"Cleaned up {count} expired sessions")
        return count

    def _cleanup_expired(self) -> None:
        """Clean up expired sessions (internal)."""
        expired = [sid for sid, session in self._sessions.items() if session.is_expired()]
        for sid in expired:
            session = self._sessions[sid]
            for callback in self._on_expire:
                try:
                    callback(session)
                except Exception as e:
                    logger.error(f"Error in session expire callback: {e}")
            del self._sessions[sid]
            async with self._metrics_lock:
                self._metrics["sessions_expired"] += 1

    async def _cleanup_loop(self) -> None:
        """Background cleanup loop."""
        while self._running:
            try:
                await asyncio.sleep(self._cleanup_interval)
                await self._cleanup_async()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in cleanup loop: {e}")

    def register_template(self, template: SessionTemplate) -> None:
        """Register a session template."""
        asyncio.run(self._register_template_async(template))

    async def _register_template_async(self, template: SessionTemplate) -> None:
        """Async version of register_template."""
        async with self._templates_lock:
            self._templates[template.name] = template
            if self._enable_logging:
                logger.info(f"Session template registered: {template.name}")

    def unregister_template(self, template_name: str) -> bool:
        """Unregister a session template."""
        return asyncio.run(self._unregister_template_async(template_name))

    async def _unregister_template_async(self, template_name: str) -> bool:
        """Async version of unregister_template."""
        async with self._templates_lock:
            if template_name in self._templates:
                del self._templates[template_name]
                if self._enable_logging:
                    logger.info(f"Session template unregistered: {template_name}")
                return True
            return False

    def get_template(self, template_name: str) -> Optional[SessionTemplate]:
        """Get a session template."""
        return self._templates.get(template_name)

    def create_from_template(self, template_name: str, runtime_id: str = "", **kwargs) -> Session:
        """Create a session from a template."""
        template = self.get_template(template_name)
        if not template:
            raise ValueError(f"Template not found: {template_name}")
        metadata = {**template.default_metadata, **kwargs.get("metadata", {})}
        state = {**template.default_state, **kwargs.get("state", {})}
        return self.create(
            runtime_id=runtime_id,
            user_id=kwargs.get("user_id"),
            client_id=kwargs.get("client_id"),
            metadata=metadata,
            state=state,
            ttl=kwargs.get("ttl", template.ttl),
        )

    def on_create(self, callback: Callable[[Session], None]) -> None:
        """Register a callback for session creation."""
        self._on_create.append(callback)

    def on_activate(self, callback: Callable[[Session], None]) -> None:
        """Register a callback for session activation."""
        self._on_activate.append(callback)

    def on_destroy(self, callback: Callable[[Session], None]) -> None:
        """Register a callback for session destruction."""
        self._on_destroy.append(callback)

    def on_expire(self, callback: Callable[[Session], None]) -> None:
        """Register a callback for session expiration."""
        self._on_expire.append(callback)

    def list_sessions(self, runtime_id: Optional[str] = None, user_id: Optional[str] = None, status: Optional[SessionStatus] = None) -> List[Session]:
        """List sessions matching the given criteria."""
        sessions = []
        for session in self._sessions.values():
            if runtime_id and session.runtime_id != runtime_id:
                continue
            if user_id and session.user_id != user_id:
                continue
            if status and session.status != status:
                continue
            sessions.append(session)
        return sessions

    def get_metrics(self) -> Dict[str, Any]:
        """Get session manager metrics."""
        return {
            **self._metrics,
            "sessions_count": len(self._sessions),
            "sessions_active": sum(1 for s in self._sessions.values() if s.is_active()),
            "templates_count": len(self._templates),
        }

    def clear(self) -> int:
        """Clear all sessions."""
        count = len(self._sessions)
        self._sessions.clear()
        self._current_session = None
        self._metrics = {
            "sessions_created": 0,
            "sessions_activated": 0,
            "sessions_destroyed": 0,
            "sessions_expired": 0,
            "sessions_paused": 0,
            "sessions_resumed": 0,
            "sessions_terminated": 0,
            "messages_sent": 0,
            "bytes_transferred": 0,
            "session_queries": 0,
        }
        return count

    def shutdown(self) -> None:
        """Shutdown the session manager."""
        asyncio.run(self._stop())
        self.clear()
        self._templates.clear()
        self._on_create.clear()
        self._on_activate.clear()
        self._on_destroy.clear()
        self._on_expire.clear()
        logger.info("Runtime session manager shutdown complete")

    def __repr__(self) -> str:
        """Return string representation."""
        return f"RuntimeSessionManager(sessions={len(self._sessions)}, active={sum(1 for s in self._sessions.values() if s.is_active())}, templates={len(self._templates)})"
