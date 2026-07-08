"""
AI Cognitive System - Cognitive Input Model

This module defines the CognitiveInput model, which represents
input data for the cognitive system.

Author: TangkuAgentOS Team
License: MIT
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Union


class InputType(Enum):
    """
    Types of cognitive inputs.
    
    Attributes:
        TEXT: Plain text input.
        VOICE: Voice/audio input.
        IMAGE: Image input.
        DOCUMENT: Document input.
        REPOSITORY: Repository input.
        TERMINAL_OUTPUT: Terminal output input.
        RUNTIME_EVENT: Runtime event input.
        SYSTEM_EVENT: System event input.
        WORKSPACE_CHANGE: Workspace change input.
        SENSOR_EVENT: Sensor event input (future).
        MULTI_MODAL: Multi-modal input (combination of types).
        STRUCTURED: Structured data input.
        STREAM: Streaming input.
    """

    TEXT = "text"
    VOICE = "voice"
    IMAGE = "image"
    DOCUMENT = "document"
    REPOSITORY = "repository"
    TERMINAL_OUTPUT = "terminal_output"
    RUNTIME_EVENT = "runtime_event"
    SYSTEM_EVENT = "system_event"
    WORKSPACE_CHANGE = "workspace_change"
    SENSOR_EVENT = "sensor_event"
    MULTI_MODAL = "multi_modal"
    STRUCTURED = "structured"
    STREAM = "stream"


class InputPriority(Enum):
    """
    Priority levels for cognitive inputs.
    
    Attributes:
        CRITICAL: Critical priority (must be processed immediately).
        HIGH: High priority (should be processed soon).
        NORMAL: Normal priority (default).
        LOW: Low priority (can wait).
        BACKGROUND: Background priority (process when idle).
    """

    CRITICAL = "critical"
    HIGH = "high"
    NORMAL = "normal"
    LOW = "low"
    BACKGROUND = "background"


@dataclass
class InputMetadata:
    """
    Metadata for cognitive inputs.
    
    Attributes:
        input_id: Unique identifier for the input.
        timestamp: When the input was received.
        source: Source of the input.
        source_id: Identifier for the source.
        type: Type of input.
        priority: Priority of the input.
        session_id: Session identifier.
        conversation_id: Conversation identifier.
        user_id: User identifier.
        agent_id: Agent identifier.
        tags: Tags for categorization.
        metadata: Additional metadata.
    """

    input_id: str = ""
    timestamp: datetime = field(default_factory=datetime.utcnow)
    source: str = ""
    source_id: str = ""
    type: InputType = InputType.TEXT
    priority: InputPriority = InputPriority.NORMAL
    session_id: str = ""
    conversation_id: str = ""
    user_id: str = ""
    agent_id: str = ""
    tags: Set[str] = field(default_factory=set)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "input_id": self.input_id,
            "timestamp": self.timestamp.isoformat(),
            "source": self.source,
            "source_id": self.source_id,
            "type": self.type.value,
            "priority": self.priority.value,
            "session_id": self.session_id,
            "conversation_id": self.conversation_id,
            "user_id": self.user_id,
            "agent_id": self.agent_id,
            "tags": list(self.tags),
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "InputMetadata":
        """Create from dictionary."""
        return cls(
            input_id=data.get("input_id", ""),
            timestamp=datetime.fromisoformat(data.get("timestamp", datetime.utcnow().isoformat())),
            source=data.get("source", ""),
            source_id=data.get("source_id", ""),
            type=InputType(data.get("type", "text")),
            priority=InputPriority(data.get("priority", "normal")),
            session_id=data.get("session_id", ""),
            conversation_id=data.get("conversation_id", ""),
            user_id=data.get("user_id", ""),
            agent_id=data.get("agent_id", ""),
            tags=set(data.get("tags", [])),
            metadata=data.get("metadata", {}),
        )


@dataclass
class TextInput:
    """
    Text input for the cognitive system.
    
    Attributes:
        content: The text content.
        language: Language of the text.
        encoding: Text encoding.
        format: Text format (plain, markdown, html, etc.).
    """

    content: str = ""
    language: str = "en"
    encoding: str = "utf-8"
    format: str = "plain"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "content": self.content,
            "language": self.language,
            "encoding": self.encoding,
            "format": self.format,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TextInput":
        """Create from dictionary."""
        return cls(
            content=data.get("content", ""),
            language=data.get("language", "en"),
            encoding=data.get("encoding", "utf-8"),
            format=data.get("format", "plain"),
        )


@dataclass
class VoiceInput:
    """
    Voice/audio input for the cognitive system.
    
    Attributes:
        audio_data: Binary audio data.
        format: Audio format (wav, mp3, etc.).
        sample_rate: Sample rate in Hz.
        channels: Number of audio channels.
        duration: Duration in seconds.
        language: Language of the speech.
        transcript: Transcribed text (if available).
    """

    audio_data: bytes = b""
    format: str = "wav"
    sample_rate: int = 16000
    channels: int = 1
    duration: float = 0.0
    language: str = "en"
    transcript: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary (excluding binary data)."""
        return {
            "format": self.format,
            "sample_rate": self.sample_rate,
            "channels": self.channels,
            "duration": self.duration,
            "language": self.language,
            "transcript": self.transcript,
            "audio_data_size": len(self.audio_data),
        }


