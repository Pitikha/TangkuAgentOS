from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List


class ContextSource(Enum):
    CONVERSATION = "conversation"
    AGENT_STATE = "agent_state"
    WORKFLOW_STATE = "workflow_state"
    WORKSPACE = "workspace"
    MEMORY = "memory"
    KNOWLEDGE = "knowledge"
    DOCUMENT = "document"
    TASK = "task"
    CAPABILITY = "capability"
    CONFIGURATION = "configuration"
    USER_PREFERENCES = "user_preferences"
    POLICY = "policy"
    TOOL_OUTPUT = "tool_output"


class ContextPriority(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass(frozen=True)
class ContextMetadata:
    source: ContextSource
    timestamp: str = ""
    segment_id: str = ""
    attributes: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ContextConfiguration:
    max_tokens: int = 4096
    compression_enabled: bool = True
    optimizer_enabled: bool = True
    retention_days: int = 30
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ContextBudget:
    max_tokens: int = 4096
    reserved_tokens: int = 256
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ContextSession:
    session_id: str
    context_ids: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ContextSegment:
    segment_id: str
    content: str
    source: ContextSource
    priority: ContextPriority = ContextPriority.MEDIUM
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ContextReference:
    reference_id: str
    source: ContextSource
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ContextStatistics:
    token_count: int = 0
    segment_count: int = 0
    source_counts: Dict[ContextSource, int] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ContextObject:
    context_id: str
    segments: List[ContextSegment] = field(default_factory=list)
    references: List[ContextReference] = field(default_factory=list)
    priority: ContextPriority = ContextPriority.MEDIUM
    statistics: ContextStatistics = field(default_factory=ContextStatistics)
    configuration: ContextConfiguration = field(default_factory=ContextConfiguration)
    metadata: Dict[str, Any] = field(default_factory=dict)
