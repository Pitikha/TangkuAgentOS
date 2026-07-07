from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List


class ModelState(Enum):
    AVAILABLE = "available"
    LOADING = "loading"
    UNAVAILABLE = "unavailable"
    DEGRADED = "degraded"


class ModelCapability(Enum):
    TEXT = "text"
    IMAGE = "image"
    AUDIO = "audio"
    VIDEO = "video"
    STRUCTURED = "structured"
    MULTIMODAL = "multimodal"


@dataclass(frozen=True)
class ModelMetadata:
    model_id: str
    provider: str
    version: str
    description: str = ""
    capabilities: List[ModelCapability] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ModelConfiguration:
    provider_id: str
    settings: Dict[str, Any] = field(default_factory=dict)
    defaults: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ModelProfile:
    profile_id: str
    display_name: str
    description: str = ""
    configuration: ModelConfiguration | None = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ModelLimits:
    max_tokens: int | None = None
    max_concurrency: int | None = None
    max_requests_per_minute: int | None = None
    max_payload_size: int | None = None


@dataclass(frozen=True)
class ModelCost:
    cost_per_request: float = 0.0
    cost_per_token: float = 0.0
    currency: str = "USD"


@dataclass(frozen=True)
class ModelUsage:
    model_id: str
    total_requests: int = 0
    total_tokens: int = 0
    total_cost: float = 0.0
    details: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class Model:
    model_id: str
    metadata: ModelMetadata
    configuration: ModelConfiguration
    state: ModelState = ModelState.AVAILABLE
    profile: ModelProfile | None = None
    limits: ModelLimits | None = None
    cost: ModelCost | None = None
    tags: List[str] = field(default_factory=list)


@dataclass(frozen=True)
class ModelSession:
    session_id: str
    model_id: str
    created_at: str
    expires_at: str | None = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ModelRequest:
    request_id: str
    model_id: str | None = None
    provider_id: str | None = None
    payload: Dict[str, Any] = field(default_factory=dict)
    parameters: Dict[str, Any] = field(default_factory=dict)
    session_id: str | None = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ModelResult:
    success: bool
    output: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    usage: ModelUsage | None = None


@dataclass(frozen=True)
class ModelResponse:
    request_id: str
    result: ModelResult
    error: ModelError | None = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ModelError:
    code: str
    message: str
    details: Dict[str, Any] = field(default_factory=dict)
