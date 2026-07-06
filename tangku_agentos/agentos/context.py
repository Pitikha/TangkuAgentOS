from __future__ import annotations

from typing import Any

from .exceptions import AgentRuntimeError
from .types import AgentContext, AgentDescriptor


class AgentContextManager:
    """Manages runtime contexts for agents."""

    def __init__(self) -> None:
        self._contexts: dict[str, AgentContext] = {}

    def create_context(self, descriptor: AgentDescriptor) -> AgentContext:
        if descriptor.agent_id in self._contexts:
            raise AgentRuntimeError(f"Context already exists for agent: {descriptor.agent_id}")
        context = AgentContext(
            agent_id=descriptor.agent_id,
            name=descriptor.name,
            agent_type=descriptor.agent_type,
            version=descriptor.version,
            metadata=descriptor.metadata,
        )
        self._contexts[descriptor.agent_id] = context
        return context

    def resolve_context(self, agent_id: str) -> AgentContext:
        context = self._contexts.get(agent_id)
        if context is None:
            raise AgentRuntimeError(f"Context not found for agent: {agent_id}")
        return context

    def remove_context(self, agent_id: str) -> None:
        self._contexts.pop(agent_id, None)
