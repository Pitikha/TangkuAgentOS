"""
TangkuAgentOS Agent Runtime - Core Agent Components

This module defines the core components of the Agent Runtime:
- Agent: The main agent class
- AgentConfig: Agent configuration
- AgentProfile: Agent profile
- AgentIdentity: Agent identity
- AgentState: Agent state
- AgentStatus: Agent status
- AgentCapabilities: Agent capabilities
- AgentContext: Agent context
- AgentMemory: Agent memory
- AgentKnowledge: Agent knowledge
- AgentPlanner: Agent planner
- AgentReasoner: Agent reasoner
- AgentToolManager: Agent tool manager
- AgentSkillRegistry: Agent skill registry
- AgentPermissionManager: Agent permission manager
- AgentCommunicationClient: Agent communication client
- AgentTaskQueue: Agent task queue
- AgentMetrics: Agent metrics
- AgentHealth: Agent health
- AgentEventStream: Agent event stream

Author: TangkuAgentOS Team
License: MIT
"""

from __future__ import annotations

import asyncio
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from typing import (
    Any,
    Callable,
    Dict,
    List,
    Optional,
    Set,
    Tuple,
    Union,
    TYPE_CHECKING,
)
import uuid

if TYPE_CHECKING:
    from tangku_agentos.runtime_communication import (
        MessageBus,
        EventBus,
        CommandBus,
        QueryBus,
        BroadcastBus,
        RequestResponseBus,
        Message,
        Event,
        Command,
        Query,
    )
    from tangku_agentos.runtime_communication.integration import (
        BaseRuntime,
        SystemEvents,
        SystemCommands,
        SystemQueries,
    )
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
        AgentLifecycleState,
        AgentStatus,
        TaskType,
        TaskStatus,
        MemoryType,
        KnowledgeType,
        PermissionType,
        CommunicationType,
    )
    from tangku_agentos.memory_engine import MemoryEngine
    from tangku_agentos.knowledge_engine import KnowledgeEngine
    from tangku_agentos.planning_runtime import PlanningRuntime
    from tangku_agentos.reasoning_runtime import ReasoningRuntime

logger = logging.getLogger(__name__)


# =============================================================================
# AGENT IDENTITY
# =============================================================================

@dataclass
class AgentIdentity:
    """
    Identity of an agent.
    
    This class represents the unique identity of an agent, including its ID,
    name, type, version, and other identifying information.
    
    Attributes:
        id: Unique identifier for the agent.
        name: Human-readable name of the agent.
        type: Type of the agent (e.g., 'researcher', 'coder').
        version: Version of the agent.
        instance_id: Unique identifier for this specific instance.
        created_at: When the agent was created.
        owner: Owner of the agent.
        tags: Tags for categorization.
    """

    id: "AgentID"
    name: "AgentName"
    type: "AgentType" = "general"
    version: "AgentVersion" = "1.0.0"
    instance_id: "AgentID" = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = field(default_factory=datetime.utcnow)
    owner: Optional[str] = None
    tags: Set[str] = field(default_factory=set)

    def __post_init__(self):
        """Validate identity after initialization."""
        if not self.id:
            self.id = str(uuid.uuid4())
        if not self.name:
            self.name = f"agent_{self.id[:8]}"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "type": self.type,
            "version": self.version,
            "instance_id": self.instance_id,
            "created_at": self.created_at.isoformat(),
            "owner": self.owner,
            "tags": list(self.tags),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AgentIdentity":
        """Create from dictionary."""
        return cls(
            id=data.get("id", str(uuid.uuid4())),
            name=data.get("name", ""),
            type=data.get("type", "general"),
            version=data.get("version", "1.0.0"),
            instance_id=data.get("instance_id", str(uuid.uuid4())),
            created_at=datetime.fromisoformat(data["created_at"])
            if "created_at" in data
            else datetime.utcnow(),
            owner=data.get("owner"),
            tags=set(data.get("tags", [])),
        )

    def __repr__(self) -> str:
        """Return string representation."""
        return f"AgentIdentity(id={self.id}, name={self.name}, type={self.type})"


