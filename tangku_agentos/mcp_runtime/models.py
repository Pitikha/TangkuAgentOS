from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List


@dataclass(frozen=True)
class MCPMetadata:
    name: str
    description: str = ''
    version: str = '0.0.1'
    provider: str = ''
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class MCPServer:
    server_id: str
    metadata: MCPMetadata
    endpoint: str = ''
    capabilities: List[str] = field(default_factory=list)


@dataclass(frozen=True)
class MCPResource:
    resource_id: str
    name: str
    resource_type: str
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class MCPTool:
    tool_id: str
    name: str
    metadata: MCPMetadata
    resource: MCPResource


@dataclass(frozen=True)
class MCPPrompt:
    prompt_id: str
    text: str
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class MCPConnection:
    connection_id: str
    server: MCPServer
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class MCPSession:
    session_id: str
    connection: MCPConnection
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class MCPRequest:
    request_id: str
    session: MCPSession
    payload: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class MCPResponse:
    request_id: str
    session: MCPSession
    payload: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class MCPError:
    error_code: str
    message: str
    details: Dict[str, Any] = field(default_factory=dict)
