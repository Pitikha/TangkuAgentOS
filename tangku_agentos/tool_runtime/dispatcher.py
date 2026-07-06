from __future__ import annotations

from .interfaces import ToolDispatcher
from .models import ToolRequest, ToolResponse, ToolResult, ToolStatus


class ToolDispatcher(ToolDispatcher):
    """Dispatch a request to a tool with a standard response envelope."""

    def dispatch(self, request: ToolRequest) -> ToolResponse:
        return ToolResponse(
            request_id=request.request_id,
            tool_id=request.tool_id,
            status=ToolStatus.AVAILABLE,
            result=ToolResult(result_id=request.request_id, output=request.payload),
        )
