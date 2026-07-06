from __future__ import annotations

from abc import ABC, abstractmethod
from copy import deepcopy
from dataclasses import asdict
from typing import Any

from tangku_agentos.agentos.agents import Agent
from tangku_agentos.agentos.capabilities import AgentCapability, CapabilityRegistry
from tangku_agentos.agentos.constants import AgentState, AgentStatus, CapabilityType
from tangku_agentos.agentos.messages import AgentMessage, AgentResult, AgentTask
from tangku_agentos.agentos.types import AgentContext, AgentDescriptor

from .models import AgentConfiguration, AgentHealth, AgentMetadata, AgentProfile, AgentStatistics


class BaseSpecializedAgent(Agent, ABC):
    """Common base class for specialized agents built atop AgentOS."""

    def __init__(
        self,
        descriptor: AgentDescriptor,
        context: AgentContext,
        profile: AgentProfile,
        configuration: AgentConfiguration | None = None,
    ) -> None:
        super().__init__(descriptor=descriptor, context=context)
        self._profile = profile
        self._configuration = configuration or AgentConfiguration(name=profile.name)
        self._metadata = AgentMetadata()
        self._statistics = AgentStatistics()
        self._health = AgentHealth(status="ready", message="initialized")
        self._capability_registry = CapabilityRegistry()
        self._capabilities: list[AgentCapability] = []
        self._initialize_default_capabilities()
        self._bootstrap_context()

    @property
    def profile(self) -> AgentProfile:
        return self._profile

    @property
    def configuration(self) -> AgentConfiguration:
        return self._configuration

    @property
    def metadata(self) -> AgentMetadata:
        return self._metadata

    @property
    def statistics(self) -> AgentStatistics:
        return self._statistics

    @property
    def health(self) -> AgentHealth:
        return self._health

    @property
    def capabilities(self) -> list[AgentCapability]:
        return list(self._capabilities)

    def start(self) -> None:
        self.initialize()
        # Activation advances the runtime state to RUNNING.
        self.activate()
        # For specialized agents, `start()` leaves the health reporting at
        # 'ready' to indicate the agent is actively running but not fully
        # marked as healthy until integrations are verified.
        self._statistics.start_count += 1
        self._health.status = "ready"
        self._health.message = "started"

    def initialize(self) -> None:
        super().initialize()
        self._health.status = "ready"
        self._health.message = "initialized"

    def activate(self) -> None:
        super().activate()
        self._health.status = "running"
        self._health.message = "active"

    def pause(self) -> None:
        super().pause()
        self._health.status = "paused"
        self._health.message = "paused"

    def resume(self) -> None:
        super().resume()
        self._health.status = "running"
        self._health.message = "resumed"

    def sleep(self) -> None:
        super().sleep()
        self._health.status = "sleeping"
        self._health.message = "sleeping"

    def restart(self) -> None:
        super().restart()
        self._health.status = "running"
        self._health.message = "restarted"

    def shutdown(self) -> None:
        super().shutdown()
        self._statistics.stop_count += 1
        self._health.status = "stopped"
        self._health.message = "shut down"

    def recover(self) -> None:
        super().recover()
        self._health.status = "running"
        self._health.message = "recovered"

    def stop(self) -> None:
        super().stop()
        self._statistics.stop_count += 1
        self._health.status = "stopped"
        self._health.message = "stopped"

    def handle_message(self, message: AgentMessage) -> None:
        self._statistics.messages_received += 1
        self._health.details["last_message"] = message.message_type

    def execute_task(self, task: AgentTask) -> AgentResult:
        self._statistics.tasks_received += 1
        self._health.details["last_task"] = task.task_id
        self._health.details["last_task_payload"] = deepcopy(task.payload)

        result_payload = deepcopy(task.payload)
        result_payload.setdefault("handled_by", self.descriptor.agent_id)
        result_payload.setdefault("agent_role", self.profile.role)
        result_payload.setdefault("status", "handled")

        self._statistics.tasks_completed += 1
        return AgentResult(
            result_id=f"result-{task.task_id}",
            task_id=task.task_id,
            agent_id=self.descriptor.agent_id,
            status=AgentStatus.COMPLETED,
            payload=result_payload,
            metadata={"agent_role": self.profile.role},
        )

    def register_capability(self, capability: AgentCapability) -> None:
        self._capability_registry.register(capability)
        self._capabilities.append(capability)

    def resolve_capability(self, name: str) -> AgentCapability:
        return self._capability_registry.resolve(name)

    def update_metadata(self, key: str, value: Any) -> None:
        self._metadata[key] = value

    def update_health(self, status: str, message: str = "", details: dict[str, Any] | None = None) -> None:
        self._health.status = status
        self._health.message = message
        if details is not None:
            self._health.details.update(details)

    def _initialize_default_capabilities(self) -> None:
        self._capabilities = []

    def _bootstrap_context(self) -> None:
        self.context.metadata.setdefault("profile", asdict(self.profile))
        self.context.metadata.setdefault("configuration", self.configuration.as_dict())
        self.context.metadata.setdefault("agent_framework", True)


__all__ = ["BaseSpecializedAgent"]
