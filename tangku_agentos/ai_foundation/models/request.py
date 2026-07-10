"""
AI Foundation Framework - Request Models

This module defines request models for AI operations.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from typing import Any, Dict, List, Optional, Set, Union, TYPE_CHECKING

if TYPE_CHECKING:
    from tangku_agentos.ai_foundation.models.message import Message


class RequestPriority(Enum):
    """Priority levels for AI requests."""
    LOW = auto()
    NORMAL = auto()
    HIGH = auto()
    CRITICAL = auto()


class ResponseFormat(Enum):
    """Response format options."""
    TEXT = auto()
    JSON = auto()
    JSON_SCHEMA = auto()
    XML = auto()
    YAML = auto()
    MARKDOWN = auto()
    HTML = auto()


@dataclass
class AIRequest:
    """
    Represents a request to an AI model.
    
    Attributes:
        messages: List of messages for chat models.
        prompt: Prompt for completion models.
        model: Model to use.
        provider: Provider to use.
        session_id: Session ID.
        conversation_id: Conversation ID.
        context: Additional context for the request.
        max_tokens: Maximum tokens to generate.
        temperature: Sampling temperature.
        top_p: Top-p sampling.
        top_k: Top-k sampling.
        stop_sequences: Stop sequences for generation.
        stream: Whether to stream the response.
        response_format: Format for the response.
        response_schema: Schema for structured response.
        use_tools: Whether to use tool calling.
        tools: Available tools for tool calling.
        tool_choice: Tool choice strategy.
        use_memory: Whether to use memory retrieval.
        use_knowledge: Whether to use knowledge retrieval.
        use_reasoning: Whether to use reasoning.
        use_planning: Whether to use planning.
        use_cache: Whether to use caching.
        cache_key: Custom cache key.
        priority: Request priority.
        timeout: Request timeout in seconds.
        max_retries: Maximum number of retries.
        retry_delay: Delay between retries in seconds.
        metadata: Additional metadata.
        created: Timestamp when the request was created.
    """

    messages: List["Message"] = field(default_factory=list)
    prompt: Optional[str] = None
    model: Optional[str] = None
    provider: Optional[str] = None
    session_id: Optional[str] = None
    conversation_id: Optional[str] = None
    context: Dict[str, Any] = field(default_factory=dict)
    max_tokens: int = 1000
    temperature: float = 0.7
    top_p: float = 0.9
    top_k: int = 50
    stop_sequences: List[str] = field(default_factory=list)
    stream: bool = False
    response_format: Optional[ResponseFormat] = None
    response_schema: Optional[Dict[str, Any]] = None
    use_tools: bool = False
    tools: List[Dict[str, Any]] = field(default_factory=list)
    tool_choice: str = "auto"  # auto, none, required
    use_memory: bool = True
    use_knowledge: bool = True
    use_reasoning: bool = True
    use_planning: bool = True
    use_cache: bool = True
    cache_key: Optional[str] = None
    priority: RequestPriority = RequestPriority.NORMAL
    timeout: float = 30.0
    max_retries: int = 3
    retry_delay: float = 1.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    created: datetime = field(default_factory=datetime.utcnow)
    
    # Computed properties
    _input_tokens: Optional[int] = field(default=None, repr=False)

    @property
    def input_tokens(self) -> int:
        """Get the number of input tokens."""
        if self._input_tokens is not None:
            return self._input_tokens
        
        # Calculate input tokens
        tokens = 0
        
        # Count tokens in messages
        for message in self.messages:
            tokens += message.token_count
        
        # Count tokens in prompt
        if self.prompt:
            # Simple token estimation: ~4 characters per token
            tokens += len(self.prompt) // 4
        
        # Count tokens in context
        for key, value in self.context.items():
            if isinstance(value, str):
                tokens += len(value) // 4
            elif isinstance(value, dict):
                tokens += len(str(value)) // 4
        
        self._input_tokens = tokens
        return tokens

    @property
    def is_chat(self) -> bool:
        """Check if this is a chat request."""
        return len(self.messages) > 0

    @property
    def is_completion(self) -> bool:
        """Check if this is a completion request."""
        return self.prompt is not None and len(self.messages) == 0

    @property
    def requires_tools(self) -> bool:
        """Check if this request requires tools."""
        return self.use_tools and len(self.tools) > 0

    @property
    def requires_structured_output(self) -> bool:
        """Check if this request requires structured output."""
        return self.response_format is not None or self.response_schema is not None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "messages": [m.to_dict() for m in self.messages],
            "prompt": self.prompt,
            "model": self.model,
            "provider": self.provider,
            "session_id": self.session_id,
            "conversation_id": self.conversation_id,
            "context": self.context,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
            "top_p": self.top_p,
            "top_k": self.top_k,
            "stop_sequences": self.stop_sequences,
            "stream": self.stream,
            "response_format": self.response_format.value if self.response_format else None,
            "response_schema": self.response_schema,
            "use_tools": self.use_tools,
            "tools": self.tools,
            "tool_choice": self.tool_choice,
            "use_memory": self.use_memory,
            "use_knowledge": self.use_knowledge,
            "use_reasoning": self.use_reasoning,
            "use_planning": self.use_planning,
            "use_cache": self.use_cache,
            "cache_key": self.cache_key,
            "priority": self.priority.value,
            "timeout": self.timeout,
            "max_retries": self.max_retries,
            "retry_delay": self.retry_delay,
            "metadata": self.metadata,
            "created": self.created.isoformat(),
            "input_tokens": self.input_tokens,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AIRequest":
        """Create from dictionary."""
        from tangku_agentos.ai_foundation.models.message import Message
        
        priority = RequestPriority.NORMAL
        if "priority" in data and data["priority"]:
            try:
                priority = RequestPriority(data["priority"])
            except ValueError:
                pass

        response_format = None
        if "response_format" in data and data["response_format"]:
            try:
                response_format = ResponseFormat(data["response_format"])
            except ValueError:
                pass

        return cls(
            messages=[Message.from_dict(m) for m in data.get("messages", [])],
            prompt=data.get("prompt"),
            model=data.get("model"),
            provider=data.get("provider"),
            session_id=data.get("session_id"),
            conversation_id=data.get("conversation_id"),
            context=data.get("context", {}),
            max_tokens=data.get("max_tokens", 1000),
            temperature=data.get("temperature", 0.7),
            top_p=data.get("top_p", 0.9),
            top_k=data.get("top_k", 50),
            stop_sequences=data.get("stop_sequences", []),
            stream=data.get("stream", False),
            response_format=response_format,
            response_schema=data.get("response_schema"),
            use_tools=data.get("use_tools", False),
            tools=data.get("tools", []),
            tool_choice=data.get("tool_choice", "auto"),
            use_memory=data.get("use_memory", True),
            use_knowledge=data.get("use_knowledge", True),
            use_reasoning=data.get("use_reasoning", True),
            use_planning=data.get("use_planning", True),
            use_cache=data.get("use_cache", True),
            cache_key=data.get("cache_key"),
            priority=priority,
            timeout=data.get("timeout", 30.0),
            max_retries=data.get("max_retries", 3),
            retry_delay=data.get("retry_delay", 1.0),
            metadata=data.get("metadata", {}),
        )

    def __repr__(self) -> str:
        """Return string representation."""
        model_str = f"model={self.model}" if self.model else ""
        prompt_str = f"prompt={self.prompt[:20]!r}..." if self.prompt and len(self.prompt) > 20 else f"prompt={self.prompt!r}"
        messages_str = f"messages={len(self.messages)}" if self.messages else ""
        
        parts = []
        if model_str:
            parts.append(model_str)
        if prompt_str:
            parts.append(prompt_str)
        if messages_str:
            parts.append(messages_str)
        
        return f"AIRequest({', '.join(parts)})"
