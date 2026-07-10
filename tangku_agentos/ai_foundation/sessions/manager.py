"""
AI Foundation Framework - Session Manager

This module provides the SessionManager class for managing AI sessions.
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Set, TYPE_CHECKING

if TYPE_CHECKING:
    from tangku_agentos.ai_foundation.sessions.session import AISession
    from tangku_agentos.ai_foundation.core.config import AIConfig
    from tangku_agentos.ai_foundation.core.foundation import AIFoundation

logger = logging.getLogger(__name__)


@dataclass
class SessionManagerMetrics:
    """Metrics for the session manager."""
    sessions_created: int = 0
    sessions_activated: int = 0
    sessions_closed: int = 0
    sessions_expired: int = 0
    active_sessions: int = 0
    errors: int = 0
    last_error: Optional[str] = None
    last_error_time: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "sessions_created": self.sessions_created,
            "sessions_activated": self.sessions_activated,
            "sessions_closed": self.sessions_closed,
            "sessions_expired": self.sessions_expired,
            "active_sessions": self.active_sessions,
            "errors": self.errors,
            "last_error": self.last_error,
            "last_error_time": self.last_error_time.isoformat() if self.last_error_time else None,
        }


class SessionManager:
    """
    Manager for AI sessions.
    
    This class provides methods for creating, managing, and tracking AI sessions.
    It handles session lifecycle, expiration, and cleanup.
    
    Thread Safety:
        This class is thread-safe for concurrent access.
    
    Example:
        >>> from tangku_agentos.ai_foundation import SessionManager
        >>> 
        >>> # Create manager
        >>> manager = SessionManager()
        >>> 
        >>> # Create a session
        >>> session = await manager.create(user_id="user123", model="gpt-4")
        >>> 
        >>> # Get a session
        >>> session = manager.get(session.session_id)
        >>> 
        >>> # List all sessions
        >>> sessions = manager.list_sessions()
        >>> 
        >>> # Close a session
        >>> await manager.close(session.session_id)
    """

    def __init__(self, config: "AIConfig", foundation: "AIFoundation"):
        """
        Initialize the session manager.
        
        Args:
            config: AI Foundation configuration.
            foundation: AI Foundation instance.
        """
        self._config = config
        self._foundation = foundation
        self._sessions: Dict[str, "AISession"] = {}
        self._user_sessions: Dict[str, Set[str]] = {}  # user_id -> set of session_ids
        self._metrics = SessionManagerMetrics()
        self._lock = asyncio.Lock()
        self._initialized = False
        self._started = False
        self._cleanup_task: Optional[asyncio.Task] = None
        
        logger.info("SessionManager initialized")

    @property
    def config(self) -> "AIConfig":
        """Get the configuration."""
        return self._config

    @property
    def foundation(self) -> "AIFoundation":
        """Get the AI Foundation instance."""
        return self._foundation

    @property
    def metrics(self) -> SessionManagerMetrics:
        """Get the session manager metrics."""
        return self._metrics

    @property
    def is_initialized(self) -> bool:
        """Check if the manager is initialized."""
        return self._initialized

    @property
    def is_started(self) -> bool:
        """Check if the manager is started."""
        return self._started

    async def initialize(self) -> None:
        """
        Initialize the session manager.
        """
        if self._initialized:
            logger.warning("SessionManager already initialized")
            return
        
        logger.info("Initializing SessionManager...")
        
        self._initialized = True
        logger.info("SessionManager initialized successfully")

    async def start(self) -> None:
        """
        Start the session manager.
        
        This method starts the cleanup task for expired sessions.
        """
        if self._started:
            logger.warning("SessionManager already started")
            return
        
        if not self._initialized:
            await self.initialize()
        
        logger.info("Starting SessionManager...")
        
        # Start cleanup task
        self._cleanup_task = asyncio.create_task(self._cleanup_expired_sessions())
        
        self._started = True
        logger.info("SessionManager started successfully")

    async def stop(self) -> None:
        """
        Stop the session manager.
        
        This method stops the cleanup task and cleans up resources.
        """
        if not self._started:
            logger.warning("SessionManager not started")
            return
        
        logger.info("Stopping SessionManager...")
        
        # Cancel cleanup task
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
        
        self._started = False
        logger.info("SessionManager stopped successfully")

    async def _cleanup_expired_sessions(self) -> None:
        """Clean up expired sessions periodically."""
        import time
        
        cleanup_interval = self._config.sessions.session_cleanup_interval
        
        while True:
            try:
                await asyncio.sleep(cleanup_interval)
                await self._cleanup_expired()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error during session cleanup: {e}")

    async def _cleanup_expired(self) -> None:
        """Clean up expired sessions."""
        async with self._lock:
            expired_sessions = []
            
            for session_id, session in self._sessions.items():
                if session.is_expired:
                    expired_sessions.append(session_id)
            
            for session_id in expired_sessions:
                await self._remove_session(session_id, expired=True)

    async def create(
        self,
        user_id: Optional[str] = None,
        model: Optional[str] = None,
        provider: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
        settings: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> "AISession":
        """
        Create a new AI session.
        
        Args:
            user_id: ID of the user associated with the session.
            model: Default model for the session.
            provider: Default provider for the session.
            context: Session-specific context.
            settings: Session-specific settings.
            metadata: Additional metadata.
        
        Returns:
            AISession instance.
        """
        from tangku_agentos.ai_foundation.sessions.session import AISession
        
        async with self._lock:
            # Check session limit
            max_sessions = self._config.sessions.max_sessions
            if len(self._sessions) >= max_sessions:
                # Remove oldest session
                await self._remove_oldest_session()
            
            # Create session
            session = AISession(
                user_id=user_id,
                model=model or self._config.models.default_chat_model,
                provider=provider or self._config.providers.default_provider,
                context=context or {},
                settings=settings or {},
                metadata=metadata or {},
            )
            
            # Store session
            self._sessions[session.session_id] = session
            
            # Index by user
            if user_id:
                if user_id not in self._user_sessions:
                    self._user_sessions[user_id] = set()
                self._user_sessions[user_id].add(session.session_id)
            
            # Update metrics
            self._metrics.sessions_created += 1
            self._metrics.active_sessions = len(self._sessions)
            
            logger.debug(f"Session created: {session.session_id}")
            return session

    async def get(self, session_id: str) -> Optional["AISession"]:
        """
        Get a session by ID.
        
        Args:
            session_id: ID of the session to get.
        
        Returns:
            AISession instance or None if not found.
        """
        async with self._lock:
            session = self._sessions.get(session_id)
            if session and session.is_expired:
                await self._remove_session(session_id, expired=True)
                return None
            return session

    async def get_by_user(self, user_id: str) -> List["AISession"]:
        """
        Get all sessions for a specific user.
        
        Args:
            user_id: ID of the user.
        
        Returns:
            List of AISession instances.
        """
        async with self._lock:
            session_ids = self._user_sessions.get(user_id, set())
            sessions = []
            
            for session_id in session_ids:
                session = self._sessions.get(session_id)
                if session and not session.is_expired:
                    sessions.append(session)
            
            return sessions

    async def list_sessions(self, user_id: Optional[str] = None) -> List["AISession"]:
        """
        List all sessions, optionally filtered by user.
        
        Args:
            user_id: Optional user ID to filter by.
        
        Returns:
            List of AISession instances.
        """
        async with self._lock:
            if user_id:
                return await self.get_by_user(user_id)
            
            # Return all non-expired sessions
            sessions = []
            for session in self._sessions.values():
                if not session.is_expired:
                    sessions.append(session)
            return sessions

    async def activate(self, session_id: str) -> Optional["AISession"]:
        """
        Activate a session.
        
        Args:
            session_id: ID of the session to activate.
        
        Returns:
            AISession instance or None if not found.
        """
        async with self._lock:
            session = self._sessions.get(session_id)
            if session:
                session.activate()
                self._metrics.sessions_activated += 1
                logger.debug(f"Session activated: {session_id}")
            return session

    async def close(self, session_id: str) -> bool:
        """
        Close a session.
        
        Args:
            session_id: ID of the session to close.
        
        Returns:
            True if session was closed, False if not found.
        """
        async with self._lock:
            return await self._remove_session(session_id, closed=True)

    async def close_all(self, user_id: Optional[str] = None) -> int:
        """
        Close all sessions, optionally filtered by user.
        
        Args:
            user_id: Optional user ID to filter by.
        
        Returns:
            Number of sessions closed.
        """
        async with self._lock:
            if user_id:
                session_ids = list(self._user_sessions.get(user_id, set()))
            else:
                session_ids = list(self._sessions.keys())
            
            count = 0
            for session_id in session_ids:
                if await self._remove_session(session_id, closed=True):
                    count += 1
            
            return count

    async def _remove_session(self, session_id: str, expired: bool = False, closed: bool = False) -> bool:
        """
        Remove a session from the manager.
        
        Args:
            session_id: ID of the session to remove.
            expired: Whether the session expired.
            closed: Whether the session was closed.
        
        Returns:
            True if session was removed, False if not found.
        """
        session = self._sessions.get(session_id)
        if not session:
            return False
        
        # Remove from user index
        if session.user_id and session.user_id in self._user_sessions:
            self._user_sessions[session.user_id].discard(session_id)
            if not self._user_sessions[session.user_id]:
                del self._user_sessions[session.user_id]
        
        # Remove from sessions
        del self._sessions[session_id]
        
        # Update metrics
        if expired:
            self._metrics.sessions_expired += 1
        if closed:
            self._metrics.sessions_closed += 1
        self._metrics.active_sessions = len(self._sessions)
        
        logger.debug(f"Session removed: {session_id} (expired={expired}, closed={closed})")
        return True

    async def _remove_oldest_session(self) -> bool:
        """
        Remove the oldest session.
        
        Returns:
            True if a session was removed, False otherwise.
        """
        if not self._sessions:
            return False
        
        # Find oldest session
        oldest_id = min(self._sessions.keys(), key=lambda sid: self._sessions[sid].created_at)
        return await self._remove_session(oldest_id, closed=True)

    async def update(self, session_id: str, **kwargs) -> bool:
        """
        Update a session.
        
        Args:
            session_id: ID of the session to update.
            **kwargs: Session attributes to update.
        
        Returns:
            True if session was updated, False if not found.
        """
        async with self._lock:
            session = self._sessions.get(session_id)
            if not session:
                return False
            
            for key, value in kwargs.items():
                if hasattr(session, key):
                    setattr(session, key, value)
            
            session.updated_at = datetime.utcnow()
            return True

    async def extend(self, session_id: str, hours: float = 1.0) -> bool:
        """
        Extend a session's expiration.
        
        Args:
            session_id: ID of the session to extend.
            hours: Number of hours to extend.
        
        Returns:
            True if session was extended, False if not found.
        """
        async with self._lock:
            session = self._sessions.get(session_id)
            if not session:
                return False
            
            session.extend(hours)
            return True

    async def get_info(self) -> Dict[str, Any]:
        """
        Get information about the session manager.
        
        Returns:
            Dictionary with session manager information.
        """
        return {
            "sessions": len(self._sessions),
            "active_sessions": self._metrics.active_sessions,
            "user_sessions": {user: len(sessions) for user, sessions in self._user_sessions.items()},
            "metrics": self._metrics.to_dict(),
        }

    async def reset(self) -> None:
        """
        Reset the session manager.
        
        This method clears all sessions and resets all state.
        """
        logger.info("Resetting SessionManager...")
        
        async with self._lock:
            # Cancel cleanup task
            if self._cleanup_task:
                self._cleanup_task.cancel()
                try:
                    await self._cleanup_task
                except asyncio.CancelledError:
                    pass
            
            # Clear all sessions
            self._sessions.clear()
            self._user_sessions.clear()
            
            # Reset metrics
            self._metrics = SessionManagerMetrics()
            
            # Reset state
            self._initialized = False
            self._started = False
            self._cleanup_task = None
        
        logger.info("SessionManager reset successfully")

    def __repr__(self) -> str:
        """Return string representation."""
        return (
            f"SessionManager("
            f"sessions={len(self._sessions)}, "
            f"active={self._metrics.active_sessions})"
        )
