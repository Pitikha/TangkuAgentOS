"""
TangkuAgentOS Agent Runtime - Agent Manager

This module provides the AgentManager class, which is responsible for:
- Creating and destroying agents
- Starting and stopping agents  
- Managing agent lifecycle
- Agent discovery and search
- Agent monitoring and recovery

The AgentManager is the primary interface for managing agents within the Agent Runtime.

Author: TangkuAgentOS Team
License: MIT
"""

from __future__ import annotations

import asyncio
import logging
from typing import (
    Any,
    Callable,
    Dict,
    List,
    Optional,
    TYPE_CHECKING,
)

if TYPE_CHECKING:
    from tangku_agentos.agent_runtime.types import AgentID
    from tangku_agentos.agent_runtime.core import Agent
    from tangku_agentos.agent_runtime.manager import AgentRegistry
    from tangku_agentos.agent_runtime.lifecycle import AgentLifecycleManager
    from tangku_agentos.agent_runtime.scheduler import AgentScheduler
    from tangku_agentos.agent_runtime.supervisor import (
        AgentSupervisor,
        AgentRecoveryManager,
    )
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
    from tangku_agentos.provider_runtime import ProviderRuntime
    from tangku_agentos.model_runtime import ModelRuntime
    from tangku_agentos.agent_runtime.runtime import AgentRuntime

logger = logging.getLogger(__name__)


