from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable


@dataclass(slots=True)
class AgentMetadata(dict):
    """Mapping-based metadata container for specialized agents."""

    def __getattr__(self, item: str) -> Any:
        try:
            return self[item]
        except KeyError as exc:  # pragma: no cover - defensive
            raise AttributeError(item) from exc

    def __setattr__(self, key: str, value: Any) -> None:
        if key.startswith("_"):
            super().__setattr__(key, value)
        else:
            self[key] = value

    def to_dict(self) -> dict[str, Any]:
        return dict(self)


@dataclass(slots=True)
class AgentProfile:
    name: str
    role: str
    description: str = ""
    version: str = "0.1.0"
    tags: list[str] = field(default_factory=list)
    capabilities: list[str] = field(default_factory=list)


@dataclass(slots=True)
class AgentConfiguration:
    name: str = ""
    enabled: bool = True
    auto_start: bool = False
    startup_timeout_seconds: float = 30.0
    metadata: AgentMetadata = field(default_factory=AgentMetadata)
    event_handlers: dict[str, list[Callable[..., Any]]] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "enabled": self.enabled,
            "auto_start": self.auto_start,
            "startup_timeout_seconds": self.startup_timeout_seconds,
            "metadata": dict(self.metadata),
        }


@dataclass(slots=True)
class AgentStatistics:
    tasks_received: int = 0
    tasks_completed: int = 0
    tasks_failed: int = 0
    messages_sent: int = 0
    messages_received: int = 0
    delegations: int = 0
    start_count: int = 0
    stop_count: int = 0


@dataclass(slots=True)
class AgentHealth:
    status: str = "initializing"
    message: str = ""
    details: dict[str, Any] = field(default_factory=dict)
    last_updated: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


__all__ = [
    "AgentConfiguration",
    "AgentHealth",
    "AgentMetadata",
    "AgentProfile",
    "AgentStatistics",
]
