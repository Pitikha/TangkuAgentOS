"""
AI Foundation Framework - AI Context

This module defines the AIContext class for managing AI context.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from typing import Any, Dict, List, Optional


class ContextSource(Enum):
    """Source of context information."""
    CONVERSATION = auto()
    MEMORY = auto()
    KNOWLEDGE = auto()
    WORKSPACE = auto()
    REPOSITORY = auto()
    TERMINAL = auto()
    SYSTEM = auto()
    RUNTIME = auto()
    USER = auto()
    CUSTOM = auto()


@dataclass
class ContextEntry:
    """
    Represents a single entry in the AI context.
    
    Attributes:
        key: Key for the context entry.
        value: Value of the context entry.
        source: Source of the context entry.
        priority: Priority of the context entry (higher = more important).
        timestamp: When the context entry was created.
        metadata: Additional metadata.
    """

    key: str
    value: Any
    source: ContextSource = ContextSource.CUSTOM
    priority: int = 0
    timestamp: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "key": self.key,
            "value": self.value,
            "source": self.source.value,
            "priority": self.priority,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ContextEntry":
        """Create from dictionary."""
        source = ContextSource.CUSTOM
        if "source" in data and data["source"]:
            try:
                source = ContextSource(data["source"])
            except ValueError:
                pass

        return cls(
            key=data.get("key", ""),
            value=data.get("value"),
            source=source,
            priority=data.get("priority", 0),
            metadata=data.get("metadata", {}),
        )


@dataclass
class AIContext:
    """
    Represents the context for an AI operation.
    
    The AIContext class collects and manages all context information
    that is relevant to an AI operation, including conversation history,
    memory, knowledge, workspace state, and more.
    
    Attributes:
        entries: Dictionary of context entries by key.
        sources: Set of context sources that contributed to this context.
        timestamp: When the context was created.
        metadata: Additional metadata.
    """

    entries: Dict[str, ContextEntry] = field(default_factory=dict)
    sources: Set[ContextSource] = field(default_factory=set)
    timestamp: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def add_entry(self, entry: ContextEntry) -> None:
        """Add a context entry."""
        self.entries[entry.key] = entry
        self.sources.add(entry.source)

    def add(self, key: str, value: Any, source: ContextSource = ContextSource.CUSTOM, 
            priority: int = 0, metadata: Optional[Dict[str, Any]] = None) -> None:
        """
        Add a context entry with the given parameters.
        
        Args:
            key: Key for the context entry.
            value: Value of the context entry.
            source: Source of the context entry.
            priority: Priority of the context entry.
            metadata: Additional metadata.
        """
        entry = ContextEntry(
            key=key,
            value=value,
            source=source,
            priority=priority,
            metadata=metadata or {},
        )
        self.add_entry(entry)

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a context entry by key.
        
        Args:
            key: Key of the context entry.
            default: Default value if key not found.
        
        Returns:
            Value of the context entry or default.
        """
        entry = self.entries.get(key)
        return entry.value if entry else default

    def get_entry(self, key: str) -> Optional[ContextEntry]:
        """
        Get a context entry by key.
        
        Args:
            key: Key of the context entry.
        
        Returns:
            ContextEntry or None if not found.
        """
        return self.entries.get(key)

    def remove(self, key: str) -> bool:
        """
        Remove a context entry by key.
        
        Args:
            key: Key of the context entry to remove.
        
        Returns:
            True if entry was removed, False if not found.
        """
        if key in self.entries:
            del self.entries[key]
            return True
        return False

    def has(self, key: str) -> bool:
        """
        Check if a context entry exists.
        
        Args:
            key: Key of the context entry.
        
        Returns:
            True if entry exists, False otherwise.
        """
        return key in self.entries

    def has_source(self, source: ContextSource) -> bool:
        """
        Check if context has entries from a specific source.
        
        Args:
            source: Source to check.
        
        Returns:
            True if context has entries from the source, False otherwise.
        """
        return source in self.sources

    def get_by_source(self, source: ContextSource) -> Dict[str, Any]:
        """
        Get all context entries from a specific source.
        
        Args:
            source: Source to filter by.
        
        Returns:
            Dictionary of context entries from the source.
        """
        return {k: v.value for k, v in self.entries.items() if v.source == source}

    def clear(self) -> None:
        """Clear all context entries."""
        self.entries.clear()
        self.sources.clear()

    def clear_source(self, source: ContextSource) -> None:
        """
        Clear all context entries from a specific source.
        
        Args:
            source: Source to clear.
        """
        keys_to_remove = [k for k, v in self.entries.items() if v.source == source]
        for key in keys_to_remove:
            del self.entries[key]
        self.sources.discard(source)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "entries": {k: v.to_dict() for k, v in self.entries.items()},
            "sources": [s.value for s in self.sources],
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AIContext":
        """Create from dictionary."""
        context = cls()
        
        for key, entry_data in data.get("entries", {}).items():
            entry = ContextEntry.from_dict(entry_data)
            context.add_entry(entry)
        
        for source in data.get("sources", []):
            try:
                context.sources.add(ContextSource(source))
            except ValueError:
                pass
        
        if "timestamp" in data:
            context.timestamp = datetime.fromisoformat(data["timestamp"])
        
        context.metadata = data.get("metadata", {})
        
        return context

    def to_prompt(self, template: Optional[str] = None) -> str:
        """
        Convert context to a prompt string.
        
        Args:
            template: Optional template for formatting the context.
        
        Returns:
            Prompt string representation of the context.
        """
        if template:
            # Use template with context entries
            prompt = template
            for key, entry in self.entries.items():
                placeholder = f"{{{key}}}"
                if placeholder in prompt:
                    prompt = prompt.replace(placeholder, str(entry.value))
            return prompt
        
        # Default: concatenate all values
        parts = []
        for entry in sorted(self.entries.values(), key=lambda e: e.priority, reverse=True):
            parts.append(f"{entry.key}: {entry.value}")
        return "\n".join(parts)

    def __len__(self) -> int:
        """Get the number of context entries."""
        return len(self.entries)

    def __iter__(self):
        """Iterate over context entries."""
        return iter(self.entries.values())

    def __getitem__(self, key: str) -> Any:
        """Get a context entry by key."""
        return self.get(key)

    def __setitem__(self, key: str, value: Any) -> None:
        """Set a context entry."""
        self.add(key, value)

    def __delitem__(self, key: str) -> None:
        """Delete a context entry."""
        self.remove(key)

    def __contains__(self, key: str) -> bool:
        """Check if a context entry exists."""
        return self.has(key)

    def __repr__(self) -> str:
        """Return string representation."""
        return f"AIContext(entries={len(self.entries)}, sources={len(self.sources)})"
