"""
TangkuAgentOS Agent Runtime - Agent Manager

This module provides the AgentManager and related classes for managing agents:
- AgentManager: Main manager for agent operations
- AgentRegistry: Registry for tracking all agents
- AgentScheduler: Scheduler for agent tasks
- AgentSupervisor: Supervisor for monitoring agents
- AgentRecoveryManager: Recovery manager for failed agents

The AgentManager is the primary interface for creating, managing, and monitoring agents.

Author: TangkuAgentOS Team
License: MIT
"""

from __future__ import annotations

import asyncio
import heapq
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timedelta
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
        TaskType,
        TaskStatus,
        PermissionType,
    )
    from tangku_agentos.agent_runtime.core import (
        Agent,
        AgentConfig,
        AgentProfile,
        AgentCapabilities,
        AgentContext,
        AgentMemory,
        AgentKnowledge,
    )
    from tangku_agentos.agent_runtime.lifecycle import AgentLifecycleManager
    from tangku_agentos.runtime_communication import (
        MessageBus,
        EventBus,
        CommandBus,
        QueryBus,
        BroadcastBus,
        RequestResponseBus,
    )
    from tangku_agentos.memory_engine import MemoryEngine
    from tangku_agentos.knowledge_engine import KnowledgeEngine
    from tangku_agentos.planning_runtime import PlanningRuntime
    from tangku_agentos.reasoning_runtime import ReasoningRuntime

logger = logging.getLogger(__name__)


# =============================================================================
# AGENT REGISTRY
# =============================================================================

@dataclass
class AgentInfo:
    """
    Information about a registered agent.
    
    Attributes:
        agent_id: Unique ID of the agent.
        name: Human-readable name.
        type: Type of agent.
        version: Version of the agent.
        config: Agent configuration.
        profile: Agent profile.
        capabilities: Agent capabilities.
        state: Current lifecycle state.
        status: Current status.
        created_at: When the agent was created.
        started_at: When the agent was started.
        last_activity: Last activity timestamp.
        metrics: Agent metrics.
        health: Agent health status.
        owner: Owner of the agent.
        tags: Tags for categorization.
    """

    agent_id: "AgentID"
    name: "AgentName"
    type: "AgentType" = "general"
    version: "AgentVersion" = "1.0.0"
    config: Optional["AgentConfig"] = None
    profile: Optional["AgentProfile"] = None
    capabilities: Optional["AgentCapabilities"] = None
    state: Optional["AgentLifecycleState"] = None
    status: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    last_activity: Optional[datetime] = None
    metrics: Dict[str, Any] = field(default_factory=dict)
    health: Dict[str, Any] = field(default_factory=dict)
    owner: Optional[str] = None
    tags: Set[str] = field(default_factory=set)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "agent_id": self.agent_id,
            "name": self.name,
            "type": self.type,
            "version": self.version,
            "config": self.config.to_dict() if self.config else None,
            "profile": self.profile.to_dict() if self.profile else None,
            "capabilities": self.capabilities.to_dict() if self.capabilities else None,
            "state": self.state.name if self.state else None,
            "status": self.status,
            "created_at": self.created_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "last_activity": self.last_activity.isoformat() if self.last_activity else None,
            "metrics": self.metrics,
            "health": self.health,
            "owner": self.owner,
            "tags": list(self.tags),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AgentInfo":
        """Create from dictionary."""
        from tangku_agentos.agent_runtime.core import (
            AgentConfig,
            AgentProfile,
            AgentCapabilities,
        )
        from tangku_agentos.agent_runtime.types import AgentLifecycleState

        config = None
        if "config" in data and data["config"]:
            config = AgentConfig.from_dict(data["config"])

        profile = None
        if "profile" in data and data["profile"]:
            profile = AgentProfile.from_dict(data["profile"])

        capabilities = None
        if "capabilities" in data and data["capabilities"]:
            capabilities = AgentCapabilities.from_dict(data["capabilities"])

        state = None
        if "state" in data and data["state"]:
            state = AgentLifecycleState[data["state"]]

        return cls(
            agent_id=data["agent_id"],
            name=data["name"],
            type=data.get("type", "general"),
            version=data.get("version", "1.0.0"),
            config=config,
            profile=profile,
            capabilities=capabilities,
            state=state,
            status=data.get("status"),
            created_at=datetime.fromisoformat(data["created_at"]),
            started_at=datetime.fromisoformat(data["started_at"])
            if data.get("started_at")
            else None,
            last_activity=datetime.fromisoformat(data["last_activity"])
            if data.get("last_activity")
            else None,
            metrics=data.get("metrics", {}),
            health=data.get("health", {}),
            owner=data.get("owner"),
            tags=set(data.get("tags", [])),
        )


