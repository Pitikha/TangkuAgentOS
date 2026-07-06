from __future__ import annotations

from typing import Any

from tangku_agentos.agentos.capabilities import AgentCapability
from tangku_agentos.agentos.constants import CapabilityType
from tangku_agentos.agentos.types import AgentContext, AgentDescriptor

from .base import BaseSpecializedAgent
from .models import AgentConfiguration, AgentMetadata, AgentProfile


class ResearchAgent(BaseSpecializedAgent):
    """Infrastructure-only research specialist."""

    def __init__(
        self,
        descriptor: AgentDescriptor | None = None,
        context: AgentContext | None = None,
        profile: AgentProfile | None = None,
        configuration: AgentConfiguration | None = None,
    ) -> None:
        descriptor = descriptor or AgentDescriptor(agent_id="research-agent", name="Research Agent", agent_type="research")
        context = context or AgentContext(agent_id=descriptor.agent_id, name=descriptor.name, agent_type=descriptor.agent_type)
        profile = profile or AgentProfile(name="Research Agent", role="research", description="Coordinates research tasks")
        super().__init__(descriptor=descriptor, context=context, profile=profile, configuration=configuration)
        self.register_capability(
            AgentCapability(
                name="research",
                description="Coordinates research requests",
                capability_type=CapabilityType.CORE,
                metadata={"kind": "research"},
            )
        )
        self.metadata["specialization"] = "research"


class SupervisorAgent(BaseSpecializedAgent):
    """Infrastructure-only supervisor specialist."""

    def __init__(
        self,
        descriptor: AgentDescriptor | None = None,
        context: AgentContext | None = None,
        profile: AgentProfile | None = None,
        configuration: AgentConfiguration | None = None,
    ) -> None:
        descriptor = descriptor or AgentDescriptor(agent_id="supervisor-agent", name="Supervisor Agent", agent_type="supervisor")
        context = context or AgentContext(agent_id=descriptor.agent_id, name=descriptor.name, agent_type=descriptor.agent_type)
        profile = profile or AgentProfile(name="Supervisor Agent", role="supervisor", description="Coordinates agents")
        super().__init__(descriptor=descriptor, context=context, profile=profile, configuration=configuration)
        self.register_capability(
            AgentCapability(
                name="orchestration",
                description="Coordinates multiple agents",
                capability_type=CapabilityType.CORE,
                metadata={"kind": "supervisor"},
            )
        )
        self.metadata["specialization"] = "supervisor"


class CodingAgent(BaseSpecializedAgent):
    """Infrastructure-only coding specialist."""

    def __init__(
        self,
        descriptor: AgentDescriptor | None = None,
        context: AgentContext | None = None,
        profile: AgentProfile | None = None,
        configuration: AgentConfiguration | None = None,
    ) -> None:
        descriptor = descriptor or AgentDescriptor(agent_id="coding-agent", name="Coding Agent", agent_type="coding")
        context = context or AgentContext(agent_id=descriptor.agent_id, name=descriptor.name, agent_type=descriptor.agent_type)
        profile = profile or AgentProfile(name="Coding Agent", role="coding", description="Coordinates coding tasks")
        super().__init__(descriptor=descriptor, context=context, profile=profile, configuration=configuration)
        self.register_capability(
            AgentCapability(
                name="code_generation",
                description="Coordinates code generation requests",
                capability_type=CapabilityType.CORE,
                metadata={"kind": "coding"},
            )
        )
        self.register_capability(
            AgentCapability(
                name="debugging",
                description="Coordinates debugging requests",
                capability_type=CapabilityType.CORE,
                metadata={"kind": "coding"},
            )
        )
        self.metadata["specialization"] = "coding"


class PlanningAgent(BaseSpecializedAgent):
    """Infrastructure-only planning specialist."""

    def __init__(
        self,
        descriptor: AgentDescriptor | None = None,
        context: AgentContext | None = None,
        profile: AgentProfile | None = None,
        configuration: AgentConfiguration | None = None,
    ) -> None:
        descriptor = descriptor or AgentDescriptor(agent_id="planning-agent", name="Planning Agent", agent_type="planning")
        context = context or AgentContext(agent_id=descriptor.agent_id, name=descriptor.name, agent_type=descriptor.agent_type)
        profile = profile or AgentProfile(name="Planning Agent", role="planning", description="Coordinates planning tasks")
        super().__init__(descriptor=descriptor, context=context, profile=profile, configuration=configuration)
        self.register_capability(
            AgentCapability(
                name="goal_decomposition",
                description="Coordinates goal decomposition",
                capability_type=CapabilityType.CORE,
                metadata={"kind": "planning"},
            )
        )
        self.register_capability(
            AgentCapability(
                name="workflow_generation",
                description="Coordinates workflow generation",
                capability_type=CapabilityType.CORE,
                metadata={"kind": "planning"},
            )
        )
        self.metadata["specialization"] = "planning"