@dataclass
class ImageInput:
    """
    Image input for the cognitive system.
    
    Attributes:
        image_data: Binary image data.
        format: Image format (png, jpeg, etc.).
        width: Image width in pixels.
        height: Image height in pixels.
        channels: Number of color channels.
        description: Text description of the image.
        tags: Tags for the image.
    """

    image_data: bytes = b""
    format: str = "png"
    width: int = 0
    height: int = 0
    channels: int = 3
    description: str = ""
    tags: Set[str] = field(default_factory=set)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary (excluding binary data)."""
        return {
            "format": self.format,
            "width": self.width,
            "height": self.height,
            "channels": self.channels,
            "description": self.description,
            "tags": list(self.tags),
            "image_data_size": len(self.image_data),
        }


@dataclass
class DocumentInput:
    """
    Document input for the cognitive system.
    
    Attributes:
        content: Text content of the document.
        format: Document format (txt, md, pdf, etc.).
        filename: Name of the document file.
        path: Path to the document.
        url: URL of the document.
        metadata: Document metadata.
    """

    content: str = ""
    format: str = "txt"
    filename: str = ""
    path: str = ""
    url: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "content": self.content[:100] + "..." if len(self.content) > 100 else self.content,
            "format": self.format,
            "filename": self.filename,
            "path": self.path,
            "url": self.url,
            "metadata": self.metadata,
            "content_length": len(self.content),
        }


@dataclass
class RepositoryInput:
    """
    Repository input for the cognitive system.
    
    Attributes:
        repository_id: Unique identifier for the repository.
        name: Name of the repository.
        url: URL of the repository.
        path: Local path to the repository.
        branch: Branch name.
        commit: Commit hash.
        files: List of files in the repository.
        metadata: Repository metadata.
    """

    repository_id: str = ""
    name: str = ""
    url: str = ""
    path: str = ""
    branch: str = "main"
    commit: str = ""
    files: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "repository_id": self.repository_id,
            "name": self.name,
            "url": self.url,
            "path": self.path,
            "branch": self.branch,
            "commit": self.commit,
            "files": self.files,
            "metadata": self.metadata,
        }


@dataclass
class TerminalInput:
    """
    Terminal output input for the cognitive system.
    
    Attributes:
        command: The command that was executed.
        output: The output from the command.
        exit_code: Exit code of the command.
        working_directory: Working directory.
        timestamp: When the command was executed.
        session_id: Terminal session identifier.
    """

    command: str = ""
    output: str = ""
    exit_code: int = 0
    working_directory: str = ""
    timestamp: datetime = field(default_factory=datetime.utcnow)
    session_id: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "command": self.command,
            "output": self.output[:100] + "..." if len(self.output) > 100 else self.output,
            "exit_code": self.exit_code,
            "working_directory": self.working_directory,
            "timestamp": self.timestamp.isoformat(),
            "session_id": self.session_id,
            "output_length": len(self.output),
        }


@dataclass
class RuntimeEventInput:
    """
    Runtime event input for the cognitive system.
    
    Attributes:
        event_type: Type of the event.
        runtime_id: Identifier of the runtime.
        payload: Event payload.
        timestamp: When the event occurred.
        severity: Severity of the event.
    """

    event_type: str = ""
    runtime_id: str = ""
    payload: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow)
    severity: str = "info"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "event_type": self.event_type,
            "runtime_id": self.runtime_id,
            "payload": self.payload,
            "timestamp": self.timestamp.isoformat(),
            "severity": self.severity,
        }


@dataclass
class SystemEventInput:
    """
    System event input for the cognitive system.
    
    Attributes:
        event_type: Type of the event.
        payload: Event payload.
        timestamp: When the event occurred.
        severity: Severity of the event.
        source: Source of the event.
    """

    event_type: str = ""
    payload: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow)
    severity: str = "info"
    source: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "event_type": self.event_type,
            "payload": self.payload,
            "timestamp": self.timestamp.isoformat(),
            "severity": self.severity,
            "source": self.source,
        }


@dataclass
class WorkspaceChangeInput:
    """
    Workspace change input for the cognitive system.
    
    Attributes:
        change_type: Type of change (create, update, delete, move, etc.).
        path: Path to the changed item.
        old_path: Previous path (for moves/renames).
        content: Content of the changed item (if applicable).
        timestamp: When the change occurred.
        metadata: Additional metadata.
    """

    change_type: str = ""
    path: str = ""
    old_path: str = ""
    content: str = ""
    timestamp: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "change_type": self.change_type,
            "path": self.path,
            "old_path": self.old_path,
            "content": self.content[:100] + "..." if len(self.content) > 100 else self.content,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata,
            "content_length": len(self.content),
        }


@dataclass
class StructuredInput:
    """
    Structured data input for the cognitive system.
    
    Attributes:
        data: The structured data.
        schema: Schema for the data.
        format: Data format (json, yaml, xml, etc.).
    """

    data: Dict[str, Any] = field(default_factory=dict)
    schema: Optional[Dict[str, Any]] = None
    format: str = "json"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "data": self.data,
            "schema": self.schema,
            "format": self.format,
        }


@dataclass
class StreamInput:
    """
    Streaming input for the cognitive system.
    
    Attributes:
        stream_id: Unique identifier for the stream.
        data: Current chunk of data.
        sequence_number: Sequence number of the chunk.
        is_complete: Whether this is the final chunk.
        metadata: Stream metadata.
    """

    stream_id: str = ""
    data: Any = None
    sequence_number: int = 0
    is_complete: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "stream_id": self.stream_id,
            "data": str(self.data)[:100] + "..." if len(str(self.data)) > 100 else str(self.data),
            "sequence_number": self.sequence_number,
            "is_complete": self.is_complete,
            "metadata": self.metadata,
        }


@dataclass
class CognitiveInput:
    """
    Main input model for the cognitive system.
    
    This class represents input data for the cognitive system, supporting
    multiple input types and formats.
    
    Attributes:
        metadata: Input metadata.
        type: Type of input.
        data: The actual input data.
        raw_data: Raw input data (if different from processed data).
        processed: Whether the input has been processed.
        processing_time: Time taken to process the input.
    """

    metadata: InputMetadata = field(default_factory=InputMetadata)
    type: InputType = InputType.TEXT
    data: Any = None
    raw_data: Any = None
    processed: bool = False
    processing_time: float = 0.0

    def __post_init__(self):
        """Post-initialization validation."""
        if self.data is None:
            # Set default data based on type
            if self.type == InputType.TEXT:
                self.data = TextInput()
            elif self.type == InputType.VOICE:
                self.data = VoiceInput()
            elif self.type == InputType.IMAGE:
                self.data = ImageInput()
            elif self.type == InputType.DOCUMENT:
                self.data = DocumentInput()
            elif self.type == InputType.REPOSITORY:
                self.data = RepositoryInput()
            elif self.type == InputType.TERMINAL_OUTPUT:
                self.data = TerminalInput()
            elif self.type == InputType.RUNTIME_EVENT:
                self.data = RuntimeEventInput()
            elif self.type == InputType.SYSTEM_EVENT:
                self.data = SystemEventInput()
            elif self.type == InputType.WORKSPACE_CHANGE:
                self.data = WorkspaceChangeInput()
            elif self.type == InputType.STRUCTURED:
                self.data = StructuredInput()
            elif self.type == InputType.STREAM:
                self.data = StreamInput()

    @classmethod
    def from_text(
        cls,
        content: str,
        source: str = "user",
        conversation_id: str = "",
        **kwargs,
    ) -> "CognitiveInput":
        """
        Create a text input.
        
        Args:
            content: Text content.
            source: Source of the input.
            conversation_id: Conversation identifier.
            **kwargs: Additional metadata.
        
        Returns:
            CognitiveInput instance.
        """
        metadata = InputMetadata(
            source=source,
            conversation_id=conversation_id,
            type=InputType.TEXT,
            **kwargs,
        )
        return cls(
            metadata=metadata,
            type=InputType.TEXT,
            data=TextInput(content=content),
        )

    @classmethod
    def from_dict_data(
        cls,
        data: Dict[str, Any],
        source: str = "user",
        conversation_id: str = "",
        **kwargs,
    ) -> "CognitiveInput":
        """
        Create an input from dictionary data.
        
        Args:
            data: Dictionary data.
            source: Source of the input.
            conversation_id: Conversation identifier.
            **kwargs: Additional metadata.
        
        Returns:
            CognitiveInput instance.
        """
        metadata = InputMetadata(
            source=source,
            conversation_id=conversation_id,
            type=InputType.STRUCTURED,
            **kwargs,
        )
        return cls(
            metadata=metadata,
            type=InputType.STRUCTURED,
            data=StructuredInput(data=data),
        )

    @classmethod
    def from_event(
        cls,
        event_type: str,
        payload: Dict[str, Any],
        source: str = "system",
        **kwargs,
    ) -> "CognitiveInput":
        """
        Create an input from an event.
        
        Args:
            event_type: Type of the event.
            payload: Event payload.
            source: Source of the input.
            **kwargs: Additional metadata.
        
        Returns:
            CognitiveInput instance.
        """
        metadata = InputMetadata(
            source=source,
            type=InputType.SYSTEM_EVENT,
            **kwargs,
        )
        return cls(
            metadata=metadata,
            type=InputType.SYSTEM_EVENT,
            data=SystemEventInput(
                event_type=event_type,
                payload=payload,
            ),
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        data_dict = {}
        if hasattr(self.data, 'to_dict'):
            data_dict = self.data.to_dict()
        else:
            data_dict = {"data": str(self.data)}
        
        return {
            "metadata": self.metadata.to_dict(),
            "type": self.type.value,
            "data": data_dict,
            "raw_data": str(self.raw_data)[:100] + "..." if self.raw_data and len(str(self.raw_data)) > 100 else str(self.raw_data),
            "processed": self.processed,
            "processing_time": self.processing_time,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CognitiveInput":
        """Create from dictionary."""
        metadata = InputMetadata.from_dict(data.get("metadata", {}))
        input_type = InputType(data.get("type", "text"))
        
        # Create appropriate data object based on type
        input_data = None
        if "data" in data:
            type_data = data["data"]
            if input_type == InputType.TEXT:
                input_data = TextInput.from_dict(type_data)
            elif input_type == InputType.VOICE:
                input_data = VoiceInput()  # Simplified
            elif input_type == InputType.IMAGE:
                input_data = ImageInput()  # Simplified
            elif input_type == InputType.DOCUMENT:
                input_data = DocumentInput.from_dict(type_data)
            elif input_type == InputType.REPOSITORY:
                input_data = RepositoryInput.from_dict(type_data)
            elif input_type == InputType.TERMINAL_OUTPUT:
                input_data = TerminalInput.from_dict(type_data)
            elif input_type == InputType.RUNTIME_EVENT:
                input_data = RuntimeEventInput.from_dict(type_data)
            elif input_type == InputType.SYSTEM_EVENT:
                input_data = SystemEventInput.from_dict(type_data)
            elif input_type == InputType.WORKSPACE_CHANGE:
                input_data = WorkspaceChangeInput.from_dict(type_data)
            elif input_type == InputType.STRUCTURED:
                input_data = StructuredInput.from_dict(type_data)
            elif input_type == InputType.STREAM:
                input_data = StreamInput.from_dict(type_data)
        
        return cls(
            metadata=metadata,
            type=input_type,
            data=input_data,
            raw_data=data.get("raw_data"),
            processed=data.get("processed", False),
            processing_time=data.get("processing_time", 0.0),
        )

    def __repr__(self) -> str:
        """Return string representation."""
        data_str = str(self.data)[:50] + "..." if len(str(self.data)) > 50 else str(self.data)
        return (
            f"CognitiveInput("
            f"type={self.type.value}, "
            f"source={self.metadata.source}, "
            f"data={data_str})"
        )