# =============================================================================
# AGENT CONFIGURATION
# =============================================================================

@dataclass
class AgentConfig:
    """
    Configuration for an agent.
    
    This class contains all the configuration options for an agent,
    including its identity, capabilities, resources, and settings.
    
    Attributes:
        identity: Agent identity.
        description: Description of the agent.
        capabilities: Set of agent capabilities.
        permissions: Set of agent permissions.
        resources: Resource limits for the agent.
        settings: Agent-specific settings.
        dependencies: Dependencies for the agent.
        timeout: Default timeout for agent operations.
        max_retries: Maximum number of retries for failed operations.
        max_parallel_tasks: Maximum number of parallel tasks.
        auto_start: Whether to auto-start the agent.
        persist: Whether to persist the agent state.
    """

    identity: AgentIdentity
    description: str = ""
    capabilities: Set["Capability"] = field(default_factory=set)
    permissions: Set["PermissionType"] = field(default_factory=set)
    resources: Dict[str, Any] = field(default_factory=dict)
    settings: Dict[str, Any] = field(default_factory=dict)
    dependencies: Set[str] = field(default_factory=set)
    timeout: float = 300.0
    max_retries: int = 3
    max_parallel_tasks: int = 5
    auto_start: bool = True
    persist: bool = True

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "identity": self.identity.to_dict(),
            "description": self.description,
            "capabilities": [c.value for c in self.capabilities],
            "permissions": [p.value for p in self.permissions],
            "resources": self.resources,
            "settings": self.settings,
            "dependencies": list(self.dependencies),
            "timeout": self.timeout,
            "max_retries": self.max_retries,
            "max_parallel_tasks": self.max_parallel_tasks,
            "auto_start": self.auto_start,
            "persist": self.persist,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AgentConfig":
        """Create from dictionary."""
        identity_data = data.get("identity", {})
        identity = AgentIdentity.from_dict(identity_data)
        
        capabilities = set()
        for cap in data.get("capabilities", []):
            try:
                capabilities.add(Capability[cap])
            except KeyError:
                logger.warning(f"Unknown capability: {cap}")
        
        permissions = set()
        for perm in data.get("permissions", []):
            try:
                permissions.add(PermissionType[perm])
            except KeyError:
                logger.warning(f"Unknown permission: {perm}")
        
        return cls(
            identity=identity,
            description=data.get("description", ""),
            capabilities=capabilities,
            permissions=permissions,
            resources=data.get("resources", {}),
            settings=data.get("settings", {}),
            dependencies=set(data.get("dependencies", [])),
            timeout=data.get("timeout", 300.0),
            max_retries=data.get("max_retries", 3),
            max_parallel_tasks=data.get("max_parallel_tasks", 5),
            auto_start=data.get("auto_start", True),
            persist=data.get("persist", True),
        )

    def validate(self) -> List[str]:
        """
        Validate the configuration.
        
        Returns:
            List of validation errors.
        """
        errors = []
        
        if not self.identity.id:
            errors.append("Agent ID cannot be empty")
        if not self.identity.name:
            errors.append("Agent name cannot be empty")
        if self.timeout <= 0:
            errors.append("Timeout must be positive")
        if self.max_retries < 0:
            errors.append("Max retries cannot be negative")
        if self.max_parallel_tasks <= 0:
            errors.append("Max parallel tasks must be positive")
        
        return errors

    def __repr__(self) -> str:
        """Return string representation."""
        return f"AgentConfig(id={self.identity.id}, name={self.identity.name})"


# =============================================================================
# AGENT PROFILE
# =============================================================================

