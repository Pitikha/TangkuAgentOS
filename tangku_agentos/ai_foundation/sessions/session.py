"""
AI Foundation Framework - AI Session

This module defines the AISession class for managing AI sessions.
"""

from __future__ import annotations

import asyncio
import hashlib
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from typing import Any, Dict, List, Optional, Set, TYPE_CHECKING

if TYPE_CHECKING:
    from tangku_agentos.ai_foundation.core.config import AIConfig
    from tangku_agentos.ai_foundation.core.foundation import AIFoundation

logger = logging.getLogger(__name__)


class SessionStatus(Enum):
    """Status of an AI session."""
    CREATED = auto()
    ACTIVE = auto()
    PAUSED = auto()
    EXPIRED = auto()
    CLOSED = auto()


@dataclass
class SessionMetrics:
    """Metrics for an AI session."""
    requests: int = 0
    tokens_processed: int = 0
    cost_incurred: float = 0.0
    latency_ms: float = 0.0
    errors: int = 0
    last_request_time: Optional[datetime] = None
    last_error: Optional[str] = None
    last_error_time: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "requests": self.requests,
            "tokens_processed": self.tokens_processed,
            "cost_incurred": self.cost_incurred,
            "latency_ms": self.latency_ms,
            "errors": self.errors,
            "last_request_time": self.last_request_time.isoformat() if self.last_request_time else None,
            "last_error": self.last_error,
            "last_error_time": self.last_error_time.isoformat() if self.last_error_time else None,
        }

    def reset(self) -> None:
        """Reset metrics."""
        self.requests = 0
        self.tokens_processed = 0
        self.cost_incurred = 0.0
        self.latency_ms = 0.0
        self.errors = 0
        self.last_request_time = None
        self.last_error = None
        self.last_error_time = None


@dataclass
class AISession:
    """
    Represents an AI session.
    
    An AI session manages the state and context for a series of AI interactions.
    It tracks conversation history, model usage, and session-specific settings.
    
    Attributes:
        session_id: Unique identifier for the session.
        user_id: ID of the user associated with the session.
        model: Default model for the session.
        provider: Default provider for the session.
        context: Session-specific context.
        settings: Session-specific settings.
        status: Current status of the session.
        created_at: When the session was created.
        updated_at: When the session was last updated.
        expires_at: When the session expires.
        metrics: Session metrics.
        metadata: Additional metadata.
    """

    session_id: str
    user_id: Optional[str] = None
    model: Optional[str] = None
    provider: Optional[str] = None
    context: Dict[str, Any] = field(default_factory=dict)
    settings: Dict[str, Any] = field(default_factory=dict)
    status: SessionStatus = SessionStatus.CREATED
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None
    metrics: SessionMetrics = field(default_factory=SessionMetrics)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Post-initialization processing."""
        if not self.session_id:
            self.session_id = self._generate_id()
        if self.expires_at is None:
            # Default expiration: 1 hour from creation
            self.expires_at = self.created_at + datetime.timedelta(hours=1)

    def _generate_id(self) -> str:
        """Generate a unique session ID."""
        import time
        unique_str = f"{self.user_id or 'unknown'}:{time.time()}:{hashlib.sha256(str(self.context).encode()).hexdigest()[:8]}"
        return f"session_{hashlib.sha256(unique_str.encode()).hexdigest()[:16]}"

    @property
    def is_active(self) -> bool:
        """Check if the session is active."""
        return self.status == SessionStatus.ACTIVE

    @property
    def is_expired(self) -> bool:
        """Check if the session is expired."""
        if self.expires_at is None:
            return False
        return datetime.utcnow() > self.expires_at

    @property
    def is_closed(self) -> bool:
        """Check if the session is closed."""
        return self.status == SessionStatus.CLOSED

    def activate(self) -> None:
        """Activate the session."""
        self.status = SessionStatus.ACTIVE
        self.updated_at = datetime.utcnow()

    def pause(self) -> None:
        """Pause the session."""
        self.status = SessionStatus.PAUSED
        self.updated_at = datetime.utcnow()

    def close(self) -> None:
        """Close the session."""
        self.status = SessionStatus.CLOSED
        self.updated_at = datetime.utcnow()

    def extend(self, hours: float = 1.0) -> None:
        """Extend the session expiration."""
        if self.expires_at:
            self.expires_at = datetime.utcnow() + datetime.timedelta(hours=hours)
        else:
            self.expires_at = datetime.utcnow() + datetime.timedelta(hours=hours)
        self.updated_at = datetime.utcnow()

    def update_context(self, context: Dict[str, Any]) -> None:
        """Update the session context."""
        self.context.update(context)
        self.updated_at = datetime.utcnow()

    def update_settings(self, settings: Dict[str, Any]) -> None:
        """Update the session settings."""
        self.settings.update(settings)
        self.updated_at = datetime.utcnow()

    def update_model(self, model: str, provider: Optional[str] = None) -> None:
        """Update the default model for the session."""
        self.model = model
        if provider:
            self.provider = provider
        self.updated_at = datetime.utcnow()

    def record_request(self, tokens: int = 0, cost: float = 0.0, latency: float = 0.0) -> None:
        """Record a request to the session."""
        self.metrics.requests += 1
        self.metrics.tokens_processed += tokens
        self.metrics.cost_incurred += cost
        self.metrics.latency_ms += latency
        self.metrics.last_request_time = datetime.utcnow()
        self.updated_at = datetime.utcnow()

    def record_error(self, error: str) -> None:
        """Record an error in the session."""
        self.metrics.errors += 1
        self.metrics.last_error = error
        self.metrics.last_error_time = datetime.utcnow()
        self.updated_at = datetime.utcnow()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "session_id": self.session_id,
            "user_id": self.user_id,
            "model": self.model,
            "provider": self.provider,
            "context": self.context,
            "settings": self.settings,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "metrics": self.metrics.to_dict(),
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AISession":
        """Create from dictionary."""
        status = SessionStatus.CREATED
        if "status" in data and data["status"]:
            try:
                status = SessionStatus(data["status"])
            except ValueError:
                pass

        return cls(
            session_id=data.get("session_id", ""),
            user_id=data.get("user_id"),
            model=data.get("model"),
            provider=data.get("provider"),
            context=data.get("context", {}),
            settings=data.get("settings", {}),
            status=status,
            created_at=datetime.fromisoformat(data.get("created_at", datetime.utcnow().isoformat())),
            updated_at=datetime.fromisoformat(data.get("updated_at", datetime.utcnow().isoformat())),
            expires_at=datetime.fromisoformat(data.get("expires_at")) if data.get("expires_at") else None,
            metrics=SessionMetrics(**data.get("metrics", {})),
            metadata=data.get("metadata", {}),
        )

    def __repr__(self) -> str:
        """Return string representation."""
        return (
            f"AISession("
            f"id={self.session_id}, "
            f"user={self.user_id}, "
            f"model={self.model}, "
            f"status={self.status.value})"
        )
