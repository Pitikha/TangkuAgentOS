from __future__ import annotations

from typing import Any

from tangku_agentos.agentos.messages import AgentMessage

from .base import BaseSpecializedAgent


class AgentCollaborationManager:
    """Lightweight collaboration manager for specialized agents."""

    def __init__(self) -> None:
        self._agents: dict[str, BaseSpecializedAgent] = {}
        self._messages: list[AgentMessage] = []

    def register(self, agent: BaseSpecializedAgent) -> None:
        self._agents[agent.descriptor.agent_id] = agent

    def unregister(self, agent_id: str) -> None:
        self._agents.pop(agent_id, None)

    def discover(self, agent_id: str | None = None) -> list[BaseSpecializedAgent]:
        if agent_id is None:
            return list(self._agents.values())
        return [agent for agent in self._agents.values() if agent.descriptor.agent_id == agent_id]

    def send_message(self, sender: BaseSpecializedAgent, receiver_id: str, payload: dict[str, Any]) -> None:
        message = AgentMessage(
            message_id=f"msg-{sender.descriptor.agent_id}-{receiver_id}",
            sender_id=sender.descriptor.agent_id,
            receiver_id=receiver_id,
            payload=payload,
            message_type="delegation",
        )
        self._messages.append(message)
        receiver = self._agents.get(receiver_id)
        if receiver is not None:
            receiver.handle_message(message)

    def delegate(self, sender: BaseSpecializedAgent, receiver_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        self.send_message(sender, receiver_id, payload)
        return {"recipient_id": receiver_id, "payload": payload}

    def shared_context(self, agent_id: str) -> dict[str, Any]:
        agent = self._agents.get(agent_id)
        if agent is None:
            return {}
        return dict(agent.context.shared_context)

    def share_context(self, agent_id: str, context: dict[str, Any]) -> None:
        agent = self._agents.get(agent_id)
        if agent is not None:
            agent.context.shared_context.update(context)

    def list_messages(self) -> list[AgentMessage]:
        return list(self._messages)


__all__ = ["AgentCollaborationManager"]
