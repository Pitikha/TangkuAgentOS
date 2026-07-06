from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Mapping
from typing import Any, Callable

from .types import AgentContext, AgentDescriptor, AgentResourceBudget, AgentSessionInfo
from .messages import AgentMessage, AgentResult, AgentTask


class BaseAgent(ABC):
    """Abstract base class for all agents."""

    @property
    @abstractmethod
    def descriptor(self) -> AgentDescriptor:
        """Return the agent descriptor."""

    @property
    @abstractmethod
    def context(self) -> AgentContext:
        """Return the agent runtime context."""

    @abstractmethod
    def start(self) -> None:
        """Initialize and start the agent."""

    @abstractmethod
    def initialize(self) -> None:
        """Prepare the agent before activation."""

    @abstractmethod
    def activate(self) -> None:
        """Activate the agent for execution."""

    @abstractmethod
    def pause(self) -> None:
        """Pause the agent."""

    @abstractmethod
    def resume(self) -> None:
        """Resume the agent after pause."""

    @abstractmethod
    def sleep(self) -> None:
        """Put the agent into a sleeping state."""

    @abstractmethod
    def restart(self) -> None:
        """Restart the agent."""

    @abstractmethod
    def shutdown(self) -> None:
        """Shutdown the agent."""

    @abstractmethod
    def recover(self) -> None:
        """Recover the agent from failure."""

    @abstractmethod
    def stop(self) -> None:
        """Stop the agent cleanly."""

    @abstractmethod
    def send_message(self, message: AgentMessage) -> None:
        """Send a message to the agent."""

    @abstractmethod
    def handle_task(self, task: AgentTask) -> AgentResult:
        """Handle a task and return a result."""


class AgentManagerInterface(ABC):
    """Abstract manager interface for agent lifecycle and registry."""

    @abstractmethod
    def register_agent(self, agent: BaseAgent) -> None:
        """Register an agent with the runtime."""

    @abstractmethod
    def unregister_agent(self, agent_id: str) -> None:
        """Unregister an agent from the runtime."""

    @abstractmethod
    def load_agent(self, agent_id: str) -> None:
        """Load and initialize an agent."""

    @abstractmethod
    def unload_agent(self, agent_id: str) -> None:
        """Unload an agent from the runtime."""

    @abstractmethod
    def activate_agent(self, agent_id: str) -> None:
        """Activate an agent for execution."""

    @abstractmethod
    def pause_agent(self, agent_id: str) -> None:
        """Pause an active agent."""

    @abstractmethod
    def resume_agent(self, agent_id: str) -> None:
        """Resume a paused agent."""

    @abstractmethod
    def sleep_agent(self, agent_id: str) -> None:
        """Put an agent into sleep mode."""

    @abstractmethod
    def restart_agent(self, agent_id: str) -> None:
        """Restart an agent."""

    @abstractmethod
    def shutdown_agent(self, agent_id: str) -> None:
        """Shutdown an agent gracefully."""

    @abstractmethod
    def recover_agent(self, agent_id: str) -> None:
        """Recover an agent from a failure checkpoint."""

    @abstractmethod
    def get_agent(self, agent_id: str) -> BaseAgent:
        """Return an agent by ID."""

    @abstractmethod
    def lookup_agent(self, agent_id: str) -> BaseAgent | None:
        """Return an agent if registered, otherwise None."""

    @abstractmethod
    def list_agents(self) -> list[BaseAgent]:
        """List all registered agents."""

    @abstractmethod
    def send_message(self, message: AgentMessage) -> None:
        """Deliver a message between agents."""

    @abstractmethod
    def broadcast_message(self, sender_id: str, payload: dict[str, Any]) -> None:
        """Broadcast a message payload to all other agents."""

    @abstractmethod
    def dispatch_task(self, task: AgentTask, callback: Callable[[AgentResult], None] | None = None) -> str:
        """Dispatch a task to the target agent."""

    @abstractmethod
    def health_report(self, agent_id: str) -> dict[str, Any]:
        """Return a health report for a registered agent."""


class AgentContextProvider(ABC):
    """Abstract provider for agent execution contexts."""

    @abstractmethod
    def create_context(self, descriptor: AgentDescriptor) -> AgentContext:
        """Create a fresh context for an agent."""

    @abstractmethod
    def resolve_context(self, agent_id: str) -> AgentContext:
        """Resolve an existing agent context."""
