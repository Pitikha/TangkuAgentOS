from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, Optional


class InterfaceType(Enum):
    CLI = "cli"
    INTERACTIVE_SHELL = "interactive_shell"
    REST_API = "rest_api"
    WEBSOCKET = "websocket"
    PYTHON_SDK = "python_sdk"
    WEB_DASHBOARD = "web_dashboard"
    DESKTOP = "desktop"
    MOBILE = "mobile"
    VS_CODE = "vscode"


@dataclass(frozen=True)
class InterfaceMetadata:
    interface_id: str
    interface_type: InterfaceType
    description: str = ""
    supports_streaming: bool = False
    authentication_required: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class InterfaceRequest:
    request_id: str
    session_id: str
    interface_type: InterfaceType
    command: str
    payload: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: Optional[float] = None


@dataclass(frozen=True)
class InterfaceResponse:
    request_id: str
    session_id: str
    status: str
    output: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    continuation_token: Optional[str] = None


@dataclass
class InterfaceSession:
    session_id: str
    interface_type: InterfaceType
    user_id: str = ""
    active: bool = False
    created_at: Optional[float] = None
    last_accessed_at: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class InterfaceContext:
    session_id: str
    context_data: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    version: Optional[int] = None


@dataclass(frozen=True)
class InterfaceEvent:
    event_id: str
    session_id: str
    event_type: str
    payload: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: Optional[float] = None


@dataclass(frozen=True)
class InterfaceCommand:
    command_id: str
    session_id: str
    name: str
    arguments: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    metadata_command: Optional[Dict[str, Any]] = None


@dataclass(frozen=True)
class InterfaceResult:
    result_id: str
    request_id: str
    success: bool
    output: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: Optional[float] = None


@dataclass(frozen=True)
class InterfaceFeature:
    feature_id: str
    name: str
    description: str = ""
    enabled: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)
