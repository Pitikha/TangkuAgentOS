from __future__ import annotations

from typing import Dict

from .exceptions import AgentRegistryError
from .interfaces import BaseAgent
from .types import AgentDescriptor


class AgentRegistry:
    """Registry for managing agent registrations."""

    def __init__(self) -> None:
        self._agents: Dict[str, BaseAgent] = {}

    def register(self, agent: BaseAgent) -> None:
        agent_id = agent.descriptor.agent_id
        if not agent_id:
            raise AgentRegistryError("Agent identifier must be provided.")
        if agent_id in self._agents:
            raise AgentRegistryError(f"Agent already registered: {agent_id}")
        self._agents[agent_id] = agent

    def unregister(self, agent_id: str) -> None:
        if agent_id not in self._agents:
            raise AgentRegistryError(f"Agent not found: {agent_id}")
        del self._agents[agent_id]

    def get(self, agent_id: str) -> BaseAgent:
        agent = self._agents.get(agent_id)
        if agent is None:
            raise AgentRegistryError(f"Agent not found: {agent_id}")
        return agent

    def list(self) -> list[BaseAgent]:
        return list(self._agents.values())