@dataclass
class AgentProfile:
    """
    Profile of an agent.
    
    This class defines the personality, behavior, and preferences of an agent.
    
    Attributes:
        type: Type of agent profile.
        personality: Personality traits of the agent.
        behavior: Behavior preferences of the agent.
        preferences: Agent preferences.
        style: Communication and output style.
        language: Preferred language.
        expertise: Areas of expertise.
        limitations: Known limitations.
    """

    type: str = "default"
    personality: Dict[str, float] = field(default_factory=dict)
    behavior: Dict[str, Any] = field(default_factory=dict)
    preferences: Dict[str, Any] = field(default_factory=dict)
    style: Dict[str, Any] = field(default_factory=dict)
    language: str = "english"
    expertise: Set[str] = field(default_factory=set)
    limitations: Set[str] = field(default_factory=set)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "type": self.type,
            "personality": self.personality,
            "behavior": self.behavior,
            "preferences": self.preferences,
            "style": self.style,
            "language": self.language,
            "expertise": list(self.expertise),
            "limitations": list(self.limitations),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AgentProfile":
        """Create from dictionary."""
        return cls(
            type=data.get("type", "default"),
            personality=data.get("personality", {}),
            behavior=data.get("behavior", {}),
            preferences=data.get("preferences", {}),
            style=data.get("style", {}),
            language=data.get("language", "english"),
            expertise=set(data.get("expertise", [])),
            limitations=set(data.get("limitations", [])),
        )

    def __repr__(self) -> str:
        """Return string representation."""
        return f"AgentProfile(type={self.type}, language={self.language})"


# =============================================================================
# AGENT CAPABILITIES
# =============================================================================

@dataclass
class AgentCapabilities:
    """
    Capabilities of an agent.
    
    This class defines what an agent can do, including its skills, tools,
    and resource access.
    
    Attributes:
        capabilities: Set of agent capabilities.
        skills: Set of skill IDs the agent has.
        tools: Set of tool IDs the agent can use.
        resources: Set of resource types the agent can access.
        models: Set of model IDs the agent can use.
        knowledge_sources: Set of knowledge source IDs the agent can access.
    """

    capabilities: Set["Capability"] = field(default_factory=set)
    skills: Set["SkillID"] = field(default_factory=set)
    tools: Set["ToolID"] = field(default_factory=set)
    resources: Set[str] = field(default_factory=set)
    models: Set[str] = field(default_factory=set)
    knowledge_sources: Set[str] = field(default_factory=set)

    def has_capability(self, capability: "Capability") -> bool:
        """Check if the agent has a specific capability."""
        return capability in self.capabilities

    def has_skill(self, skill_id: "SkillID") -> bool:
        """Check if the agent has a specific skill."""
        return skill_id in self.skills

    def has_tool(self, tool_id: "ToolID") -> bool:
        """Check if the agent can use a specific tool."""
        return tool_id in self.tools

    def can_access_resource(self, resource: str) -> bool:
        """Check if the agent can access a specific resource."""
        return resource in self.resources

    def can_use_model(self, model_id: str) -> bool:
        """Check if the agent can use a specific model."""
        return model_id in self.models

    def can_access_knowledge(self, source_id: str) -> bool:
        """Check if the agent can access a specific knowledge source."""
        return source_id in self.knowledge_sources

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "capabilities": [c.value for c in self.capabilities],
            "skills": list(self.skills),
            "tools": list(self.tools),
            "resources": list(self.resources),
            "models": list(self.models),
            "knowledge_sources": list(self.knowledge_sources),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AgentCapabilities":
        """Create from dictionary."""
        capabilities = set()
        for cap in data.get("capabilities", []):
            try:
                capabilities.add(Capability[cap])
            except KeyError:
                logger.warning(f"Unknown capability: {cap}")
        
        return cls(
            capabilities=capabilities,
            skills=set(data.get("skills", [])),
            tools=set(data.get("tools", [])),
            resources=set(data.get("resources", [])),
            models=set(data.get("models", [])),
            knowledge_sources=set(data.get("knowledge_sources", [])),
        )

    def __repr__(self) -> str:
        """Return string representation."""
        return (
            f"AgentCapabilities(capabilities={len(self.capabilities)}, "
            f"skills={len(self.skills)}, tools={len(self.tools)})"
        )
