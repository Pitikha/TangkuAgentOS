from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Protocol

from .models import Tool, ToolRequest, ToolResponse, ToolResult, ToolStatus, ToolConfiguration


class ToolManagerInterface(ABC):
    """Interface for tool runtime manager."""

    @abstractmethod
    def register_tool(self, tool: Tool) -> None:
        ...

    @abstractmethod
    def get_tool(self, tool_id: str) -> Tool:
        ...

    @abstractmethod
    def list_tools(self) -> list[Tool]:
        ...

    @abstractmethod
    def remove_tool(self, tool_id: str) -> None:
        ...


class ToolRegistryInterface(ABC):
    """Interface for tool registry operations."""

    @abstractmethod
    def register(self, tool: Tool) -> None:
        ...

    @abstractmethod
    def resolve(self, tool_id: str) -> Tool:
        ...

    @abstractmethod
    def list(self) -> list[Tool]:
        ...


class ToolLoader(ABC):
    """Interface for tool loading."""

    @abstractmethod
    def load(self, tool_definition: str) -> Tool:
        ...


class ToolProvider(ABC):
    """Interface for tool providers."""

    @abstractmethod
    def provide(self, tool_id: str) -> Tool:
        ...


class ToolResolver(ABC):
    """Interface for resolving tools."""

    @abstractmethod
    def resolve(self, request: ToolRequest) -> Tool:
        ...


class ToolDispatcher(ABC):
    """Interface for dispatching tool requests."""

    @abstractmethod
    def dispatch(self, request: ToolRequest) -> ToolResponse:
        ...


class ToolSession(ABC):
    """Interface representing a tool session."""

    @abstractmethod
    def start(self) -> None:
        ...

    @abstractmethod
    def end(self) -> None:
        ...


class ToolContext(ABC):
    """Interface for tool execution context."""

    @abstractmethod
    def get_context(self) -> dict[str, str]:
        ...


class ToolPermissionManager(ABC):
    """Interface for managing tool permissions."""

    @abstractmethod
    def authorize(self, tool: Tool, action: str) -> bool:
        ...


class ToolConfigurationManager(ABC):
    """Interface for tool configuration management."""

    @abstractmethod
    def get_configuration(self, tool_id: str) -> ToolConfiguration:
        ...

    @abstractmethod
    def set_configuration(self, tool_id: str, configuration: ToolConfiguration) -> None:
        ...


class ToolStatisticsManager(ABC):
    """Interface for tool usage statistics."""

    @abstractmethod
    def record_usage(self, tool_id: str, data: dict[str, str]) -> None:
        ...

    @abstractmethod
    def get_statistics(self, tool_id: str) -> dict[str, str]:
        ...


class ToolHealthManager(ABC):
    """Interface for tool health monitoring."""

    @abstractmethod
    def check_health(self, tool_id: str) -> ToolStatus:
        ...
