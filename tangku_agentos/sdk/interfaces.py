from __future__ import annotations

from abc import ABC, abstractmethod


class SDKInterface(ABC):
    """Base SDK interface."""

    @abstractmethod
    def register(self, registration: "SDKRegistration") -> None:
        ...


class AgentSDKInterface(SDKInterface):
    """Agent SDK contract."""

    @abstractmethod
    def register_agent(self, agent: "AgentDescriptor") -> None:
        ...


class ToolSDKInterface(SDKInterface):
    """Tool SDK contract."""

    @abstractmethod
    def register_tool(self, tool: "ToolDescriptor") -> None:
        ...


class PluginSDKInterface(SDKInterface):
    """Plugin SDK contract."""

    @abstractmethod
    def register_plugin(self, plugin: "PluginDescriptor") -> None:
        ...


class WorkflowSDKInterface(SDKInterface):
    """Workflow SDK contract."""

    @abstractmethod
    def register_workflow(self, workflow: "WorkflowDescriptor") -> None:
        ...


class MemorySDKInterface(SDKInterface):
    """Memory SDK contract."""

    @abstractmethod
    def register_memory(self, memory: "MemoryDescriptor") -> None:
        ...


class CapabilitySDKInterface(SDKInterface):
    """Capability SDK contract."""

    @abstractmethod
    def register_capability(self, capability: "CapabilityDescriptor") -> None:
        ...


class ContextSDKInterface(SDKInterface):
    """Context SDK contract."""

    @abstractmethod
    def register_context(self, context: "ContextDescriptor") -> None:
        ...


class InterfaceSDKInterface(SDKInterface):
    """Interface SDK contract."""

    @abstractmethod
    def register_interface(self, interface: "InterfaceDescriptor") -> None:
        ...
