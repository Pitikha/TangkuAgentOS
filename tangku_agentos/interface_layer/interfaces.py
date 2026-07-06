from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

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
)
from .context import InterfaceContextManager
from .events import InterfaceEventManager
from .router import InterfaceRouter
from .session import InterfaceSessionManager
from .state import InterfaceStateManager


class InterfaceAdapter(ABC):
    """Base contract for any Tangku interface adapter."""

    @abstractmethod
    def initialize(self, metadata: InterfaceMetadata) -> None:
        ...

    @abstractmethod
    def handle_request(self, request: InterfaceRequest) -> InterfaceResponse:
        ...

    @abstractmethod
    def supports_streaming(self) -> bool:
        ...

    @abstractmethod
    def shutdown(self) -> None:
        ...


class CLIInterface(InterfaceAdapter):
    """Command line interface abstraction."""

    @abstractmethod
    def execute_command(self, command: InterfaceCommand) -> InterfaceResult:
        ...


class InteractiveShellInterface(InterfaceAdapter):
    """Interactive shell interface abstraction."""

    @abstractmethod
    def open_session(self, session: InterfaceSession) -> InterfaceSession:
        ...

    @abstractmethod
    def execute_command(self, command: InterfaceCommand) -> InterfaceResult:
        ...

    @abstractmethod
    def stream_output(self, request: InterfaceRequest) -> InterfaceResponse:
        ...

    @abstractmethod
    def close_session(self, session_id: str) -> None:
        ...


class RESTAPIInterface(InterfaceAdapter):
    """REST API interface abstraction."""

    @abstractmethod
    def handle_request(self, request: InterfaceRequest) -> InterfaceResponse:
        ...

    @abstractmethod
    def authenticate_request(self, request: InterfaceRequest) -> bool:
        ...


class WebSocketInterface(InterfaceAdapter):
    """WebSocket interface abstraction."""

    @abstractmethod
    def open_connection(self, session_id: str, metadata: dict[str, Any]) -> str:
        ...

    @abstractmethod
    def send_event(self, event: InterfaceEvent) -> None:
        ...

    @abstractmethod
    def close_connection(self, session_id: str) -> None:
        ...

    @abstractmethod
    def authenticate_connection(self, session_id: str, metadata: dict[str, Any]) -> bool:
        ...


class PythonSDKInterface(InterfaceAdapter):
    """Python SDK interface abstraction."""

    @abstractmethod
    def call(self, command: InterfaceCommand) -> InterfaceResult:
        ...

    @abstractmethod
    def authenticate_call(self, request: InterfaceRequest) -> bool:
        ...


class WebDashboardInterface(InterfaceAdapter):
    """Web dashboard interface abstraction."""

    @abstractmethod
    def render_route(self, route: str, payload: dict[str, Any]) -> InterfaceResponse:
        ...

    @abstractmethod
    def push_update(self, update: InterfaceEvent) -> None:
        ...


class DesktopInterface(InterfaceAdapter):
    """Desktop application interface abstraction."""

    @abstractmethod
    def launch(self) -> None:
        ...

    @abstractmethod
    def send_command(self, command: InterfaceCommand) -> InterfaceResult:
        ...


class MobileInterface(InterfaceAdapter):
    """Mobile application interface abstraction."""

    @abstractmethod
    def launch(self) -> None:
        ...

    @abstractmethod
    def send_command(self, command: InterfaceCommand) -> InterfaceResult:
        ...


class VSCodeExtensionInterface(InterfaceAdapter):
    """VS Code extension interface abstraction."""

    @abstractmethod
    def activate(self) -> None:
        ...

    @abstractmethod
    def send_notification(self, event: InterfaceEvent) -> None:
        ...


class InterfaceManagerInterface(ABC):
    """Manager for interface adapter orchestration."""

    @abstractmethod
    def register_interface(self, interface_id: str, interface: InterfaceAdapter) -> None:
        ...

    @abstractmethod
    def get_interface(self, interface_id: str) -> InterfaceAdapter:
        ...

    @abstractmethod
    def list_interfaces(self) -> list[str]:
        ...

    @abstractmethod
    def set_router(self, router: "InterfaceRouter") -> None:
        ...

    @abstractmethod
    def route_request(self, request: InterfaceRequest) -> InterfaceResponse:
        ...

    @abstractmethod
    def get_session_manager(self) -> "InterfaceSessionManager":
        ...

    @abstractmethod
    def get_context_manager(self) -> "InterfaceContextManager":
        ...

    @abstractmethod
    def get_state_manager(self) -> "InterfaceStateManager":
        ...

    @abstractmethod
    def get_event_manager(self) -> "InterfaceEventManager":
        ...

    @abstractmethod
    def get_permission_manager(self) -> "InterfacePermissionManager":
        ...

    @abstractmethod
    def get_configuration_manager(self) -> "InterfaceConfigurationManager":
        ...


class InterfaceRegistryInterface(ABC):
    """Registry contract for interface adapters."""

    @abstractmethod
    def register(self, interface_id: str, interface: InterfaceAdapter) -> None:
        ...

    @abstractmethod
    def resolve(self, interface_id: str) -> InterfaceAdapter:
        ...

    @abstractmethod
    def list_registered(self) -> list[str]:
        ...


class InterfacePermissionManager(ABC):
    """Interface-level permission manager contract."""

    @abstractmethod
    def grant_permission(self, session_id: str, permission_id: str) -> None:
        ...

    @abstractmethod
    def revoke_permission(self, session_id: str, permission_id: str) -> None:
        ...

    @abstractmethod
    def authorize(self, session_id: str, permission_id: str) -> bool:
        ...

    @abstractmethod
    def list_permissions(self, session_id: str) -> list[str]:
        ...


class InterfaceConfigurationManager(ABC):
    """Interface-level configuration manager contract."""

    @abstractmethod
    def get_configuration(self, interface_id: str) -> dict[str, Any]:
        ...

    @abstractmethod
    def configure(self, interface_id: str, configuration: dict[str, Any]) -> None:
        ...

    @abstractmethod
    def validate_configuration(self, interface_id: str, configuration: dict[str, Any]) -> bool:
        ...

    @abstractmethod
    def list_configurations(self) -> list[dict[str, Any]]:
        ...
