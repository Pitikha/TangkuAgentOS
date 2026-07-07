from __future__ import annotations

from tangku_agentos.agent_framework import (
    AgentCollaborationManager,
    AgentConfiguration,
    AgentHealth,
    AgentMetadata,
    AgentProfile,
    AgentStatistics,
    BaseSpecializedAgent,
    CodingAgent,
    PlanningAgent,
)
from tangku_agentos.agentos.constants import AgentState, AgentStatus
from tangku_agentos.agentos.messages import AgentTask
from tangku_agentos.agentos.types import AgentContext, AgentDescriptor


class DummyAgent(BaseSpecializedAgent):
    def __init__(self) -> None:
        descriptor = AgentDescriptor(agent_id="dummy", name="Dummy", agent_type="dummy")
        context = AgentContext(agent_id="dummy", name="Dummy", agent_type="dummy")
        profile = AgentProfile(name="Dummy", role="test", description="test agent")
        configuration = AgentConfiguration(name="Dummy", enabled=True)
        super().__init__(descriptor=descriptor, context=context, profile=profile, configuration=configuration)


def test_base_specialized_agent_lifecycle_and_metadata() -> None:
    agent = DummyAgent()

    agent.start()
    assert agent.state == AgentState.RUNNING
    assert agent.profile.name == "Dummy"
    assert agent.configuration.enabled is True
    assert agent.health.status == "ready"

    task = AgentTask(task_id="task-1", agent_id=agent.descriptor.agent_id, payload={"operation": "explain"})
    result = agent.handle_task(task)

    assert result.status == AgentStatus.COMPLETED
    assert result.payload["operation"] == "explain"
    assert agent.statistics.tasks_completed == 1


def test_specialized_agents_expose_specialized_capabilities() -> None:
    coding_agent = CodingAgent()
    planning_agent = PlanningAgent()

    assert coding_agent.profile.role == "coding"
    assert planning_agent.profile.role == "planning"
    assert any(capability.name == "code_generation" for capability in coding_agent.capabilities)
    assert any(capability.name == "goal_decomposition" for capability in planning_agent.capabilities)


def test_collaboration_manager_supports_registration_and_delegation() -> None:
    manager = AgentCollaborationManager()
    agent = DummyAgent()
    manager.register(agent)

    delegated = manager.delegate(agent, "assistant", {"operation": "handoff"})

    assert delegated["recipient_id"] == "assistant"
    assert manager.discover("dummy") == [agent]