class MemoryAgent(BaseSpecializedAgent):
    """Infrastructure-only memory specialist."""

    def __init__(self, descriptor: AgentDescriptor | None = None, context: AgentContext | None = None, profile: AgentProfile | None = None, configuration: AgentConfiguration | None = None) -> None:
        descriptor = descriptor or AgentDescriptor(agent_id="memory-agent", name="Memory Agent", agent_type="memory")
        context = context or AgentContext(agent_id=descriptor.agent_id, name=descriptor.name, agent_type=descriptor.agent_type)
        profile = profile or AgentProfile(name="Memory Agent", role="memory", description="Coordinates memory runtime")
        super().__init__(descriptor=descriptor, context=context, profile=profile, configuration=configuration)
        self.register_capability(
            AgentCapability(name="memory_orchestration", description="Coordinates memory operations", capability_type=CapabilityType.CORE)
        )
        self.metadata["specialization"] = "memory"


class KnowledgeAgent(BaseSpecializedAgent):
    """Infrastructure-only knowledge specialist."""

    def __init__(self, descriptor: AgentDescriptor | None = None, context: AgentContext | None = None, profile: AgentProfile | None = None, configuration: AgentConfiguration | None = None) -> None:
        descriptor = descriptor or AgentDescriptor(agent_id="knowledge-agent", name="Knowledge Agent", agent_type="knowledge")
        context = context or AgentContext(agent_id=descriptor.agent_id, name=descriptor.name, agent_type=descriptor.agent_type)
        profile = profile or AgentProfile(name="Knowledge Agent", role="knowledge", description="Coordinates knowledge retrieval")
        super().__init__(descriptor=descriptor, context=context, profile=profile, configuration=configuration)
        self.register_capability(
            AgentCapability(name="knowledge_retrieval", description="Coordinates knowledge retrieval", capability_type=CapabilityType.CORE)
        )
        self.metadata["specialization"] = "knowledge"


class WorkspaceAgent(BaseSpecializedAgent):
    """Infrastructure-only workspace specialist."""

    def __init__(self, descriptor: AgentDescriptor | None = None, context: AgentContext | None = None, profile: AgentProfile | None = None, configuration: AgentConfiguration | None = None) -> None:
        descriptor = descriptor or AgentDescriptor(agent_id="workspace-agent", name="Workspace Agent", agent_type="workspace")
        context = context or AgentContext(agent_id=descriptor.agent_id, name=descriptor.name, agent_type=descriptor.agent_type)
        profile = profile or AgentProfile(name="Workspace Agent", role="workspace", description="Coordinates workspace operations")
        super().__init__(descriptor=descriptor, context=context, profile=profile, configuration=configuration)
        self.register_capability(
            AgentCapability(name="workspace_loading", description="Coordinates workspace loading", capability_type=CapabilityType.CORE)
        )
        self.metadata["specialization"] = "workspace"


class ToolAgent(BaseSpecializedAgent):
    """Infrastructure-only tool specialist."""

    def __init__(self, descriptor: AgentDescriptor | None = None, context: AgentContext | None = None, profile: AgentProfile | None = None, configuration: AgentConfiguration | None = None) -> None:
        descriptor = descriptor or AgentDescriptor(agent_id="tool-agent", name="Tool Agent", agent_type="tool")
        context = context or AgentContext(agent_id=descriptor.agent_id, name=descriptor.name, agent_type=descriptor.agent_type)
        profile = profile or AgentProfile(name="Tool Agent", role="tool", description="Coordinates tool operations")
        super().__init__(descriptor=descriptor, context=context, profile=profile, configuration=configuration)
        self.register_capability(
            AgentCapability(name="tool_selection", description="Coordinates tool selection", capability_type=CapabilityType.CORE)
        )
        self.metadata["specialization"] = "tool"


class ModelAgent(BaseSpecializedAgent):
    """Infrastructure-only model specialist."""

    def __init__(self, descriptor: AgentDescriptor | None = None, context: AgentContext | None = None, profile: AgentProfile | None = None, configuration: AgentConfiguration | None = None) -> None:
        descriptor = descriptor or AgentDescriptor(agent_id="model-agent", name="Model Agent", agent_type="model")
        context = context or AgentContext(agent_id=descriptor.agent_id, name=descriptor.name, agent_type=descriptor.agent_type)
        profile = profile or AgentProfile(name="Model Agent", role="model", description="Coordinates model selection")
        super().__init__(descriptor=descriptor, context=context, profile=profile, configuration=configuration)
        self.register_capability(
            AgentCapability(name="model_selection", description="Coordinates model selection", capability_type=CapabilityType.CORE)
        )
        self.metadata["specialization"] = "model"


__all__ = [
    "CodingAgent",
    "KnowledgeAgent",
    "MemoryAgent",
    "ModelAgent",
    "PlanningAgent",
    "ResearchAgent",
    "SupervisorAgent",
    "ToolAgent",
    "WorkspaceAgent",
]
