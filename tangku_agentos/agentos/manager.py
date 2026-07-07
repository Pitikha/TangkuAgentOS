from __future__ import annotations

from typing import Dict, Iterable

from .exceptions import AgentRegistryError
from .interfaces import AgentManagerInterface, BaseAgent
from .registry import AgentRegistry
from .types import AgentContext, AgentDescriptor


class AgentManager(AgentManagerInterface):
    """Runtime manager for agent registration and lifecycle."""

    def __init__(self, registry: AgentRegistry, context_manager: "AgentContextManager") -> None:
        self._registry = registry
        self._context_manager = context_manager

    def register_agent(self, agent: BaseAgent) -> None:
        self._registry.register(agent)

    def unregister_agent(self, agent_id: str) -> None:
        self._context_manager.remove_context(agent_id)
        self._registry.unregister(agent_id)

    def get_agent(self, agent_id: str) -> BaseAgent:
        return self._registry.get(agent_id)

    def list_agents(self) -> list[BaseAgent]:
        return self._registry.list()


class AgentRuntimeRegistry(AgentRegistry):
    """Extended runtime registry with query helpers."""

    def find_by_type(self, agent_type: str) -> list[BaseAgent]:
        return [agent for agent in self.list() if agent.descriptor.agent_type == agent_type]

    def find_by_status(self, status: str) -> list[BaseAgent]:
        return [agent for agent in self.list() if getattr(agent, "state", None) == status]