class AgentRegistry:
    """
    Registry for tracking all agents in the Agent Runtime.
    
    This class provides:
    - Agent registration and unregistration
    - Agent lookup by various criteria
    - Agent filtering and search
    - Agent metadata management
    
    Thread Safety:
        This class is thread-safe for concurrent access.
    
    Example:
        >>> from tangku_agentos.agent_runtime.manager import AgentRegistry
        >>> 
        >>> registry = AgentRegistry()
        >>> 
        >>> # Register an agent
        >>> await registry.register(agent_info)
        >>> 
        >>> # Get agent info
        >>> info = registry.get("agent_1")
        >>> 
        >>> # Search agents
        >>> results = registry.search(type="researcher")
    """

    def __init__(
        self,
        lifecycle_manager: Optional["AgentLifecycleManager"] = None,
        enable_indexing: bool = True,
    ):
        """
        Initialize the agent registry.
        
        Args:
            lifecycle_manager: Lifecycle manager for tracking agent states.
            enable_indexing: Whether to enable indexing for fast lookups.
        """
        self._agents: Dict["AgentID", AgentInfo] = {}
        self._lock = asyncio.Lock()
        self._lifecycle_manager = lifecycle_manager
        self._enable_indexing = enable_indexing

        # Indexes for fast lookups
        self._name_index: Dict[str, "AgentID"] = {}
        self._type_index: Dict[str, Set["AgentID"]] = {}
        self._owner_index: Dict[str, Set["AgentID"]] = {}
        self._tag_index: Dict[str, Set["AgentID"]] = {}
        self._capability_index: Dict[str, Set["AgentID"]] = {}
        self._state_index: Dict[str, Set["AgentID"]] = {}
        self._status_index: Dict[str, Set["AgentID"]] = {}

        # Callbacks
        self._on_register: List[Callable[[AgentInfo], None]] = []
        self._on_unregister: List[Callable[[AgentInfo], None]] = []

        # Metrics
        self._metrics: Dict[str, Any] = {
            "agents_registered": 0,
            "agents_unregistered": 0,
            "agents_active": 0,
            "agents_by_type": {},
            "agents_by_owner": {},
        }

        logger.info("AgentRegistry initialized")

    async def register(self, agent_info: AgentInfo) -> None:
        """
        Register an agent with the registry.
        
        Args:
            agent_info: Information about the agent to register.
            
        Raises:
            AgentAlreadyExistsError: If an agent with the same ID already exists.
        """
        from tangku_agentos.agent_runtime.exceptions import AgentAlreadyExistsError

        async with self._lock:
            if agent_info.agent_id in self._agents:
                raise AgentAlreadyExistsError(
                    f"Agent already exists: {agent_info.agent_id}",
                    agent_id=agent_info.agent_id,
                )

            self._agents[agent_info.agent_id] = agent_info
            self._update_indexes(agent_info)
            self._metrics["agents_registered"] += 1
            self._metrics["agents_active"] += 1

            # Update type metrics
            if agent_info.type not in self._metrics["agents_by_type"]:
                self._metrics["agents_by_type"][agent_info.type] = 0
            self._metrics["agents_by_type"][agent_info.type] += 1

            # Update owner metrics
            if agent_info.owner and agent_info.owner not in self._metrics["agents_by_owner"]:
                self._metrics["agents_by_owner"][agent_info.owner] = 0
            if agent_info.owner:
                self._metrics["agents_by_owner"][agent_info.owner] += 1

            logger.debug(f"Agent registered: {agent_info.agent_id} ({agent_info.name})")

            # Call callbacks
            for callback in self._on_register:
                try:
                    callback(agent_info)
                except Exception as e:
                    logger.error(f"Error in register callback: {e}")

    async def unregister(self, agent_id: "AgentID") -> Optional[AgentInfo]:
        """
        Unregister an agent from the registry.
        
        Args:
            agent_id: ID of the agent to unregister.
            
        Returns:
            AgentInfo if the agent was found and unregistered, None otherwise.
        """
        async with self._lock:
            if agent_id not in self._agents:
                return None

            agent_info = self._agents[agent_id]
            self._remove_from_indexes(agent_info)
            del self._agents[agent_id]
            self._metrics["agents_unregistered"] += 1
            self._metrics["agents_active"] -= 1

            # Update type metrics
            if agent_info.type in self._metrics["agents_by_type"]:
                self._metrics["agents_by_type"][agent_info.type] -= 1
                if self._metrics["agents_by_type"][agent_info.type] <= 0:
                    del self._metrics["agents_by_type"][agent_info.type]

            # Update owner metrics
            if agent_info.owner and agent_info.owner in self._metrics["agents_by_owner"]:
                self._metrics["agents_by_owner"][agent_info.owner] -= 1
                if self._metrics["agents_by_owner"][agent_info.owner] <= 0:
                    del self._metrics["agents_by_owner"][agent_info.owner]

            logger.debug(f"Agent unregistered: {agent_id}")

            # Call callbacks
            for callback in self._on_unregister:
                try:
                    callback(agent_info)
                except Exception as e:
                    logger.error(f"Error in unregister callback: {e}")

            return agent_info

    async def update(self, agent_info: AgentInfo) -> bool:
        """
        Update agent information in the registry.
        
        Args:
            agent_info: Updated agent information.
            
        Returns:
            True if the agent was updated, False if not found.
        """
        async with self._lock:
            if agent_info.agent_id not in self._agents:
                return False

            # Remove old indexes
            old_info = self._agents[agent_info.agent_id]
            self._remove_from_indexes(old_info)

            # Update agent info
            self._agents[agent_info.agent_id] = agent_info
            self._update_indexes(agent_info)

            logger.debug(f"Agent updated: {agent_info.agent_id}")
            return True

    def _update_indexes(self, agent_info: AgentInfo) -> None:
        """Update all indexes for an agent."""
        if not self._enable_indexing:
            return

        # Name index
        self._name_index[agent_info.name.lower()] = agent_info.agent_id

        # Type index
        if agent_info.type not in self._type_index:
            self._type_index[agent_info.type] = set()
        self._type_index[agent_info.type].add(agent_info.agent_id)

        # Owner index
        if agent_info.owner:
            if agent_info.owner not in self._owner_index:
                self._owner_index[agent_info.owner] = set()
            self._owner_index[agent_info.owner].add(agent_info.agent_id)

        # Tag index
        for tag in agent_info.tags:
            if tag not in self._tag_index:
                self._tag_index[tag] = set()
            self._tag_index[tag].add(agent_info.agent_id)

        # Capability index
        if agent_info.capabilities:
            for capability in agent_info.capabilities.capabilities:
                cap_str = capability.value if hasattr(capability, 'value') else str(capability)
                if cap_str not in self._capability_index:
                    self._capability_index[cap_str] = set()
                self._capability_index[cap_str].add(agent_info.agent_id)

        # State index
        if agent_info.state:
            state_str = agent_info.state.name if hasattr(agent_info.state, 'name') else str(agent_info.state)
            if state_str not in self._state_index:
                self._state_index[state_str] = set()
            self._state_index[state_str].add(agent_info.agent_id)

        # Status index
        if agent_info.status:
            if agent_info.status not in self._status_index:
                self._status_index[agent_info.status] = set()
            self._status_index[agent_info.status].add(agent_info.agent_id)

    def _remove_from_indexes(self, agent_info: AgentInfo) -> None:
        """Remove an agent from all indexes."""
        if not self._enable_indexing:
            return

        # Name index
        if agent_info.name.lower() in self._name_index:
            del self._name_index[agent_info.name.lower()]

        # Type index
        if agent_info.type in self._type_index:
            self._type_index[agent_info.type].discard(agent_info.agent_id)
            if not self._type_index[agent_info.type]:
                del self._type_index[agent_info.type]

        # Owner index
        if agent_info.owner and agent_info.owner in self._owner_index:
            self._owner_index[agent_info.owner].discard(agent_info.agent_id)
            if not self._owner_index[agent_info.owner]:
                del self._owner_index[agent_info.owner]

        # Tag index
        for tag in agent_info.tags:
            if tag in self._tag_index:
                self._tag_index[tag].discard(agent_info.agent_id)
                if not self._tag_index[tag]:
                    del self._tag_index[tag]

        # Capability index
        if agent_info.capabilities:
            for capability in agent_info.capabilities.capabilities:
                cap_str = capability.value if hasattr(capability, 'value') else str(capability)
                if cap_str in self._capability_index:
                    self._capability_index[cap_str].discard(agent_info.agent_id)
                    if not self._capability_index[cap_str]:
                        del self._capability_index[cap_str]

        # State index
        if agent_info.state:
            state_str = agent_info.state.name if hasattr(agent_info.state, 'name') else str(agent_info.state)
            if state_str in self._state_index:
                self._state_index[state_str].discard(agent_info.agent_id)
                if not self._state_index[state_str]:
                    del self._state_index[state_str]

        # Status index
        if agent_info.status and agent_info.status in self._status_index:
            self._status_index[agent_info.status].discard(agent_info.agent_id)
            if not self._status_index[agent_info.status]:
                del self._status_index[agent_info.status]

    def get(self, agent_id: "AgentID") -> Optional[AgentInfo]:
        """
        Get agent information by ID.
        
        Args:
            agent_id: ID of the agent.
            
        Returns:
            AgentInfo if found, None otherwise.
        """
        return self._agents.get(agent_id)

    def get_by_name(self, name: str) -> Optional[AgentInfo]:
        """
        Get agent information by name.
        
        Args:
            name: Name of the agent.
            
        Returns:
            AgentInfo if found, None otherwise.
        """
        agent_id = self._name_index.get(name.lower())
        return self._agents.get(agent_id) if agent_id else None

    def list_all(self) -> List[AgentInfo]:
        """
        List all registered agents.
        
        Returns:
            List of all AgentInfo objects.
        """
        return list(self._agents.values())

    def list_by_type(self, agent_type: str) -> List[AgentInfo]:
        """
        List agents by type.
        
        Args:
            agent_type: Type of agents to list.
            
        Returns:
            List of AgentInfo objects of the specified type.
        """
        agent_ids = self._type_index.get(agent_type, set())
        return [self._agents[aid] for aid in agent_ids if aid in self._agents]

    def list_by_owner(self, owner: str) -> List[AgentInfo]:
        """
        List agents by owner.
        
        Args:
            owner: Owner of the agents.
            
        Returns:
            List of AgentInfo objects owned by the specified owner.
        """
        agent_ids = self._owner_index.get(owner, set())
        return [self._agents[aid] for aid in agent_ids if aid in self._agents]

    def list_by_tag(self, tag: str) -> List[AgentInfo]:
        """
        List agents by tag.
        
        Args:
            tag: Tag to filter by.
            
        Returns:
            List of AgentInfo objects with the specified tag.
        """
        agent_ids = self._tag_index.get(tag, set())
        return [self._agents[aid] for aid in agent_ids if aid in self._agents]

    def list_by_capability(self, capability: str) -> List[AgentInfo]:
        """
        List agents by capability.
        
        Args:
            capability: Capability to filter by.
            
        Returns:
            List of AgentInfo objects with the specified capability.
        """
        agent_ids = self._capability_index.get(capability, set())
        return [self._agents[aid] for aid in agent_ids if aid in self._agents]

    def list_by_state(self, state: str) -> List[AgentInfo]:
        """
        List agents by lifecycle state.
        
        Args:
            state: Lifecycle state to filter by.
            
        Returns:
            List of AgentInfo objects in the specified state.
        """
        agent_ids = self._state_index.get(state, set())
        return [self._agents[aid] for aid in agent_ids if aid in self._agents]

    def list_by_status(self, status: str) -> List[AgentInfo]:
        """
        List agents by status.
        
        Args:
            status: Status to filter by.
            
        Returns:
            List of AgentInfo objects with the specified status.
        """
        agent_ids = self._status_index.get(status, set())
        return [self._agents[aid] for aid in agent_ids if aid in self._agents]

    def search(
        self,
        name: Optional[str] = None,
        agent_type: Optional[str] = None,
        owner: Optional[str] = None,
        tags: Optional[Set[str]] = None,
        capabilities: Optional[Set[str]] = None,
        state: Optional[str] = None,
        status: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> List[AgentInfo]:
        """
        Search for agents matching the given criteria.
        
        Args:
            name: Name to search for (partial match).
            agent_type: Type of agent to filter by.
            owner: Owner to filter by.
            tags: Set of tags to filter by (AND logic).
            capabilities: Set of capabilities to filter by (AND logic).
            state: Lifecycle state to filter by.
            status: Status to filter by.
            limit: Maximum number of results to return.
            
        Returns:
            List of matching AgentInfo objects.
        """
        results = []

        for agent_info in self._agents.values():
            # Filter by name
            if name and name.lower() not in agent_info.name.lower():
                continue

            # Filter by type
            if agent_type and agent_info.type != agent_type:
                continue

            # Filter by owner
            if owner and agent_info.owner != owner:
                continue

            # Filter by tags
            if tags and not tags.issubset(agent_info.tags):
                continue

            # Filter by capabilities
            if capabilities and agent_info.capabilities:
                agent_caps = {
                    c.value if hasattr(c, 'value') else str(c)
                    for c in agent_info.capabilities.capabilities
                }
                if not capabilities.issubset(agent_caps):
                    continue

            # Filter by state
            if state and agent_info.state:
                state_str = agent_info.state.name if hasattr(agent_info.state, 'name') else str(agent_info.state)
                if state_str != state:
                    continue

            # Filter by status
            if status and agent_info.status != status:
                continue

            results.append(agent_info)

            # Apply limit
            if limit and len(results) >= limit:
                break

        return results

    def count(self) -> int:
        """
        Get the total number of registered agents.
        
        Returns:
            Number of registered agents.
        """
        return len(self._agents)

    def count_by_type(self, agent_type: str) -> int:
        """
        Get the number of agents of a specific type.
        
        Args:
            agent_type: Type of agents to count.
            
        Returns:
            Number of agents of the specified type.
        """
        return len(self._type_index.get(agent_type, set()))

    def count_by_owner(self, owner: str) -> int:
        """
        Get the number of agents owned by a specific owner.
        
        Args:
            owner: Owner to count agents for.
            
        Returns:
            Number of agents owned by the specified owner.
        """
        return len(self._owner_index.get(owner, set()))

    def exists(self, agent_id: "AgentID") -> bool:
        """
        Check if an agent exists in the registry.
        
        Args:
            agent_id: ID of the agent to check.
            
        Returns:
            True if the agent exists, False otherwise.
        """
        return agent_id in self._agents

    def on_register(self, callback: Callable[[AgentInfo], None]) -> None:
        """
        Register a callback for agent registration.
        
        Args:
            callback: Callback function to call when an agent is registered.
        """
        self._on_register.append(callback)

    def on_unregister(self, callback: Callable[[AgentInfo], None]) -> None:
        """
        Register a callback for agent unregistration.
        
        Args:
            callback: Callback function to call when an agent is unregistered.
        """
        self._on_unregister.append(callback)

    def get_metrics(self) -> Dict[str, Any]:
        """
        Get registry metrics.
        
        Returns:
            Dictionary of metrics.
        """
        return {
            **self._metrics,
            "total_agents": len(self._agents),
            "types": list(self._type_index.keys()),
            "owners": list(self._owner_index.keys()),
            "tags": list(self._tag_index.keys()),
            "capabilities": list(self._capability_index.keys()),
            "states": list(self._state_index.keys()),
            "statuses": list(self._status_index.keys()),
        }

    def clear(self) -> int:
        """
        Clear all registered agents.
        
        Returns:
            Number of agents cleared.
        """
        async with self._lock:
            count = len(self._agents)
            self._agents.clear()
            self._name_index.clear()
            self._type_index.clear()
            self._owner_index.clear()
            self._tag_index.clear()
            self._capability_index.clear()
            self._state_index.clear()
            self._status_index.clear()
            self._metrics = {
                "agents_registered": 0,
                "agents_unregistered": 0,
                "agents_active": 0,
                "agents_by_type": {},
                "agents_by_owner": {},
            }
            return count

    def shutdown(self) -> None:
        """Shutdown the registry."""
        self._agents.clear()
        self._name_index.clear()
        self._type_index.clear()
        self._owner_index.clear()
        self._tag_index.clear()
        self._capability_index.clear()
        self._state_index.clear()
        self._status_index.clear()
        self._on_register.clear()
        self._on_unregister.clear()
        self._metrics = {
            "agents_registered": 0,
            "agents_unregistered": 0,
            "agents_active": 0,
            "agents_by_type": {},
            "agents_by_owner": {},
        }
        logger.info("AgentRegistry shutdown complete")

    def __len__(self) -> int:
        """Get the number of registered agents."""
        return len(self._agents)

    def __contains__(self, agent_id: "AgentID") -> bool:
        """Check if an agent is registered."""
        return agent_id in self._agents

    def __iter__(self):
        """Iterate over registered agent IDs."""
        return iter(self._agents.keys())

    def __repr__(self) -> str:
        """Return string representation."""
        return (
            f"AgentRegistry(agents={len(self._agents)}, "
            f"types={len(self._type_index)}, "
            f"owners={len(self._owner_index)})"
        )