class AgentManager:
    """
    Manager for creating, managing, and monitoring agents.
    
    This class provides the primary interface for agent operations, including:
    - Agent creation and destruction
    - Agent lifecycle management (start, stop, pause, resume, restart)
    - Agent discovery and search
    - Agent monitoring and recovery
    - Agent communication
    - Agent task management
    
    Thread Safety:
        This class is thread-safe for concurrent access.
    """

    def __init__(
        self,
        runtime: "AgentRuntime",
        registry: "AgentRegistry",
        lifecycle_manager: "AgentLifecycleManager",
        scheduler: "AgentScheduler",
        supervisor: "AgentSupervisor",
        recovery_manager: "AgentRecoveryManager",
        message_bus: Optional["MessageBus"] = None,
        event_bus: Optional["EventBus"] = None,
        command_bus: Optional["CommandBus"] = None,
        query_bus: Optional["QueryBus"] = None,
        broadcast_bus: Optional["BroadcastBus"] = None,
        request_response_bus: Optional["RequestResponseBus"] = None,
        memory_engine: Optional["MemoryEngine"] = None,
        knowledge_engine: Optional["KnowledgeEngine"] = None,
        planning_runtime: Optional["PlanningRuntime"] = None,
        reasoning_runtime: Optional["ReasoningRuntime"] = None,
        provider_runtime: Optional["ProviderRuntime"] = None,
        model_runtime: Optional["ModelRuntime"] = None,
    ):
        """
        Initialize the agent manager.
        """
        # References
        self._runtime = runtime
        self._registry = registry
        self._lifecycle_manager = lifecycle_manager
        self._scheduler = scheduler
        self._supervisor = supervisor
        self._recovery_manager = recovery_manager

        # Communication buses
        self._message_bus = message_bus
        self._event_bus = event_bus
        self._command_bus = command_bus
        self._query_bus = query_bus
        self._broadcast_bus = broadcast_bus
        self._request_response_bus = request_response_bus

        # Runtime integrations
        self._memory_engine = memory_engine
        self._knowledge_engine = knowledge_engine
        self._planning_runtime = planning_runtime
        self._reasoning_runtime = reasoning_runtime
        self._provider_runtime = provider_runtime
        self._model_runtime = model_runtime

        # Agent storage
        self._agents: Dict[str, "Agent"] = {}
        self._lock = asyncio.Lock()

        # Callbacks
        self._on_agent_created: List[Callable[["Agent"], None]] = []
        self._on_agent_destroyed: List[Callable[[str], None]] = []
        self._on_agent_started: List[Callable[[str], None]] = []
        self._on_agent_stopped: List[Callable[[str], None]] = []
        self._on_agent_paused: List[Callable[[str], None]] = []
        self._on_agent_resumed: List[Callable[[str], None]] = []
        self._on_agent_failed: List[Callable[[str, str], None]] = []
        self._on_agent_recovered: List[Callable[[str], None]] = []

        # Metrics
        self._metrics: Dict[str, int] = {
            "agents_created": 0,
            "agents_destroyed": 0,
            "agents_started": 0,
            "agents_stopped": 0,
            "agents_paused": 0,
            "agents_resumed": 0,
            "agents_failed": 0,
            "agents_recovered": 0,
        }

        logger.info("AgentManager initialized")

    @property
    def runtime(self) -> "AgentRuntime":
        """Get the parent runtime."""
        return self._runtime

    @property
    def registry(self) -> "AgentRegistry":
        """Get the agent registry."""
        return self._registry

    @property
    def lifecycle_manager(self) -> "AgentLifecycleManager":
        """Get the lifecycle manager."""
        return self._lifecycle_manager

    @property
    def scheduler(self) -> "AgentScheduler":
        """Get the scheduler."""
        return self._scheduler

    @property
    def supervisor(self) -> "AgentSupervisor":
        """Get the supervisor."""
        return self._supervisor

    @property
    def recovery_manager(self) -> "AgentRecoveryManager":
        """Get the recovery manager."""
        return self._recovery_manager

    # =========================================================================
    # AGENT CREATION AND DESTRUCTION
    # =========================================================================

    async def create_agent(
        self,
        name: Optional[str] = None,
        agent_type: Optional[str] = None,
        version: str = "1.0.0",
        description: str = "",
        capabilities: Optional[List[str]] = None,
        permissions: Optional[List[str]] = None,
        profile: Optional[Dict[str, Any]] = None,
        config: Optional[Dict[str, Any]] = None,
        auto_start: bool = True,
        persist: bool = True,
    ) -> str:
        """
        Create a new agent.
        
        Returns:
            ID of the created agent.
        """
        from tangku_agentos.agent_runtime.core import (
            Agent,
            AgentConfig,
            AgentIdentity,
            AgentProfile,
        )
        from tangku_agentos.agent_runtime.types import Capability, PermissionType
        from tangku_agentos.agent_runtime.exceptions import AgentAlreadyExistsError
        from tangku_agentos.agent_runtime.manager import AgentInfo
        from datetime import datetime
        import uuid

        async with self._lock:
            # Generate agent ID
            agent_id = f"agent_{uuid.uuid4().hex[:12]}"

            # Check if agent already exists
            if agent_id in self._agents:
                raise AgentAlreadyExistsError(
                    f"Agent already exists: {agent_id}",
                    agent_id=agent_id,
                )

            # Create identity
            identity = AgentIdentity(
                id=agent_id,
                name=name or f"agent_{agent_id[:8]}",
                type=agent_type or "general",
                version=version,
            )

            # Parse capabilities
            capability_set = set()
            if capabilities:
                for cap in capabilities:
                    try:
                        capability_set.add(Capability[cap])
                    except KeyError:
                        logger.warning(f"Unknown capability: {cap}")

            # Parse permissions
            permission_set = set()
            if permissions:
                for perm in permissions:
                    try:
                        permission_set.add(PermissionType[perm])
                    except KeyError:
                        logger.warning(f"Unknown permission: {perm}")

            # Create configuration
            agent_config = AgentConfig(
                identity=identity,
                description=description,
                capabilities=capability_set,
                permissions=permission_set,
                resources=config.get("resources", {}) if config else {},
                settings=config.get("settings", {}) if config else {},
                dependencies=set(config.get("dependencies", []) if config else []),
                timeout=config.get("timeout", self._runtime.config.default_timeout) if config else self._runtime.config.default_timeout,
                max_retries=config.get("max_retries", 3) if config else 3,
                max_parallel_tasks=config.get("max_parallel_tasks", self._runtime.config.max_parallel_tasks) if config else self._runtime.config.max_parallel_tasks,
                auto_start=auto_start,
                persist=persist,
            )

            # Create profile
            agent_profile = AgentProfile.from_dict(profile or {})

            # Create agent
            agent = Agent(
                config=agent_config,
                profile=agent_profile,
                manager=self,
                lifecycle_manager=self._lifecycle_manager,
                message_bus=self._message_bus,
                event_bus=self._event_bus,
                command_bus=self._command_bus,
                query_bus=self._query_bus,
                broadcast_bus=self._broadcast_bus,
                request_response_bus=self._request_response_bus,
                memory_engine=self._memory_engine,
                knowledge_engine=self._knowledge_engine,
                planning_runtime=self._planning_runtime,
                reasoning_runtime=self._reasoning_runtime,
            )

            # Store agent
            self._agents[agent_id] = agent

            # Register with lifecycle manager
            await self._lifecycle_manager.register(agent_id)

            # Register with registry
            from tangku_agentos.agent_runtime.core import AgentCapabilities
            agent_info = AgentInfo(
                agent_id=agent_id,
                name=identity.name,
                type=identity.type,
                version=identity.version,
                config=agent_config,
                profile=agent_profile,
                capabilities=AgentCapabilities(capabilities=capability_set),
                state=None,
                status="CREATED",
                created_at=datetime.utcnow(),
                owner=None,
                tags=set(),
            )
            await self._registry.register(agent_info)

            # Initialize agent
            await agent.initialize()

            # Auto-start if configured
            if auto_start:
                await self.start_agent(agent_id)

            # Update metrics
            self._metrics["agents_created"] += 1

            # Call callbacks
            for callback in self._on_agent_created:
                try:
                    callback(agent)
                except Exception as e:
                    logger.error(f"Error in agent created callback: {e}")

            logger.info(f"Agent created: {agent_id} ({identity.name})")
            return agent_id

    async def destroy_agent(self, agent_id: str, force: bool = False) -> bool:
        """
        Destroy an agent.
        
        Returns:
            True if the agent was destroyed, False if not found.
        """
        async with self._lock:
            if agent_id not in self._agents:
                return False

            agent = self._agents[agent_id]

            try:
                # Stop the agent
                if agent.is_running:
                    await agent.stop(force=force)

                # Unregister from lifecycle manager
                await self._lifecycle_manager.unregister(agent_id)

                # Unregister from registry
                await self._registry.unregister(agent_id)

                # Remove from storage
                del self._agents[agent_id]

                # Update metrics
                self._metrics["agents_destroyed"] += 1

                # Call callbacks
                for callback in self._on_agent_destroyed:
                    try:
                        callback(agent_id)
                    except Exception as e:
                        logger.error(f"Error in agent destroyed callback: {e}")

                logger.info(f"Agent destroyed: {agent_id}")
                return True

            except Exception as e:
                logger.error(f"Error destroying agent {agent_id}: {e}")
                return False

    # =========================================================================
    # AGENT LIFECYCLE MANAGEMENT
    # =========================================================================

    async def start_agent(self, agent_id: str) -> bool:
        """
        Start an agent.
        
        Returns:
            True if the agent was started, False otherwise.
        """
        async with self._lock:
            if agent_id not in self._agents:
                return False

            agent = self._agents[agent_id]

            if agent.is_running:
                return False

            try:
                # Start the agent
                await agent.start()

                # Update registry
                agent_info = self._registry.get(agent_id)
                if agent_info:
                    agent_info.started_at = datetime.utcnow()
                    agent_info.status = "RUNNING"
                    await self._registry.update(agent_info)

                # Update lifecycle
                from tangku_agentos.agent_runtime.types import AgentLifecycleState
                await self._lifecycle_manager.transition(
                    agent_id,
                    AgentLifecycleState.IDLE,
                    reason="started",
                )

                # Update metrics
                self._metrics["agents_started"] += 1

                # Call callbacks
                for callback in self._on_agent_started:
                    try:
                        callback(agent_id)
                    except Exception as e:
                        logger.error(f"Error in agent started callback: {e}")

                logger.info(f"Agent started: {agent_id}")
                return True

            except Exception as e:
                logger.error(f"Error starting agent {agent_id}: {e}")
                return False

    async def stop_agent(self, agent_id: str, force: bool = False) -> bool:
        """
        Stop an agent.
        
        Returns:
            True if the agent was stopped, False otherwise.
        """
        async with self._lock:
            if agent_id not in self._agents:
                return False

            agent = self._agents[agent_id]

            if not agent.is_running:
                return False

            try:
                # Stop the agent
                await agent.stop(force=force)

                # Update registry
                agent_info = self._registry.get(agent_id)
                if agent_info:
                    agent_info.status = "STOPPED"
                    await self._registry.update(agent_info)

                # Update lifecycle
                from tangku_agentos.agent_runtime.types import AgentLifecycleState
                await self._lifecycle_manager.transition(
                    agent_id,
                    AgentLifecycleState.STOPPED,
                    reason="stopped",
                )

                # Update metrics
                self._metrics["agents_stopped"] += 1

                # Call callbacks
                for callback in self._on_agent_stopped:
                    try:
                        callback(agent_id)
                    except Exception as e:
                        logger.error(f"Error in agent stopped callback: {e}")

                logger.info(f"Agent stopped: {agent_id}")
                return True

            except Exception as e:
                logger.error(f"Error stopping agent {agent_id}: {e}")
                return False

    async def pause_agent(self, agent_id: str) -> bool:
        """
        Pause an agent.
        
        Returns:
            True if the agent was paused, False otherwise.
        """
        async with self._lock:
            if agent_id not in self._agents:
                return False

            agent = self._agents[agent_id]

            if not agent.is_running:
                return False

            try:
                # Pause the agent
                await agent.pause()

                # Update registry
                agent_info = self._registry.get(agent_id)
                if agent_info:
                    agent_info.status = "PAUSED"
                    await self._registry.update(agent_info)

                # Update lifecycle
                from tangku_agentos.agent_runtime.types import AgentLifecycleState
                await self._lifecycle_manager.transition(
                    agent_id,
                    AgentLifecycleState.PAUSED,
                    reason="paused",
                )

                # Update metrics
                self._metrics["agents_paused"] += 1

                # Call callbacks
                for callback in self._on_agent_paused:
                    try:
                        callback(agent_id)
                    except Exception as e:
                        logger.error(f"Error in agent paused callback: {e}")

                logger.info(f"Agent paused: {agent_id}")
                return True

            except Exception as e:
                logger.error(f"Error pausing agent {agent_id}: {e}")
                return False

    async def resume_agent(self, agent_id: str) -> bool:
        """
        Resume a paused agent.
        
        Returns:
            True if the agent was resumed, False otherwise.
        """
        async with self._lock:
            if agent_id not in self._agents:
                return False

            agent = self._agents[agent_id]

            if agent.is_running:
                return False

            try:
                # Resume the agent
                await agent.resume()

                # Update registry
                agent_info = self._registry.get(agent_id)
                if agent_info:
                    agent_info.status = "RUNNING"
                    await self._registry.update(agent_info)

                # Update lifecycle
                from tangku_agentos.agent_runtime.types import AgentLifecycleState
                await self._lifecycle_manager.transition(
                    agent_id,
                    AgentLifecycleState.IDLE,
                    reason="resumed",
                )

                # Update metrics
                self._metrics["agents_resumed"] += 1

                # Call callbacks
                for callback in self._on_agent_resumed:
                    try:
                        callback(agent_id)
                    except Exception as e:
                        logger.error(f"Error in agent resumed callback: {e}")

                logger.info(f"Agent resumed: {agent_id}")
                return True

            except Exception as e:
                logger.error(f"Error resuming agent {agent_id}: {e}")
                return False

    async def restart_agent(self, agent_id: str) -> bool:
        """
        Restart an agent.
        
        Returns:
            True if the agent was restarted, False otherwise.
        """
        async with self._lock:
            if agent_id not in self._agents:
                return False

            try:
                # Restart the agent
                await self._agents[agent_id].restart()

                # Update registry
                agent_info = self._registry.get(agent_id)
                if agent_info:
                    agent_info.status = "RUNNING"
                    await self._registry.update(agent_info)

                # Update lifecycle
                from tangku_agentos.agent_runtime.types import AgentLifecycleState
                await self._lifecycle_manager.transition(
                    agent_id,
                    AgentLifecycleState.IDLE,
                    reason="restarted",
                )

                logger.info(f"Agent restarted: {agent_id}")
                return True

            except Exception as e:
                logger.error(f"Error restarting agent {agent_id}: {e}")
                return False

    # =========================================================================
    # AGENT ACCESS METHODS
    # =========================================================================

    def get_agent(self, agent_id: str) -> Optional["Agent"]:
        """Get an agent by ID."""
        return self._agents.get(agent_id)

    async def list_agents(
        self,
        name: Optional[str] = None,
        agent_type: Optional[str] = None,
        owner: Optional[str] = None,
        tags: Optional[List[str]] = None,
        capabilities: Optional[List[str]] = None,
        state: Optional[str] = None,
        status: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> List["Agent"]:
        """List agents matching the given criteria."""
        # Get agent IDs from registry
        from tangku_agentos.agent_runtime.manager import AgentInfo
        agent_infos = self._registry.search(
            name=name,
            agent_type=agent_type,
            owner=owner,
            tags=set(tags) if tags else None,
            capabilities=set(capabilities) if capabilities else None,
            state=state,
            status=status,
            limit=limit,
        )

        # Get agents from storage
        agents = []
        for info in agent_infos:
            agent = self._agents.get(info.agent_id)
            if agent:
                agents.append(agent)

        return agents

    async def get_agent_info(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """Get information about an agent."""
        agent_info = self._registry.get(agent_id)
        return agent_info.to_dict() if agent_info else None

    async def get_agent_state(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """Get the state of an agent."""
        agent = self.get_agent(agent_id)
        return agent.state.to_dict() if agent else None

    async def get_agent_metrics(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """Get the metrics of an agent."""
        agent = self.get_agent(agent_id)
        return agent.metrics.to_dict() if agent else None

    async def get_agent_health(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """Get the health of an agent."""
        health = self._supervisor.get_health(agent_id)
        return health.to_dict() if health else None

    # =========================================================================
    # TASK MANAGEMENT METHODS
    # =========================================================================

    async def schedule_task(
        self,
        agent_id: str,
        task_name: str,
        payload: Optional[Dict[str, Any]] = None,
        priority: int = 0,
        scheduled_at: Optional[datetime] = None,
        timeout: Optional[float] = None,
        max_retries: Optional[int] = None,
        retry_delay: Optional[float] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Schedule a task for an agent."""
        from datetime import datetime
        task_id = await self._scheduler.schedule(
            agent_id=agent_id,
            name=task_name,
            payload=payload,
            priority=priority,
            scheduled_at=scheduled_at,
            timeout=timeout,
            max_retries=max_retries,
            retry_delay=retry_delay,
            metadata=metadata,
        )
        return task_id

    async def cancel_task(self, task_id: str) -> bool:
        """Cancel a scheduled task."""
        return await self._scheduler.cancel(task_id)

    async def get_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get information about a task."""
        task = await self._scheduler.get_task(task_id)
        return task.to_dict() if task else None

    async def list_tasks(
        self,
        agent_id: Optional[str] = None,
        status: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """List tasks matching the given criteria."""
        from tangku_agentos.agent_runtime.types import TaskStatus

        status_enum = None
        if status:
            try:
                status_enum = TaskStatus[status]
            except KeyError:
                logger.warning(f"Unknown task status: {status}")

        tasks = await self._scheduler.list_tasks(
            agent_id=agent_id,
            status=status_enum,
            limit=limit,
        )
        return [task.to_dict() for task in tasks]

    # =========================================================================
    # CALLBACK REGISTRATION
    # =========================================================================

    def on_agent_created(self, callback: Callable[["Agent"], None]) -> None:
        """Register a callback for agent creation."""
        self._on_agent_created.append(callback)

    def on_agent_destroyed(self, callback: Callable[[str], None]) -> None:
        """Register a callback for agent destruction."""
        self._on_agent_destroyed.append(callback)

    def on_agent_started(self, callback: Callable[[str], None]) -> None:
        """Register a callback for agent start."""
        self._on_agent_started.append(callback)

    def on_agent_stopped(self, callback: Callable[[str], None]) -> None:
        """Register a callback for agent stop."""
        self._on_agent_stopped.append(callback)

    def on_agent_paused(self, callback: Callable[[str], None]) -> None:
        """Register a callback for agent pause."""
        self._on_agent_paused.append(callback)

    def on_agent_resumed(self, callback: Callable[[str], None]) -> None:
        """Register a callback for agent resume."""
        self._on_agent_resumed.append(callback)

    def on_agent_failed(self, callback: Callable[[str, str], None]) -> None:
        """Register a callback for agent failure."""
        self._on_agent_failed.append(callback)

    def on_agent_recovered(self, callback: Callable[[str], None]) -> None:
        """Register a callback for agent recovery."""
        self._on_agent_recovered.append(callback)

    # =========================================================================
    # UTILITY METHODS
    # =========================================================================

    def get_metrics(self) -> Dict[str, Any]:
        """Get manager metrics."""
        return {
            **self._metrics,
            "agents": len(self._agents),
            "agents_running": sum(1 for a in self._agents.values() if a.is_running),
            "agents_initialized": sum(1 for a in self._agents.values() if a.is_initialized),
        }

    def get_status(self) -> Dict[str, Any]:
        """Get manager status."""
        return {
            "agents": len(self._agents),
            "agents_running": sum(1 for a in self._agents.values() if a.is_running),
            "agents_initialized": sum(1 for a in self._agents.values() if a.is_initialized),
        }

    async def clear(self) -> int:
        """Clear all agents."""
        async with self._lock:
            count = len(self._agents)
            for agent_id in list(self._agents.keys()):
                await self.destroy_agent(agent_id, force=True)
            return count

    def shutdown(self) -> None:
        """Shutdown the manager."""
        self._agents.clear()
        self._on_agent_created.clear()
        self._on_agent_destroyed.clear()
        self._on_agent_started.clear()
        self._on_agent_stopped.clear()
        self._on_agent_paused.clear()
        self._on_agent_resumed.clear()
        self._on_agent_failed.clear()
        self._on_agent_recovered.clear()
        self._metrics = {
            "agents_created": 0,
            "agents_destroyed": 0,
            "agents_started": 0,
            "agents_stopped": 0,
            "agents_paused": 0,
            "agents_resumed": 0,
            "agents_failed": 0,
            "agents_recovered": 0,
        }
        logger.info("AgentManager shutdown complete")

    def __len__(self) -> int:
        """Get the number of managed agents."""
        return len(self._agents)

    def __contains__(self, agent_id: str) -> bool:
        """Check if an agent is managed."""
        return agent_id in self._agents

    def __iter__(self):
        """Iterate over managed agent IDs."""
        return iter(self._agents.keys())

    def __repr__(self) -> str:
        """Return string representation."""
        return (
            f"AgentManager(agents={len(self._agents)}, "
            f"running={sum(1 for a in self._agents.values() if a.is_running)})"
        )
