from __future__ import annotations

from abc import ABC, abstractmethod

from .models import InterfaceRequest, InterfaceResponse


class InterfaceRouter(ABC):
    """Interface for routing interface requests."""

    @abstractmethod
    def route(self, request: InterfaceRequest) -> InterfaceResponse:
        ...


class DefaultInterfaceRouter(InterfaceRouter):
    def route(self, request: InterfaceRequest) -> InterfaceResponse:
        raise NotImplementedError
