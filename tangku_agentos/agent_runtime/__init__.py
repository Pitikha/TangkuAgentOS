"""
TangkuAgentOS Agent Runtime

A production-grade runtime responsible for managing autonomous AI agents.

This runtime provides:
- Agent lifecycle management
- Agent registration and discovery
- Agent scheduling and execution
- Agent supervision and recovery
- Agent communication via Runtime Communication Framework
- Agent memory and knowledge integration
- Agent planning and reasoning
- Agent tool and skill management
- Multi-agent collaboration
- Agent security and permissions
- Agent monitoring and observability
- Agent persistence

Architecture:
    The Agent Runtime is a first-class runtime managed by the Kernel.
    All agent communication goes through the Runtime Communication Framework.
    Agents are modular, with pluggable components for memory, knowledge, planning, reasoning, and tools.

Example usage:
    from tangku_agentos.agent_runtime import (
        AgentRuntime,
        AgentManager,
        Agent,
        AgentConfig,
        AgentProfile,
        AgentState,
    )
    
    # Create agent runtime
    agent_runtime = AgentRuntime()
    
    # Create and start an agent
    agent = await agent_runtime.create_agent(
        name="research_agent",
        profile="researcher",
        capabilities=["search", "analysis", "reporting"]
    )
    await agent_runtime.start_agent(agent.id)

Author: TangkuAgentOS Team
License: MIT
"""

# Core agent components
from tangku_agentos.agent_runtime.core import (
    Agent,
    AgentConfig,
    AgentProfile,
    AgentIdentity,
    AgentState,
    AgentStatus,
    AgentCapabilities,
    AgentContext,
    AgentMemory,
    AgentKnowledge,
    AgentPlanner,
    AgentReasoner,
    AgentToolManager,
    AgentSkillRegistry,
    AgentPermissionManager,
    AgentCommunicationClient,
    AgentTaskQueue,
    AgentMetrics,
    AgentHealth,
    AgentEventStream,
)

# Agent lifecycle
from tangku_agentos.agent_runtime.lifecycle import (
    AgentLifecycleManager,
    AgentLifecycleState,
    AgentLifecycleTransition,
)

# Agent manager
from tangku_agentos.agent_runtime.manager import (
    AgentManager,
    AgentRegistry,
    AgentScheduler,
    AgentSupervisor,
    AgentRecoveryManager,
)

# Agent components
from tangku_agentos.agent_runtime.components import (
    BaseAgentComponent,
    MemoryComponent,
    KnowledgeComponent,
    PlanningComponent,
    ReasoningComponent,
    ToolComponent,
    SkillComponent,
    CommunicationComponent,
)

# Agent types
from tangku_agentos.agent_runtime.types import (
    AgentID,
    AgentName,
    AgentType,
    AgentVersion,
    Capability,
    SkillID,
    ToolID,
    TaskID,
    MemoryID,
    KnowledgeID,
    PlanID,
    ReasoningID,
)

# Agent runtime
from tangku_agentos.agent_runtime.runtime import AgentRuntime

# Exceptions
from tangku_agentos.agent_runtime.exceptions import (
    AgentError,
    AgentNotFoundError,
    AgentAlreadyExistsError,
    AgentLifecycleError,
    AgentPermissionError,
    AgentExecutionError,
    AgentCommunicationError,
    AgentSchedulingError,
    AgentRecoveryError,
    AgentConfigurationError,
)

# Public API
__all__ = [
    # Core components
    "Agent",
    "AgentConfig",
    "AgentProfile",
    "AgentIdentity",
    "AgentState",
    "AgentStatus",
    "AgentCapabilities",
    "AgentContext",
    "AgentMemory",
    "AgentKnowledge",
    "AgentPlanner",
    "AgentReasoner",
    "AgentToolManager",
    "AgentSkillRegistry",
    "AgentPermissionManager",
    "AgentCommunicationClient",
    "AgentTaskQueue",
    "AgentMetrics",
    "AgentHealth",
    "AgentEventStream",
    # Lifecycle
    "AgentLifecycleManager",
    "AgentLifecycleState",
    "AgentLifecycleTransition",
    # Manager
    "AgentManager",
    "AgentRegistry",
    "AgentScheduler",
    "AgentSupervisor",
    "AgentRecoveryManager",
    # Components
    "BaseAgentComponent",
    "MemoryComponent",
    "KnowledgeComponent",
    "PlanningComponent",
    "ReasoningComponent",
    "ToolComponent",
    "SkillComponent",
    "CommunicationComponent",
    # Types
    "AgentID",
    "AgentName",
    "AgentType",
    "AgentVersion",
    "Capability",
    "SkillID",
    "ToolID",
    "TaskID",
    "MemoryID",
    "KnowledgeID",
    "PlanID",
    "ReasoningID",
    # Runtime
    "AgentRuntime",
    # Exceptions
    "AgentError",
    "AgentNotFoundError",
    "AgentAlreadyExistsError",
    "AgentLifecycleError",
    "AgentPermissionError",
    "AgentExecutionError",
    "AgentCommunicationError",
    "AgentSchedulingError",
    "AgentRecoveryError",
    "AgentConfigurationError",
]
