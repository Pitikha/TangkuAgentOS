from __future__ import annotations

from typing import Optional

from .exceptions import CapabilityDispatcherError
from .interfaces import CapabilityDispatcher, CapabilityEventManager, CapabilityRequestHandler, CapabilityResponseProvider
from .models import CapabilityContext, CapabilityRequest, CapabilityResponse, CapabilityResult
from .resolver import CapabilityResolver


class CapabilityDispatcherImpl(CapabilityDispatcher):
    """Capability dispatcher that resolves and routes requests."""

    def __init__(
        self,
        resolver: CapabilityResolver,
        event_manager: Optional[CapabilityEventManager] = None,
        request_handler: Optional[CapabilityRequestHandler] = None,
        response_provider: Optional[CapabilityResponseProvider] = None,
    ) -> None:
        self._resolver = resolver
        self._event_manager = event_manager
        self._request_handler = request_handler
        self._response_provider = response_provider

    def dispatch(self, request: CapabilityRequest, context: CapabilityContext) -> CapabilityResponse:
        try:
            if self._event_manager:
                self._event_manager.publish("capability.requested", {"request_id": request.request_id, "capability": request.capability_name})

            capability = self._resolver.resolve(request)

            if self._event_manager:
                self._event_manager.publish("capability.resolved", {"request_id": request.request_id, "capability": capability.name})

            if self._request_handler:
                response = self._request_handler.handle(request, context)
            else:
                response = CapabilityResponse(
                    request_id=request.request_id,
                    capability_name=capability.name,
                    status="dispatched",
                    result={"note": "capability resolution complete"},
                )

            if self._response_provider:
                response = self._response_provider.provide(CapabilityResult(
                    result_id=f"result-{request.request_id}",
                    request_id=request.request_id,
                    capability_name=capability.name,
                    status=response.status,
                    payload=response.result,
                    metadata=response.metadata,
                ))

            if self._event_manager:
                self._event_manager.publish("capability.dispatched", {"request_id": request.request_id, "capability": capability.name, "status": response.status})

            return response
        except Exception as error:
            if self._event_manager:
                self._event_manager.publish("capability.failed", {"request_id": request.request_id, "capability": request.capability_name, "error": str(error)})
            raise CapabilityDispatcherError(str(error)) from error
