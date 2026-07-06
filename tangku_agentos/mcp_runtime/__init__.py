"""MCP runtime architecture for Tangku AgentOS."""

from .interfaces import (
    MCPConfigurationManager,
    MCPManagerInterface,
    MCPRegistryInterface,
    MCPServerAdapter,
    MCPSessionManager,
    MCPTransportLayer,
    MCPPermissionManager,
    MCPDiscoveryManager,
)
from .manager import MCPManager
from .registry import MCPRegistry
from .client import MCPClient
from .server import MCPServerAdapter
from .transport import MCPTransportLayer
from .session import MCPSessionManager
from .discovery import MCPDiscoveryManager
from .permissions import MCPPermissionManager
from .configuration import MCPConfigurationManager
from .models import (
    MCPConnection,
    MCPError,
    MCPMetadata,
    MCPRequest,
    MCPResponse,
    MCPResource,
    MCPServer,
    MCPSession,
    MCPTool,
    MCPPrompt,
)

__all__ = [
    "MCPManager",
    "MCPRegistry",
    "MCPClient",
    "MCPServerAdapter",
    "MCPSessionManager",
    "MCPTransportLayer",
    "MCPDiscoveryManager",
    "MCPPermissionManager",
    "MCPConfigurationManager",
    "MCPServer",
    "MCPResource",
    "MCPTool",
    "MCPPrompt",
    "MCPConnection",
    "MCPSession",
    "MCPMetadata",
    "MCPRequest",
    "MCPResponse",
    "MCPError",
    "MCPManagerInterface",
    "MCPRegistryInterface",
    "MCPClient",
    "MCPServerAdapter",
]
