"""
Session History for TangkuAgentOS AI Foundation Framework.

This module manages the history of AI sessions.
"""

from typing import Any, Optional, Dict, List, UUID
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class SessionHistory:
    """Manages the history of AI sessions."""
    session_id: UUID
    history: List[Dict[str, Any]] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    def add_entry(self, entry: Dict[str, Any]) -> None:
        """Add an entry to the session history."""
        self.history.append(entry)
        self.updated_at = datetime.utcnow()

    def get_history(self) -> List[Dict[str, Any]]:
        """Retrieve the full session history."""
        return self.history

    def clear_history(self) -> None:
        """Clear the session history."""
        self.history.clear()
        self.updated_at = datetime.utcnow()

    def get_last_entry(self) -> Optional[Dict[str, Any]]:
        """Retrieve the last entry in the session history."""
        return self.history[-1] if self.history else None
