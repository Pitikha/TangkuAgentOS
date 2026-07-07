"""SDK architecture for Tangku AgentOS."""

from .interfaces import (
    AgentSDKInterface,
    CapabilitySDKInterface,
    ContextSDKInterface,
    InterfaceSDKInterface,
    MemorySDKInterface,
    PluginSDKInterface,
    ToolSDKInterface,
    WorkflowSDKInterface,
)
from .builders import SDKBuilder
from .factories import SDKFactory
from .registries import SDKRegistry
from .adapters import SDKAdapter
from .developer import TangkuDeveloperSDK
from .models import (
    SDKExtensionPoint,
    SDKInterface,
    SDKRegistration,
)

__all__ = [
    "SDKBuilder",
    "SDKFactory",
    "SDKRegistry",
    "SDKAdapter",
    "SDKExtensionPoint",
    "SDKInterface",
    "SDKRegistration",
    "AgentSDKInterface",
    "ToolSDKInterface",
    "PluginSDKInterface",
    "WorkflowSDKInterface",
    "MemorySDKInterface",
    "CapabilitySDKInterface",
    "ContextSDKInterface",
    "InterfaceSDKInterface",
    "TangkuDeveloperSDK",
]
