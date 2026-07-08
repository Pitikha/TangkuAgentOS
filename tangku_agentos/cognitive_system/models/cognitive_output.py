"""
AI Cognitive System - Cognitive Output Model

This module defines the CognitiveOutput model, which represents
output data from the cognitive system.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Union


class OutputType(Enum):
    TEXT = "text"
    VOICE = "voice"
    IMAGE = "image"
    DOCUMENT = "document"
    STRUCTURED = "structured"
    ACTION = "action"
    DECISION = "decision"
    PLAN = "plan"
    REASONING = "reasoning"
    MULTI_MODAL = "multi_modal"
    STREAM = "stream"


class OutputStatus(Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    PARTIAL = "partial"
    ERROR = "error"
    TIMEOUT = "timeout"


@dataclass
class OutputMetadata:
    output_id: str = ""
    timestamp: datetime = field(default_factory=datetime.utcnow)
    agent_id: str = ""
    session_id: str = ""
    conversation_id: str = ""
    user_id: str = ""
    type: OutputType = OutputType.TEXT
    status: OutputStatus = OutputStatus.PENDING
    confidence: float = 0.0
    processing_time: float = 0.0
    tags: Set[str] = field(default_factory=set)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "output_id": self.output_id,
            "timestamp": self.timestamp.isoformat(),
            "agent_id": self.agent_id,
            "session_id": self.session_id,
            "conversation_id": self.conversation_id,
            "user_id": self.user_id,
            "type": self.type.value,
            "status": self.status.value,
            "confidence": self.confidence,
            "processing_time": self.processing_time,
            "tags": list(self.tags),
            "metadata": self.metadata,
        }


@dataclass
class TextOutput:
    content: str = ""
    language: str = "en"
    format: str = "markdown"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "content": self.content,
            "language": self.language,
            "format": self.format,
        }


@dataclass
class VoiceOutput:
    audio_data: bytes = b""
    format: str = "wav"
    sample_rate: int = 16000
    channels: int = 1
    language: str = "en"
    transcript: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "format": self.format,
            "sample_rate": self.sample_rate,
            "channels": self.channels,
            "language": self.language,
            "transcript": self.transcript,
            "audio_data_size": len(self.audio_data),
        }


@dataclass
class StructuredOutput:
    data: Dict[str, Any] = field(default_factory=dict)
    schema: Optional[Dict[str, Any]] = None
    format: str = "json"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "data": self.data,
            "schema": self.schema,
            "format": self.format,
        }


@dataclass
class ActionOutput:
    action_type: str = ""
    target: str = ""
    parameters: Dict[str, Any] = field(default_factory=dict)
    result: Any = None
    success: bool = False
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "action_type": self.action_type,
            "target": self.target,
            "parameters": self.parameters,
            "result": str(self.result)[:100] + "..." if self.result and len(str(self.result)) > 100 else str(self.result),
            "success": self.success,
            "error": self.error,
        }


@dataclass
class DecisionOutput:
    decision: Any = None
    options: List[Any] = field(default_factory=list)
    selected_option: Any = None
    reasoning: str = ""
    confidence: float = 0.0
    utility: float = 0.0
    risk: float = 0.0
    cost: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "decision": str(self.decision)[:100] + "..." if self.decision and len(str(self.decision)) > 100 else str(self.decision),
            "options": [str(o)[:50] + "..." if len(str(o)) > 50 else str(o) for o in self.options],
            "selected_option": str(self.selected_option)[:100] + "..." if self.selected_option and len(str(self.selected_option)) > 100 else str(self.selected_option),
            "reasoning": self.reasoning[:200] + "..." if len(self.reasoning) > 200 else self.reasoning,
            "confidence": self.confidence,
            "utility": self.utility,
            "risk": self.risk,
            "cost": self.cost,
        }


@dataclass
class PlanOutput:
    goal: str = ""
    steps: List[Dict[str, Any]] = field(default_factory=list)
    dependencies: Dict[str, List[str]] = field(default_factory=dict)
    resources: Dict[str, Any] = field(default_factory=dict)
    timeline: Dict[str, Any] = field(default_factory=dict)
    confidence: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "goal": self.goal,
            "steps": self.steps,
            "dependencies": self.dependencies,
            "resources": self.resources,
            "timeline": self.timeline,
            "confidence": self.confidence,
        }


@dataclass
class ReasoningOutput:
    reasoning_type: str = ""
    steps: List[Dict[str, Any]] = field(default_factory=list)
    intermediate_results: List[Any] = field(default_factory=list)
    final_result: Any = None
    confidence: float = 0.0
    sources: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "reasoning_type": self.reasoning_type,
            "steps": self.steps,
            "intermediate_results": [str(r)[:50] + "..." if len(str(r)) > 50 else str(r) for r in self.intermediate_results],
            "final_result": str(self.final_result)[:100] + "..." if self.final_result and len(str(self.final_result)) > 100 else str(self.final_result),
            "confidence": self.confidence,
            "sources": self.sources,
        }


@dataclass
class CognitiveOutput:
    metadata: OutputMetadata = field(default_factory=OutputMetadata)
    type: OutputType = OutputType.TEXT
    data: Any = None
    raw_data: Any = None
    confidence: float = 0.0
    reasoning: Optional[str] = None
    sources: List[str] = field(default_factory=list)
    related_memories: List[str] = field(default_factory=list)
    related_knowledge: List[str] = field(default_factory=list)

    def __post_init__(self):
        if self.data is None:
            if self.type == OutputType.TEXT:
                self.data = TextOutput()
            elif self.type == OutputType.VOICE:
                self.data = VoiceOutput()
            elif self.type == OutputType.STRUCTURED:
                self.data = StructuredOutput()
            elif self.type == OutputType.ACTION:
                self.data = ActionOutput()
            elif self.type == OutputType.DECISION:
                self.data = DecisionOutput()
            elif self.type == OutputType.PLAN:
                self.data = PlanOutput()
            elif self.type == OutputType.REASONING:
                self.data = ReasoningOutput()

    @classmethod
    def from_text(
        cls,
        content: str,
        agent_id: str = "",
        confidence: float = 1.0,
        **kwargs,
    ) -> "CognitiveOutput":
        metadata = OutputMetadata(
            agent_id=agent_id,
            type=OutputType.TEXT,
            confidence=confidence,
            **kwargs,
        )
        return cls(
            metadata=metadata,
            type=OutputType.TEXT,
            data=TextOutput(content=content),
            confidence=confidence,
        )

    @classmethod
    def from_structured(
        cls,
        data: Dict[str, Any],
        agent_id: str = "",
        confidence: float = 1.0,
        **kwargs,
    ) -> "CognitiveOutput":
        metadata = OutputMetadata(
            agent_id=agent_id,
            type=OutputType.STRUCTURED,
            confidence=confidence,
            **kwargs,
        )
        return cls(
            metadata=metadata,
            type=OutputType.STRUCTURED,
            data=StructuredOutput(data=data),
            confidence=confidence,
        )

    @classmethod
    def from_action(
        cls,
        action_type: str,
        target: str,
        parameters: Dict[str, Any],
        result: Any,
        success: bool,
        agent_id: str = "",
        confidence: float = 1.0,
        **kwargs,
    ) -> "CognitiveOutput":
        metadata = OutputMetadata(
            agent_id=agent_id,
            type=OutputType.ACTION,
            confidence=confidence,
            **kwargs,
        )
        return cls(
            metadata=metadata,
            type=OutputType.ACTION,
            data=ActionOutput(
                action_type=action_type,
                target=target,
                parameters=parameters,
                result=result,
                success=success,
            ),
            confidence=confidence,
        )

    @classmethod
    def from_decision(
        cls,
        decision: Any,
        options: List[Any],
        selected_option: Any,
        reasoning: str,
        confidence: float,
        agent_id: str = "",
        **kwargs,
    ) -> "CognitiveOutput":
        metadata = OutputMetadata(
            agent_id=agent_id,
            type=OutputType.DECISION,
            confidence=confidence,
            **kwargs,
        )
        return cls(
            metadata=metadata,
            type=OutputType.DECISION,
            data=DecisionOutput(
                decision=decision,
                options=options,
                selected_option=selected_option,
                reasoning=reasoning,
                confidence=confidence,
            ),
            confidence=confidence,
            reasoning=reasoning,
        )

    def to_dict(self) -> Dict[str, Any]:
        data_dict = {}
        if hasattr(self.data, 'to_dict'):
            data_dict = self.data.to_dict()
        else:
            data_dict = {"data": str(self.data)}
        
        return {
            "metadata": self.metadata.to_dict(),
            "type": self.type.value,
            "data": data_dict,
            "confidence": self.confidence,
            "reasoning": self.reasoning[:200] + "..." if self.reasoning and len(self.reasoning) > 200 else self.reasoning,
            "sources": self.sources,
            "related_memories": self.related_memories,
            "related_knowledge": self.related_knowledge,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CognitiveOutput":
        metadata = OutputMetadata.from_dict(data.get("metadata", {}))
        output_type = OutputType(data.get("type", "text"))
        
        output_data = None
        if "data" in data:
            type_data = data["data"]
            if output_type == OutputType.TEXT:
                output_data = TextOutput.from_dict(type_data)
            elif output_type == OutputType.VOICE:
                output_data = VoiceOutput()
            elif output_type == OutputType.STRUCTURED:
                output_data = StructuredOutput.from_dict(type_data)
            elif output_type == OutputType.ACTION:
                output_data = ActionOutput.from_dict(type_data)
            elif output_type == OutputType.DECISION:
                output_data = DecisionOutput.from_dict(type_data)
            elif output_type == OutputType.PLAN:
                output_data = PlanOutput.from_dict(type_data)
            elif output_type == OutputType.REASONING:
                output_data = ReasoningOutput.from_dict(type_data)
        
        return cls(
            metadata=metadata,
            type=output_type,
            data=output_data,
            confidence=data.get("confidence", 0.0),
            reasoning=data.get("reasoning"),
            sources=data.get("sources", []),
            related_memories=data.get("related_memories", []),
            related_knowledge=data.get("related_knowledge", []),
        )

    def __repr__(self) -> str:
        data_str = str(self.data)[:50] + "..." if len(str(self.data)) > 50 else str(self.data)
        return f"CognitiveOutput(type={self.type.value}, confidence={self.confidence:.2f}, data={data_str})"
