from __future__ import annotations

from typing import Any

from .context import InterfaceContextManager
from .events import InterfaceEventManager
from .interfaces import (
    InterfaceConfigurationManager,
    InterfaceManagerInterface,
    InterfacePermissionManager,
    InterfaceRouter,
    InterfaceSessionManager,
    InterfaceStateManager,
)
from .models import InterfaceRequest, InterfaceResponse
from .registry import InterfaceRegistry


class InterfaceManager(InterfaceManagerInterface):
    """Manager for registered interface channels."""

    def __init__(
        self,
        registry: InterfaceRegistry,
        router: InterfaceRouter | None = None,
        session_manager: InterfaceSessionManager | None = None,
        context_manager: InterfaceContextManager | None = None,
        state_manager: InterfaceStateManager | None = None,
        event_manager: InterfaceEventManager | None = None,
        permission_manager: InterfacePermissionManager | None = None,
        configuration_manager: InterfaceConfigurationManager | None = None,
    ) -> None:
        self._registry = registry
        self._router = router
        self._session_manager = session_manager
        self._context_manager = context_manager
        self._state_manager = state_manager
        self._event_manager = event_manager
        self._permission_manager = permission_manager
        self._configuration_manager = configuration_manager

    def register_interface(self, interface_id: str, interface: Any) -> None:
        self._registry.register(interface_id, interface)

    def get_interface(self, interface_id: str) -> Any:
        return self._registry.resolve(interface_id)

    def list_interfaces(self) -> list[str]:
        return self._registry.list_registered()

    def set_router(self, router: InterfaceRouter) -> None:
        self._router = router

    def route_request(self, request: InterfaceRequest) -> InterfaceResponse:
        if self._router is not None:
            return self._router.route(request)

        interface = self._registry.resolve(request.interface_type.value)
        return interface.handle_request(request)

    def get_session_manager(self) -> InterfaceSessionManager:
        if self._session_manager is None:
            raise RuntimeError("Interface session manager is not configured.")
        return self._session_manager

    def get_context_manager(self) -> InterfaceContextManager:
        if self._context_manager is None:
            raise RuntimeError("Interface context manager is not configured.")
        return self._context_manager

    def get_state_manager(self) -> InterfaceStateManager:
        if self._state_manager is None:
            raise RuntimeError("Interface state manager is not configured.")
        return self._state_manager

    def get_event_manager(self) -> InterfaceEventManager:
        if self._event_manager is None:
            raise RuntimeError("Interface event manager is not configured.")
        return self._event_manager

    def get_permission_manager(self) -> InterfacePermissionManager:
        if self._permission_manager is None:
            raise RuntimeError("Interface permission manager is not configured.")
        return self._permission_manager

    def get_configuration_manager(self) -> InterfaceConfigurationManager:
        if self._configuration_manager is None:
            raise RuntimeError("Interface configuration manager is not configured.")
        return self._configuration_manager
