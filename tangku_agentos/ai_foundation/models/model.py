"""
AI Foundation Framework - Model Abstraction

This module defines the universal AIModel interface and related classes.
Every provider must implement this interface.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, Union, TYPE_CHECKING

if TYPE_CHECKING:
    from tangku_agentos.ai_foundation.models.request import AIRequest
    from tangku_agentos.ai_foundation.models.response import AIResponse, StreamChunk


class ModelModality(Enum):
    """
    Supported modalities for AI models.
    
    Attributes:
        TEXT: Text input/output.
        CHAT: Chat/conversation input/output.
        COMPLETION: Text completion.
        EMBEDDING: Embedding generation.
        VISION: Image/vision input.
        AUDIO: Audio input/output.
        IMAGE: Image generation.
        VIDEO: Video input/output.
        MULTI_MODAL: Multiple modalities combined.
        TOOL_CALLING: Tool/function calling.
        STRUCTURED_OUTPUT: Structured output generation.
        STREAMING: Streaming output.
        BATCH: Batch processing.
        REASONING: Advanced reasoning.
    """

    TEXT = "text"
    CHAT = "chat"
    COMPLETION = "completion"
    EMBEDDING = "embedding"
    VISION = "vision"
    AUDIO = "audio"
    IMAGE = "image"
    VIDEO = "video"
    MULTI_MODAL = "multi_modal"
    TOOL_CALLING = "tool_calling"
    STRUCTURED_OUTPUT = "structured_output"
    STREAMING = "streaming"
    BATCH = "batch"
    REASONING = "reasoning"


class ModelType(Enum):
    """
    Types of AI models.
    
    Attributes:
        CHAT: Chat/conversation models.
        COMPLETION: Text completion models.
        EMBEDDING: Embedding models.
        VISION: Vision models.
        AUDIO: Audio models.
        IMAGE: Image generation models.
        MULTI_MODAL: Multi-modal models.
        REASONING: Reasoning models.
        CODE: Code generation models.
        SPECIALIZED: Specialized models.
    """

    CHAT = "chat"
    COMPLETION = "completion"
    EMBEDDING = "embedding"
    VISION = "vision"
    AUDIO = "audio"
    IMAGE = "image"
    MULTI_MODAL = "multi_modal"
    REASONING = "reasoning"
    CODE = "code"
    SPECIALIZED = "specialized"


class ModelStatus(Enum):
    """
    Status of an AI model.
    
    Attributes:
        AVAILABLE: Model is available and ready to use.
        UNAVAILABLE: Model is temporarily unavailable.
        DEGRADED: Model is available but with degraded performance.
        MAINTENANCE: Model is under maintenance.
        DEPRECATED: Model is deprecated.
        DISABLED: Model is disabled.
        UNKNOWN: Model status is unknown.
    """

    AVAILABLE = "available"
    UNAVAILABLE = "unavailable"
    DEGRADED = "degraded"
    MAINTENANCE = "maintenance"
    DEPRECATED = "deprecated"
    DISABLED = "disabled"
    UNKNOWN = "unknown"


@dataclass
class ModelPricing:
    """
    Pricing information for an AI model.
    
    Attributes:
        input_price_per_token: Price per input token (in USD).
        output_price_per_token: Price per output token (in USD).
        embedding_price_per_token: Price per embedding token (in USD).
        image_price: Price per image (in USD).
        audio_price_per_minute: Price per minute of audio (in USD).
        currency: Currency code (default: USD).
    """

    input_price_per_token: float = 0.0
    output_price_per_token: float = 0.0
    embedding_price_per_token: float = 0.0
    image_price: float = 0.0
    audio_price_per_minute: float = 0.0
    currency: str = "USD"

    def calculate_cost(self, input_tokens: int = 0, output_tokens: int = 0, 
                      embedding_tokens: int = 0, images: int = 0, 
                      audio_minutes: float = 0.0) -> float:
        """Calculate the total cost for a request."""
        cost = 0.0
        cost += input_tokens * self.input_price_per_token
        cost += output_tokens * self.output_price_per_token
        cost += embedding_tokens * self.embedding_price_per_token
        cost += images * self.image_price
        cost += audio_minutes * self.audio_price_per_minute
        return cost

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "input_price_per_token": self.input_price_per_token,
            "output_price_per_token": self.output_price_per_token,
            "embedding_price_per_token": self.embedding_price_per_token,
            "image_price": self.image_price,
            "audio_price_per_minute": self.audio_price_per_minute,
            "currency": self.currency,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ModelPricing":
        """Create from dictionary."""
        return cls(
            input_price_per_token=data.get("input_price_per_token", 0.0),
            output_price_per_token=data.get("output_price_per_token", 0.0),
            embedding_price_per_token=data.get("embedding_price_per_token", 0.0),
            image_price=data.get("image_price", 0.0),
            audio_price_per_minute=data.get("audio_price_per_minute", 0.0),
            currency=data.get("currency", "USD"),
        )


@dataclass
class ModelLimits:
    """
    Limits for an AI model.
    
    Attributes:
        max_input_tokens: Maximum input tokens.
        max_output_tokens: Maximum output tokens.
        max_total_tokens: Maximum total tokens (input + output).
        max_embedding_tokens: Maximum tokens for embeddings.
        max_images: Maximum number of images.
        max_audio_length: Maximum audio length in seconds.
        max_batch_size: Maximum batch size.
        max_parallel_requests: Maximum parallel requests.
        rate_limit_requests: Requests per minute limit.
        rate_limit_tokens: Tokens per minute limit.
    """

    max_input_tokens: int = 0
    max_output_tokens: int = 0
    max_total_tokens: int = 0
    max_embedding_tokens: int = 0
    max_images: int = 0
    max_audio_length: float = 0.0
    max_batch_size: int = 0
    max_parallel_requests: int = 0
    rate_limit_requests: int = 0
    rate_limit_tokens: int = 0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "max_input_tokens": self.max_input_tokens,
            "max_output_tokens": self.max_output_tokens,
            "max_total_tokens": self.max_total_tokens,
            "max_embedding_tokens": self.max_embedding_tokens,
            "max_images": self.max_images,
            "max_audio_length": self.max_audio_length,
            "max_batch_size": self.max_batch_size,
            "max_parallel_requests": self.max_parallel_requests,
            "rate_limit_requests": self.rate_limit_requests,
            "rate_limit_tokens": self.rate_limit_tokens,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ModelLimits":
        """Create from dictionary."""
        return cls(
            max_input_tokens=data.get("max_input_tokens", 0),
            max_output_tokens=data.get("max_output_tokens", 0),
            max_total_tokens=data.get("max_total_tokens", 0),
            max_embedding_tokens=data.get("max_embedding_tokens", 0),
            max_images=data.get("max_images", 0),
            max_audio_length=data.get("max_audio_length", 0.0),
            max_batch_size=data.get("max_batch_size", 0),
            max_parallel_requests=data.get("max_parallel_requests", 0),
            rate_limit_requests=data.get("rate_limit_requests", 0),
            rate_limit_tokens=data.get("rate_limit_tokens", 0),
        )


@dataclass
class ModelCapability:
    """
    Capabilities of an AI model.
    
    Attributes:
        modalities: Supported modalities.
        supports_chat: Whether chat is supported.
        supports_completion: Whether completion is supported.
        supports_embedding: Whether embeddings are supported.
        supports_vision: Whether vision is supported.
        supports_audio: Whether audio is supported.
        supports_image_generation: Whether image generation is supported.
        supports_video: Whether video is supported.
        supports_tool_calling: Whether tool calling is supported.
        supports_structured_output: Whether structured output is supported.
        supports_streaming: Whether streaming is supported.
        supports_batch: Whether batch processing is supported.
        supports_reasoning: Whether advanced reasoning is supported.
        supports_json_mode: Whether JSON mode is supported.
        supports_function_calling: Whether function calling is supported.
    """

    modalities: Set[ModelModality] = field(default_factory=set)
    supports_chat: bool = False
    supports_completion: bool = False
    supports_embedding: bool = False
    supports_vision: bool = False
    supports_audio: bool = False
    supports_image_generation: bool = False
    supports_video: bool = False
    supports_tool_calling: bool = False
    supports_structured_output: bool = False
    supports_streaming: bool = False
    supports_batch: bool = False
    supports_reasoning: bool = False
    supports_json_mode: bool = False
    supports_function_calling: bool = False

    def has_modality(self, modality: ModelModality) -> bool:
        """Check if model supports a specific modality."""
        return modality in self.modalities

    def has_capability(self, capability: str) -> bool:
        """Check if model has a specific capability."""
        capability_map = {
            "chat": self.supports_chat,
            "completion": self.supports_completion,
            "embedding": self.supports_embedding,
            "vision": self.supports_vision,
            "audio": self.supports_audio,
            "image_generation": self.supports_image_generation,
            "video": self.supports_video,
            "tool_calling": self.supports_tool_calling,
            "structured_output": self.supports_structured_output,
            "streaming": self.supports_streaming,
            "batch": self.supports_batch,
            "reasoning": self.supports_reasoning,
            "json_mode": self.supports_json_mode,
            "function_calling": self.supports_function_calling,
        }
        return capability_map.get(capability, False)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "modalities": [m.value for m in self.modalities],
            "supports_chat": self.supports_chat,
            "supports_completion": self.supports_completion,
            "supports_embedding": self.supports_embedding,
            "supports_vision": self.supports_vision,
            "supports_audio": self.supports_audio,
            "supports_image_generation": self.supports_image_generation,
            "supports_video": self.supports_video,
            "supports_tool_calling": self.supports_tool_calling,
            "supports_structured_output": self.supports_structured_output,
            "supports_streaming": self.supports_streaming,
            "supports_batch": self.supports_batch,
            "supports_reasoning": self.supports_reasoning,
            "supports_json_mode": self.supports_json_mode,
            "supports_function_calling": self.supports_function_calling,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ModelCapability":
        """Create from dictionary."""
        modalities = set()
        for modality in data.get("modalities", []):
            try:
                modalities.add(ModelModality(modality))
            except ValueError:
                pass

        return cls(
            modalities=modalities,
            supports_chat=data.get("supports_chat", False),
            supports_completion=data.get("supports_completion", False),
            supports_embedding=data.get("supports_embedding", False),
            supports_vision=data.get("supports_vision", False),
            supports_audio=data.get("supports_audio", False),
            supports_image_generation=data.get("supports_image_generation", False),
            supports_video=data.get("supports_video", False),
            supports_tool_calling=data.get("supports_tool_calling", False),
            supports_structured_output=data.get("supports_structured_output", False),
            supports_streaming=data.get("supports_streaming", False),
            supports_batch=data.get("supports_batch", False),
            supports_reasoning=data.get("supports_reasoning", False),
            supports_json_mode=data.get("supports_json_mode", False),
            supports_function_calling=data.get("supports_function_calling", False),
        )


@dataclass
class AIModel:
    """
    Universal AI Model interface.
    
    This class defines the interface that all AI models must implement.
    It provides a provider-agnostic way to interact with AI models.
    
    Attributes:
        model_id: Unique identifier for the model.
        name: Human-readable name for the model.
        provider: Provider name (e.g., "openai", "anthropic").
        model_type: Type of model (chat, completion, embedding, etc.).
        modalities: Supported modalities.
        capabilities: Model capabilities.
        limits: Model limits.
        pricing: Model pricing.
        status: Current status of the model.
        version: Model version.
        description: Model description.
        created_at: When the model was created.
        updated_at: When the model was last updated.
        metadata: Additional metadata.
    """

    model_id: str
    name: str
    provider: str
    model_type: ModelType = ModelType.CHAT
    modalities: Set[ModelModality] = field(default_factory=set)
    capabilities: ModelCapability = field(default_factory=ModelCapability)
    limits: ModelLimits = field(default_factory=ModelLimits)
    pricing: ModelPricing = field(default_factory=ModelPricing)
    status: ModelStatus = ModelStatus.UNKNOWN
    version: str = "1.0"
    description: str = ""
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Post-initialization validation."""
        if not self.model_id:
            raise ValueError("model_id is required")
        if not self.name:
            self.name = self.model_id
        if not self.provider:
            raise ValueError("provider is required")

    def has_modality(self, modality: ModelModality) -> bool:
        """Check if model supports a specific modality."""
        return self.capabilities.has_modality(modality)

    def has_capability(self, capability: str) -> bool:
        """Check if model has a specific capability."""
        return self.capabilities.has_capability(capability)

    def can_handle(self, request: "AIRequest") -> bool:
        """Check if this model can handle the given request."""
        # Check if model supports required modalities
        required_modalities = self._get_required_modalities(request)
        for modality in required_modalities:
            if not self.has_modality(modality):
                return False
        
        # Check if model supports required capabilities
        required_capabilities = self._get_required_capabilities(request)
        for capability in required_capabilities:
            if not self.has_capability(capability):
                return False
        
        return True

    def _get_required_modalities(self, request: "AIRequest") -> Set[ModelModality]:
        """Get required modalities for a request."""
        required = {ModelModality.TEXT}
        
        # Check for chat
        if request.messages:
            required.add(ModelModality.CHAT)
        
        # Check for streaming
        if request.stream:
            required.add(ModelModality.STREAMING)
        
        # Check for tool calling
        if request.use_tools:
            required.add(ModelModality.TOOL_CALLING)
        
        # Check for structured output
        if request.response_format:
            required.add(ModelModality.STRUCTURED_OUTPUT)
        
        return required

    def _get_required_capabilities(self, request: "AIRequest") -> Set[str]:
        """Get required capabilities for a request."""
        required = set()
        
        if request.stream:
            required.add("streaming")
        
        if request.use_tools:
            required.add("tool_calling")
            required.add("function_calling")
        
        if request.response_format:
            required.add("json_mode")
            required.add("structured_output")
        
        return required

    def calculate_cost(self, request: "AIRequest", response: Optional["AIResponse"] = None) -> float:
        """Calculate the cost for a request and optional response."""
        input_tokens = request.input_tokens if hasattr(request, 'input_tokens') else 0
        output_tokens = response.output_tokens if response and hasattr(response, 'output_tokens') else 0
        
        return self.pricing.calculate_cost(
            input_tokens=input_tokens,
            output_tokens=output_tokens
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "model_id": self.model_id,
            "name": self.name,
            "provider": self.provider,
            "model_type": self.model_type.value,
            "modalities": [m.value for m in self.modalities],
            "capabilities": self.capabilities.to_dict(),
            "limits": self.limits.to_dict(),
            "pricing": self.pricing.to_dict(),
            "status": self.status.value,
            "version": self.version,
            "description": self.description,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AIModel":
        """Create from dictionary."""
        modalities = set()
        for modality in data.get("modalities", []):
            try:
                modalities.add(ModelModality(modality))
            except ValueError:
                pass

        return cls(
            model_id=data.get("model_id", ""),
            name=data.get("name", ""),
            provider=data.get("provider", ""),
            model_type=ModelType(data.get("model_type", "chat")),
            modalities=modalities,
            capabilities=ModelCapability.from_dict(data.get("capabilities", {})),
            limits=ModelLimits.from_dict(data.get("limits", {})),
            pricing=ModelPricing.from_dict(data.get("pricing", {})),
            status=ModelStatus(data.get("status", "unknown")),
            version=data.get("version", "1.0"),
            description=data.get("description", ""),
            metadata=data.get("metadata", {}),
        )

    def __repr__(self) -> str:
        """Return string representation."""
        return (
            f"AIModel("
            f"id={self.model_id}, "
            f"name={self.name}, "
            f"provider={self.provider}, "
            f"type={self.model_type.value}, "
            f"status={self.status.value})"
        )
