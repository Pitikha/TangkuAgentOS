from __future__ import annotations

import threading
import time
from threading import RLock
from typing import Any, Callable, Dict, Optional

from .exceptions import AgentLifecycleError, AgentRegistryError, AgentRuntimeError
from .interfaces import AgentManagerInterface, BaseAgent
from .messages import AgentTask, AgentMessage, AgentResult
from .registry import AgentRegistry
from .session import AgentSessionManager
from .scheduler import AgentScheduler
from .execution import AgentExecutionEngine
from .types import AgentContext, AgentDescriptor, AgentResourceAllocation, AgentResourceBudget


class AgentManagerImpl(AgentManagerInterface):
    """Concrete implementation of the agent runtime manager."""

    def __init__(
        self,
        registry: AgentRegistry,
        context_manager: "AgentContextManager",
        session_manager: AgentSessionManager,
        scheduler: AgentScheduler,
        execution_engine: AgentExecutionEngine,
    ) -> None:
        self._registry = registry
        self._context_manager = context_manager
        self._session_manager = session_manager
        self._scheduler = scheduler
        self._execution_engine = execution_engine
        self._lock = RLock()

    def register_agent(self, agent: BaseAgent) -> None:
        with self._lock:
            self._registry.register(agent)
            self._context_manager.create_context(agent.descriptor)
            self._set_agent_state(agent, "ready")

    def load_agent(self, agent_id: str) -> None:
        agent = self.get_agent(agent_id)
        if agent.state != "initialized":
            agent.start()
        self._set_agent_state(agent, "loaded")

    def activate_agent(self, agent_id: str) -> None:
        agent = self.get_agent(agent_id)
        if agent.state not in ("initialized", "ready", "paused", "sleeping"):
            raise AgentLifecycleError(f"Agent cannot be activated from state {agent.state}")
        agent.start()
        self._set_agent_state(agent, "running")

    def pause_agent(self, agent_id: str) -> None:
        agent = self.get_agent(agent_id)
        if agent.state != "running":
            raise AgentLifecycleError("Agent must be running to pause.")
        agent._transition_state(agent.state)
        self._set_agent_state(agent, "paused")

    def resume_agent(self, agent_id: str) -> None:
        agent = self.get_agent(agent_id)
        if agent.state != "paused":
            raise AgentLifecycleError("Agent must be paused to resume.")
        agent.start()
        self._set_agent_state(agent, "running")

    def restart_agent(self, agent_id: str) -> None:
        agent = self.get_agent(agent_id)
        agent.stop()
        agent.start()
        self._set_agent_state(agent, "running")

    def shutdown_agent(self, agent_id: str) -> None:
        agent = self.get_agent(agent_id)
        agent.stop()
        self._set_agent_state(agent, "stopped")

    def recover_agent(self, agent_id: str) -> None:
        agent = self.get_agent(agent_id)
        if agent.state != "failed":
            raise AgentLifecycleError("Agent is not in a failed state.")
        agent._transition_state("recovering")
        self._set_agent_state(agent, "running")

    def unregister_agent(self, agent_id: str) -> None:
        with self._lock:
            self._session_manager.remove_session(agent_id)
            self._registry.unregister(agent_id)

    def get_agent(self, agent_id: str) -> BaseAgent:
        return self._registry.get(agent_id)

    def list_agents(self) -> list[BaseAgent]:
        return self._registry.list()

    def lookup_agent(self, agent_id: str) -> Optional[BaseAgent]:
        try:
            return self.get_agent(agent_id)
        except AgentRegistryError:
            return None

    def send_message(self, message: AgentMessage) -> None:
        receiver = self.get_agent(message.receiver_id)
        receiver.send_message(message)

    def broadcast_message(self, sender_id: str, payload: dict[str, Any]) -> None:
        for agent in self.list_agents():
            if agent.descriptor.agent_id != sender_id:
                agent.send_message(
                    AgentMessage(
                        message_id=f"broadcast-{agent.descriptor.agent_id}-{time.time()}",
                        sender_id=sender_id,
                        receiver_id=agent.descriptor.agent_id,
                        payload=payload,
                        message_type="broadcast",
                    )
                )

    def dispatch_task(self, task: AgentTask, callback: Callable[[AgentResult], None] | None = None) -> str:
        agent = self.get_agent(task.agent_id)
        if agent.state != "running":
            raise AgentLifecycleError("Agent must be running to accept tasks.")
        return self._execution_engine.submit_task(agent, task, callback)

    def health_report(self, agent_id: str) -> dict[str, Any]:
        agent = self.get_agent(agent_id)
        return {
            "agent_id": agent_id,
            "state": agent.state,
            "descriptor": agent.descriptor,
        }

    def _set_agent_state(self, agent: BaseAgent, state: str) -> None:
        agent._state = state
