"""
AI Foundation Framework - Response Models

This module defines response models for AI operations.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from typing import Any, Dict, List, Optional, Union, TYPE_CHECKING

if TYPE_CHECKING:
    from tangku_agentos.ai_foundation.models.model import AIModel


class ResponseStatus(Enum):
    """Status of an AI response."""
    PENDING = auto()
    PROCESSING = auto()
    COMPLETED = auto()
    PARTIAL = auto()
    ERROR = auto()
    TIMEOUT = auto()
    CANCELLED = auto()


class FinishReason(Enum):
    """Reason why the response finished."""
    STOP = auto()
    LENGTH = auto()
    CONTENT_FILTER = auto()
    TOOL_CALLS = auto()
    FUNCTION_CALL = auto()
    ERROR = auto()
    UNKNOWN = auto()


@dataclass
class Usage:
    """
    Token usage information for an AI response.
    
    Attributes:
        input_tokens: Number of tokens in the input.
        output_tokens: Number of tokens in the output.
        total_tokens: Total number of tokens (input + output).
        embedding_tokens: Number of tokens used for embeddings.
        image_tokens: Number of tokens used for images.
        audio_tokens: Number of tokens used for audio.
    """

    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0
    embedding_tokens: int = 0
    image_tokens: int = 0
    audio_tokens: int = 0

    @property
    def total(self) -> int:
        """Get total token count."""
        return self.input_tokens + self.output_tokens + self.embedding_tokens + self.image_tokens + self.audio_tokens

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "total_tokens": self.total_tokens,
            "embedding_tokens": self.embedding_tokens,
            "image_tokens": self.image_tokens,
            "audio_tokens": self.audio_tokens,
            "total": self.total,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Usage":
        """Create from dictionary."""
        return cls(
            input_tokens=data.get("input_tokens", 0),
            output_tokens=data.get("output_tokens", 0),
            total_tokens=data.get("total_tokens", 0),
            embedding_tokens=data.get("embedding_tokens", 0),
            image_tokens=data.get("image_tokens", 0),
            audio_tokens=data.get("audio_tokens", 0),
        )


@dataclass
class ToolCall:
    """
    Represents a tool/function call in an AI response.
    
    Attributes:
        id: Unique identifier for the tool call.
        type: Type of tool call (function, etc.).
        name: Name of the tool/function to call.
        arguments: Arguments for the tool/function.
        function: Function definition (if available).
    """

    id: str
    type: str = "function"
    name: str = ""
    arguments: str = ""
    function: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "type": self.type,
            "name": self.name,
            "arguments": self.arguments,
            "function": self.function,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ToolCall":
        """Create from dictionary."""
        return cls(
            id=data.get("id", ""),
            type=data.get("type", "function"),
            name=data.get("name", ""),
            arguments=data.get("arguments", ""),
            function=data.get("function"),
        )


@dataclass
class ToolResult:
    """
    Represents the result of a tool call.
    
    Attributes:
        tool_call_id: ID of the tool call this result corresponds to.
        content: Result content.
        role: Role of the result (typically "tool").
    """

    tool_call_id: str
    content: Any = None
    role: str = "tool"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "tool_call_id": self.tool_call_id,
            "content": self.content,
            "role": self.role,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ToolResult":
        """Create from dictionary."""
        return cls(
            tool_call_id=data.get("tool_call_id", ""),
            content=data.get("content"),
            role=data.get("role", "tool"),
        )


@dataclass
class StreamChunk:
    """
    Represents a chunk of a streaming AI response.
    
    Attributes:
        id: Unique identifier for the chunk.
        content: Text content of the chunk.
        role: Role of the message (assistant, tool, etc.).
        finish_reason: Reason why the stream finished (if applicable).
        usage: Token usage (if available).
        model: Model that generated the chunk.
        created: Timestamp when the chunk was created.
    """

    id: str
    content: str = ""
    role: str = "assistant"
    finish_reason: Optional[FinishReason] = None
    usage: Optional[Usage] = None
    model: Optional[str] = None
    created: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "content": self.content,
            "role": self.role,
            "finish_reason": self.finish_reason.value if self.finish_reason else None,
            "usage": self.usage.to_dict() if self.usage else None,
            "model": self.model,
            "created": self.created.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "StreamChunk":
        """Create from dictionary."""
        finish_reason = None
        if "finish_reason" in data and data["finish_reason"]:
            try:
                finish_reason = FinishReason(data["finish_reason"])
            except ValueError:
                pass

        return cls(
            id=data.get("id", ""),
            content=data.get("content", ""),
            role=data.get("role", "assistant"),
            finish_reason=finish_reason,
            usage=Usage.from_dict(data.get("usage", {})) if data.get("usage") else None,
            model=data.get("model"),
            created=datetime.fromisoformat(data.get("created", datetime.utcnow().isoformat())),
        )


@dataclass
class AIResponse:
    """
    Represents a complete AI response.
    
    Attributes:
        id: Unique identifier for the response.
        content: Text content of the response.
        role: Role of the response (assistant, tool, etc.).
        model: Model that generated the response.
        provider: Provider that generated the response.
        finish_reason: Reason why the response finished.
        usage: Token usage information.
        tool_calls: Tool calls made during generation.
        tool_results: Results from tool calls.
        status: Status of the response.
        error: Error message (if applicable).
        created: Timestamp when the response was created.
        metadata: Additional metadata.
    """

    id: str
    content: str = ""
    role: str = "assistant"
    model: Optional[str] = None
    provider: Optional[str] = None
    finish_reason: Optional[FinishReason] = None
    usage: Usage = field(default_factory=Usage)
    tool_calls: List[ToolCall] = field(default_factory=list)
    tool_results: List[ToolResult] = field(default_factory=list)
    status: ResponseStatus = ResponseStatus.COMPLETED
    error: Optional[str] = None
    created: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def input_tokens(self) -> int:
        """Get input token count."""
        return self.usage.input_tokens

    @property
    def output_tokens(self) -> int:
        """Get output token count."""
        return self.usage.output_tokens

    @property
    def total_tokens(self) -> int:
        """Get total token count."""
        return self.usage.total

    def has_tool_calls(self) -> bool:
        """Check if the response contains tool calls."""
        return len(self.tool_calls) > 0

    def has_tool_results(self) -> bool:
        """Check if the response contains tool results."""
        return len(self.tool_results) > 0

    def has_error(self) -> bool:
        """Check if the response contains an error."""
        return self.error is not None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "content": self.content,
            "role": self.role,
            "model": self.model,
            "provider": self.provider,
            "finish_reason": self.finish_reason.value if self.finish_reason else None,
            "usage": self.usage.to_dict(),
            "tool_calls": [tc.to_dict() for tc in self.tool_calls],
            "tool_results": [tr.to_dict() for tr in self.tool_results],
            "status": self.status.value,
            "error": self.error,
            "created": self.created.isoformat(),
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AIResponse":
        """Create from dictionary."""
        finish_reason = None
        if "finish_reason" in data and data["finish_reason"]:
            try:
                finish_reason = FinishReason(data["finish_reason"])
            except ValueError:
                pass

        status = ResponseStatus.COMPLETED
        if "status" in data and data["status"]:
            try:
                status = ResponseStatus(data["status"])
            except ValueError:
                pass

        return cls(
            id=data.get("id", ""),
            content=data.get("content", ""),
            role=data.get("role", "assistant"),
            model=data.get("model"),
            provider=data.get("provider"),
            finish_reason=finish_reason,
            usage=Usage.from_dict(data.get("usage", {})),
            tool_calls=[ToolCall.from_dict(tc) for tc in data.get("tool_calls", [])],
            tool_results=[ToolResult.from_dict(tr) for tr in data.get("tool_results", [])],
            status=status,
            error=data.get("error"),
            metadata=data.get("metadata", {}),
        )

    def __repr__(self) -> str:
        """Return string representation."""
        content_preview = self.content[:50] + "..." if len(self.content) > 50 else self.content
        return (
            f"AIResponse("
            f"id={self.id}, "
            f"model={self.model}, "
            f"status={self.status.value}, "
            f"content={content_preview!r}, "
            f"tokens={self.total_tokens})"
        )
