from __future__ import annotations

from abc import ABC, abstractmethod

from .models import (
    MCPConnection,
    MCPError,
    MCPRequest,
    MCPResponse,
    MCPResource,
    MCPServer,
    MCPSession,
    MCPTool,
    MCPPrompt,
)


class MCPManagerInterface(ABC):
    """Interface for MCP manager."""

    @abstractmethod
    def register_server(self, server: MCPServer) -> None:
        ...

    @abstractmethod
    def get_server(self, server_id: str) -> MCPServer:
        ...

    @abstractmethod
    def list_servers(self) -> list[MCPServer]:
        ...

    @abstractmethod
    def deregister_server(self, server_id: str) -> None:
        ...


class MCPRegistryInterface(ABC):
    """Interface for MCP registry."""

    @abstractmethod
    def register(self, resource: MCPResource) -> None:
        ...

    @abstractmethod
    def resolve(self, key: str) -> MCPResource:
        ...


class MCPClient(ABC):
    """Client abstraction for MCP communication."""

    @abstractmethod
    def connect(self, server: MCPServer) -> MCPConnection:
        ...

    @abstractmethod
    def request(self, connection: MCPConnection, request: MCPRequest) -> MCPResponse:
        ...


class MCPServerAdapter(ABC):
    """Adapter contract for MCP servers."""

    @abstractmethod
    def start(self) -> None:
        ...

    @abstractmethod
    def stop(self) -> None:
        ...


class MCPTransportLayer(ABC):
    """Transport abstraction for MCP."""

    @abstractmethod
    def send(self, connection: MCPConnection, payload: dict[str, str]) -> MCPResponse:
        ...

    @abstractmethod
    def receive(self, connection: MCPConnection) -> dict[str, str]:
        ...


class MCPSessionManager(ABC):
    """Session manager for MCP sessions."""

    @abstractmethod
    def create_session(self, connection: MCPConnection) -> MCPSession:
        ...

    @abstractmethod
    def close_session(self, session_id: str) -> None:
        ...


class MCPDiscoveryManager(ABC):
    """Discovery manager for MCP resources."""

    @abstractmethod
    def discover(self) -> list[MCPResource]:
        ...


class MCPPermissionManager(ABC):
    """Permission manager for MCP resources."""

    @abstractmethod
    def authorize(self, tool: MCPTool, action: str) -> bool:
        ...


class MCPConfigurationManager(ABC):
    """Configuration manager for MCP."""

    @abstractmethod
    def get_configuration(self, server_id: str) -> dict[str, str]:
        ...

    @abstractmethod
    def set_configuration(self, server_id: str, configuration: dict[str, str]) -> None:
        ...
