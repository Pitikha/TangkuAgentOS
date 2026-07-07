from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List


class CapabilityCategory(Enum):
    FILE_OPERATIONS = "file_operations"
    CODE_ANALYSIS = "code_analysis"
    CODE_GENERATION = "code_generation"
    TERMINAL_EXECUTION = "terminal_execution"
    BROWSER_AUTOMATION = "browser_automation"
    GIT_OPERATIONS = "git_operations"
    DATABASE_ACCESS = "database_access"
    NETWORK_OPERATIONS = "network_operations"
    SEARCH = "search"
    OCR = "ocr"
    IMAGE_PROCESSING = "image_processing"
    AUDIO_PROCESSING = "audio_processing"
    VIDEO_PROCESSING = "video_processing"
    DEPLOYMENT = "deployment"
    CLOUD_OPERATIONS = "cloud_operations"
    DOCUMENTATION = "documentation"
    MEMORY_ACCESS = "memory_access"
    KNOWLEDGE_RETRIEVAL = "knowledge_retrieval"
    PLANNING = "planning"
    VERIFICATION = "verification"


class CapabilityState(Enum):
    AVAILABLE = "available"
    UNAVAILABLE = "unavailable"
    ERROR = "error"
    DEPRECATED = "deprecated"


@dataclass(frozen=True)
class CapabilityMetadata:
    name: str
    description: str = ""
    category: CapabilityCategory = CapabilityCategory.CODE_ANALYSIS
    version: str = "0.1.0"
    provider: str = ""
    tags: List[str] = field(default_factory=list)
    attributes: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class CapabilityContext:
    request_id: str
    agent_id: str
    permissions: list[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    payload: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class CapabilityPermission:
    capability_name: str
    allowed: bool = False
    requirements: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class CapabilityRequest:
    request_id: str
    agent_id: str
    capability_name: str
    parameters: Dict[str, Any] = field(default_factory=dict)
    priority: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class CapabilityResponse:
    request_id: str
    capability_name: str
    status: str = "pending"
    result: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class CapabilityResult:
    result_id: str
    request_id: str
    capability_name: str
    status: str = "pending"
    payload: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class CapabilityConfiguration:
    enabled: bool = True
    timeout_seconds: int = 30
    retry_attempts: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)
