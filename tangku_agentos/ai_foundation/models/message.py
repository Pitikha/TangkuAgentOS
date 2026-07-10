"""
AI Foundation Framework - Message Models

This module defines message models for AI conversations.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from typing import Any, Dict, List, Optional, Union


class MessageRole(Enum):
    """
    Roles for AI messages.
    
    Attributes:
        SYSTEM: System message (instructions, context).
        USER: User message (input, questions).
        ASSISTANT: Assistant message (AI output).
        TOOL: Tool message (tool output).
        FUNCTION: Function message (function output).
        DEVELOPER: Developer message (internal instructions).
        KERNEL: Kernel message (system-level instructions).
    """

    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"
    FUNCTION = "function"
    DEVELOPER = "developer"
    KERNEL = "kernel"


class MessageType(Enum):
    """
    Types of AI messages.
    
    Attributes:
        TEXT: Plain text message.
        IMAGE: Image message.
        AUDIO: Audio message.
        VIDEO: Video message.
        EMBEDDING: Embedding vector.
        TOOL_CALL: Tool/function call.
        TOOL_RESULT: Tool/function result.
        STRUCTURED: Structured data.
    """

    TEXT = "text"
    IMAGE = "image"
    AUDIO = "audio"
    VIDEO = "video"
    EMBEDDING = "embedding"
    TOOL_CALL = "tool_call"
    TOOL_RESULT = "tool_result"
    STRUCTURED = "structured"


@dataclass
class ContentPart:
    """
    Represents a part of a multi-part message content.
    
    Attributes:
        type: Type of content (text, image, audio, etc.).
        text: Text content.
        image_url: URL for image content.
        image_data: Base64-encoded image data.
        audio_url: URL for audio content.
        audio_data: Base64-encoded audio data.
        video_url: URL for video content.
        video_data: Base64-encoded video data.
        embedding: Embedding vector.
        metadata: Additional metadata.
    """

    type: MessageType = MessageType.TEXT
    text: Optional[str] = None
    image_url: Optional[str] = None
    image_data: Optional[str] = None
    audio_url: Optional[str] = None
    audio_data: Optional[str] = None
    video_url: Optional[str] = None
    video_data: Optional[str] = None
    embedding: Optional[List[float]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def is_text(self) -> bool:
        """Check if this is a text part."""
        return self.type == MessageType.TEXT and self.text is not None

    @property
    def is_image(self) -> bool:
        """Check if this is an image part."""
        return self.type == MessageType.IMAGE and (self.image_url is not None or self.image_data is not None)

    @property
    def is_audio(self) -> bool:
        """Check if this is an audio part."""
        return self.type == MessageType.AUDIO and (self.audio_url is not None or self.audio_data is not None)

    @property
    def is_video(self) -> bool:
        """Check if this is a video part."""
        return self.type == MessageType.VIDEO and (self.video_url is not None or self.video_data is not None)

    @property
    def is_embedding(self) -> bool:
        """Check if this is an embedding part."""
        return self.type == MessageType.EMBEDDING and self.embedding is not None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        result = {
            "type": self.type.value,
            "metadata": self.metadata,
        }
        
        if self.text is not None:
            result["text"] = self.text
        if self.image_url is not None:
            result["image_url"] = self.image_url
        if self.image_data is not None:
            result["image_data"] = self.image_data
        if self.audio_url is not None:
            result["audio_url"] = self.audio_url
        if self.audio_data is not None:
            result["audio_data"] = self.audio_data
        if self.video_url is not None:
            result["video_url"] = self.video_url
        if self.video_data is not None:
            result["video_data"] = self.video_data
        if self.embedding is not None:
            result["embedding"] = self.embedding
        
        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ContentPart":
        """Create from dictionary."""
        type_str = data.get("type", "text")
        try:
            type_ = MessageType(type_str)
        except ValueError:
            type_ = MessageType.TEXT

        return cls(
            type=type_,
            text=data.get("text"),
            image_url=data.get("image_url"),
            image_data=data.get("image_data"),
            audio_url=data.get("audio_url"),
            audio_data=data.get("audio_data"),
            video_url=data.get("video_url"),
            video_data=data.get("video_data"),
            embedding=data.get("embedding"),
            metadata=data.get("metadata", {}),
        )


@dataclass
class Message:
    """
    Represents a message in an AI conversation.
    
    Attributes:
        role: Role of the message sender.
        content: Content of the message (text or list of content parts).
        name: Optional name for the sender.
        tool_call_id: ID of the tool call this message is responding to.
        tool_calls: Tool calls made in this message.
        metadata: Additional metadata.
        created: Timestamp when the message was created.
        token_count: Number of tokens in the message.
    """

    role: MessageRole
    content: Union[str, List[ContentPart]] = ""
    name: Optional[str] = None
    tool_call_id: Optional[str] = None
    tool_calls: List[Dict[str, Any]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created: datetime = field(default_factory=datetime.utcnow)
    token_count: int = 0

    def __post_init__(self):
        """Post-initialization processing."""
        # Calculate token count if not provided
        if self.token_count == 0 and self.content:
            self._calculate_token_count()

    def _calculate_token_count(self) -> None:
        """Calculate the token count for this message."""
        if isinstance(self.content, str):
            # Simple token estimation: ~4 characters per token
            self.token_count = len(self.content) // 4
        elif isinstance(self.content, list):
            total = 0
            for part in self.content:
                if isinstance(part, ContentPart):
                    if part.is_text and part.text:
                        total += len(part.text) // 4
                    elif part.is_image:
                        # Estimate image tokens (varies by model)
                        total += 1000  # Rough estimate
                    elif part.is_audio:
                        # Estimate audio tokens
                        total += 1000  # Rough estimate
                    elif part.is_embedding:
                        # Embedding tokens
                        if part.embedding:
                            total += len(part.embedding) // 4
                elif isinstance(part, str):
                    total += len(part) // 4
            self.token_count = total

    @property
    def is_system(self) -> bool:
        """Check if this is a system message."""
        return self.role == MessageRole.SYSTEM

    @property
    def is_user(self) -> bool:
        """Check if this is a user message."""
        return self.role == MessageRole.USER

    @property
    def is_assistant(self) -> bool:
        """Check if this is an assistant message."""
        return self.role == MessageRole.ASSISTANT

    @property
    def is_tool(self) -> bool:
        """Check if this is a tool message."""
        return self.role == MessageRole.TOOL

    @property
    def has_tool_calls(self) -> bool:
        """Check if this message contains tool calls."""
        return len(self.tool_calls) > 0

    @property
    def is_multi_part(self) -> bool:
        """Check if this message has multi-part content."""
        return isinstance(self.content, list) and len(self.content) > 0

    def get_text(self) -> str:
        """Get the text content of the message."""
        if isinstance(self.content, str):
            return self.content
        elif isinstance(self.content, list):
            parts = []
            for part in self.content:
                if isinstance(part, ContentPart) and part.is_text and part.text:
                    parts.append(part.text)
                elif isinstance(part, str):
                    parts.append(part)
            return "".join(parts)
        return ""

    def get_content_parts(self) -> List[ContentPart]:
        """Get the content parts of the message."""
        if isinstance(self.content, list):
            parts = []
            for part in self.content:
                if isinstance(part, ContentPart):
                    parts.append(part)
                else:
                    parts.append(ContentPart(type=MessageType.TEXT, text=str(part)))
            return parts
        elif isinstance(self.content, str):
            return [ContentPart(type=MessageType.TEXT, text=self.content)]
        return []

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        content = self.content
        if isinstance(content, list):
            content = [part.to_dict() if isinstance(part, ContentPart) else part for part in content]
        
        return {
            "role": self.role.value,
            "content": content,
            "name": self.name,
            "tool_call_id": self.tool_call_id,
            "tool_calls": self.tool_calls,
            "metadata": self.metadata,
            "created": self.created.isoformat(),
            "token_count": self.token_count,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Message":
        """Create from dictionary."""
        role = MessageRole(data.get("role", "user"))
        
        content = data.get("content", "")
        if isinstance(content, list):
            content = [
                ContentPart.from_dict(part) if isinstance(part, dict) else part
                for part in content
            ]
        
        return cls(
            role=role,
            content=content,
            name=data.get("name"),
            tool_call_id=data.get("tool_call_id"),
            tool_calls=data.get("tool_calls", []),
            metadata=data.get("metadata", {}),
            token_count=data.get("token_count", 0),
        )

    def __repr__(self) -> str:
        """Return string representation."""
        content_preview = self.get_text()[:30] + "..." if len(self.get_text()) > 30 else self.get_text()
        return (
            f"Message("
            f"role={self.role.value}, "
            f"content={content_preview!r}, "
            f"tokens={self.token_count})"
        )
