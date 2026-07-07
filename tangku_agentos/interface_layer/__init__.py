"""Interface layer contracts and concrete adapters for Tangku AgentOS."""

from .context import InterfaceContextManager
from .events import InterfaceEventManager
from .interfaces import (
    CLIInterface,
    DesktopInterface,
    InterfaceAdapter,
    InterfaceConfigurationManager,
    InterfaceFeature,
    InterfaceManagerInterface,
    InterfacePermissionManager,
    InterfaceRegistryInterface,
    InteractiveShellInterface,
    MobileInterface,
    PythonSDKInterface,
    RESTAPIInterface,
    VSCodeExtensionInterface,
    WebDashboardInterface,
    WebSocketInterface,
)
from .manager import InterfaceManager
from .models import (
    InterfaceCommand,
    InterfaceContext,
    InterfaceEvent,
    InterfaceFeature,
    InterfaceMetadata,
    InterfaceRequest,
    InterfaceResponse,
    InterfaceResult,
    InterfaceSession,
    InterfaceType,
)
from .registry import InterfaceRegistry
from .router import DefaultInterfaceRouter, InterfaceRouter
from .session import InterfaceSessionManager, InterfaceSessionPersistence
from .state import InterfaceStateManager
from .web_dashboard import ProductionWebDashboard
from .web_dashboard_server import DashboardHTTPApp

__all__ = [
    "InterfaceManager",
    "InterfaceManagerInterface",
    "InterfaceRegistry",
    "InterfaceRegistryInterface",
    "InterfaceRouter",
    "DefaultInterfaceRouter",
    "InterfaceAdapter",
    "InterfaceType",
    "InterfaceMetadata",
    "InterfaceRequest",
    "InterfaceResponse",
    "InterfaceSession",
    "InterfaceContext",
    "InterfaceEvent",
    "InterfaceCommand",
    "InterfaceResult",
    "InterfaceFeature",
    "InterfaceSessionManager",
    "InterfaceContextManager",
    "InterfaceStateManager",
    "InterfaceEventManager",
    "InterfacePermissionManager",
    "InterfaceConfigurationManager",
    "CLIInterface",
    "InteractiveShellInterface",
    "RESTAPIInterface",
    "WebSocketInterface",
    "PythonSDKInterface",
    "WebDashboardInterface",
    "ProductionWebDashboard",
    "DashboardHTTPApp",
    "DesktopInterface",
    "MobileInterface",
    "VSCodeExtensionInterface",
]
