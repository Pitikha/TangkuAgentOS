from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List


class ToolCategory(Enum):
    FILE_SYSTEM = 'file_system'
    TERMINAL = 'terminal'
    PYTHON = 'python'
    GIT = 'git'
    BROWSER = 'browser'
    WEB_SEARCH = 'web_search'
    DATABASE = 'database'
    HTTP_API = 'http_api'
    OCR = 'ocr'
    IMAGE = 'image'
    AUDIO = 'audio'
    VIDEO = 'video'
    OFFICE_DOCUMENTS = 'office_documents'
    COMPRESSION = 'compression'
    DOCKER = 'docker'
    KUBERNETES = 'kubernetes'
    CLOUD = 'cloud'
    SYSTEM_INFORMATION = 'system_information'
    PACKAGE_MANAGEMENT = 'package_management'


class ToolStatus(Enum):
    AVAILABLE = 'available'
    UNAVAILABLE = 'unavailable'
    DEGRADED = 'degraded'
    OFFLINE = 'offline'


@dataclass(frozen=True)
class ToolMetadata:
    tool_id: str
    name: str
    description: str = ''
    category: ToolCategory = ToolCategory.SYSTEM_INFORMATION
    version: str = '0.0.1'
    capabilities: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ToolDefinition:
    tool_id: str
    metadata: ToolMetadata
    configuration_schema: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ToolCapabilityMapping:
    tool_id: str
    capabilities: List[str] = field(default_factory=list)


@dataclass
class ToolConfiguration:
    tool_id: str
    settings: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ToolRequest:
    request_id: str
    tool_id: str
    payload: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ToolResponse:
    request_id: str
    tool_id: str
    status: ToolStatus
    result: ToolResult | None = None
    error: str | None = None


@dataclass
class ToolResult:
    result_id: str
    output: Any = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ToolError:
    error_code: str
    message: str
    details: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Tool:
    tool_id: str
    definition: ToolDefinition
    metadata: ToolMetadata
    status: ToolStatus = ToolStatus.AVAILABLE
    configuration: ToolConfiguration = field(default_factory=lambda: ToolConfiguration(tool_id='', settings={}))
    schema: Dict[str, Any] = field(default_factory=dict)
    permission_requirements: List[str] = field(default_factory=list)
    capabilities: List[str] = field(default_factory=list)
    health: Dict[str, Any] = field(default_factory=dict)
    statistics: Dict[str, Any] = field(default_factory=dict)
    lifecycle_hooks: Dict[str, Any] = field(default_factory=dict)
    executor: Callable[[ToolRequest], ToolResponse] | None = None

    def execute(self, request: ToolRequest) -> ToolResponse:
        if self.executor is None:
            return ToolResponse(
                request_id=request.request_id,
                tool_id=self.tool_id,
                status=ToolStatus.UNAVAILABLE,
                result=ToolResult(result_id=request.request_id, output={"message": "No executor configured"}),
            )
        try:
            return self.executor(request)
        except Exception as exc:  # pragma: no cover - defensive fallback
            return ToolResponse(
                request_id=request.request_id,
                tool_id=self.tool_id,
                status=ToolStatus.UNAVAILABLE,
                error=str(exc),
            )
