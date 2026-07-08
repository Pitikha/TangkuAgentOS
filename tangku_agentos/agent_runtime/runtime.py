"""
TangkuAgentOS Agent Runtime - Main Runtime Class

This module provides the AgentRuntime class, which is the main runtime
for managing agents in TangkuAgentOS.

The AgentRuntime is a first-class runtime managed by the Kernel, and it
provides:
- Agent lifecycle management
- Agent registration and discovery
- Agent scheduling and execution
- Agent supervision and recovery
- Agent communication via Runtime Communication Framework
- Integration with other runtimes (Memory, Knowledge, Planning, Reasoning)

Author: TangkuAgentOS Team
License: MIT
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime
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
        AgentIdentity,
        AgentCapabilities,
        AgentContext,
        AgentMemory,
        AgentKnowledge,
    )
    from tangku_agentos.agent_runtime.manager import (
        AgentManager,
        AgentRegistry,
        AgentScheduler,
    )
    from tangku_agentos.agent_runtime.lifecycle import AgentLifecycleManager
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
    from tangku_agentos.memory_engine import MemoryEngine
    from tangku_agentos.knowledge_engine import KnowledgeEngine
    from tangku_agentos.planning_runtime import PlanningRuntime
    from tangku_agentos.reasoning_runtime import ReasoningRuntime
    from tangku_agentos.provider_runtime import ProviderRuntime
    from tangku_agentos.model_runtime import ModelRuntime

logger = logging.getLogger(__name__)


# =============================================================================
# AGENT RUNTIME CONFIGURATION
# =============================================================================

@dataclass
class AgentRuntimeConfig:
    """
    Configuration for the Agent Runtime.
    
    Attributes:
        runtime_id: Unique ID for the runtime.
        name: Human-readable name.
        version: Runtime version.
        max_agents: Maximum number of agents.
        max_parallel_tasks: Maximum number of parallel tasks per agent.
        default_timeout: Default timeout for agent operations.
        default_retry_policy: Default retry policy for tasks.
        enable_persistence: Whether to enable agent persistence.
        persistence_path: Path for persistence storage.
        enable_monitoring: Whether to enable monitoring.
        enable_auto_recovery: Whether to enable automatic recovery.
        check_interval: Interval between health checks.
        metrics: Runtime metrics configuration.
    """

    runtime_id: str = "agent_runtime"
    name: str = "Agent Runtime"
    version: str = "1.0.0"
    max_agents: int = 100
    max_parallel_tasks: int = 10
    default_timeout: float = 300.0
    default_retry_policy: Optional[Dict[str, Any]] = None
    enable_persistence: bool = True
    persistence_path: str = "./data/agent_runtime"
    enable_monitoring: bool = True
    enable_auto_recovery: bool = True
    check_interval: float = 60.0
    metrics: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "runtime_id": self.runtime_id,
            "name": self.name,
            "version": self.version,
            "max_agents": self.max_agents,
            "max_parallel_tasks": self.max_parallel_tasks,
            "default_timeout": self.default_timeout,
            "default_retry_policy": self.default_retry_policy,
            "enable_persistence": self.enable_persistence,
            "persistence_path": self.persistence_path,
            "enable_monitoring": self.enable_monitoring,
            "enable_auto_recovery": self.enable_auto_recovery,
            "check_interval": self.check_interval,
            "metrics": self.metrics,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AgentRuntimeConfig":
        """Create from dictionary."""
        return cls(
            runtime_id=data.get("runtime_id", "agent_runtime"),
            name=data.get("name", "Agent Runtime"),
            version=data.get("version", "1.0.0"),
            max_agents=data.get("max_agents", 100),
            max_parallel_tasks=data.get("max_parallel_tasks", 10),
            default_timeout=data.get("default_timeout", 300.0),
            default_retry_policy=data.get("default_retry_policy"),
            enable_persistence=data.get("enable_persistence", True),
            persistence_path=data.get("persistence_path", "./data/agent_runtime"),
            enable_monitoring=data.get("enable_monitoring", True),
            enable_auto_recovery=data.get("enable_auto_recovery", True),
            check_interval=data.get("check_interval", 60.0),
            metrics=data.get("metrics", {}),
        )


# =============================================================================
# AGENT RUNTIME
# =============================================================================

class AgentRuntime:
    """
    Main runtime for managing agents in TangkuAgentOS.
    
    This is a first-class runtime managed by the Kernel. It provides
    comprehensive agent management capabilities, including:
    
    - Agent lifecycle management (create, start, stop, pause, resume, destroy)
    - Agent registration and discovery
    - Agent scheduling and execution
    - Agent supervision and recovery
    - Agent communication via Runtime Communication Framework
    - Integration with other runtimes (Memory, Knowledge, Planning, Reasoning)
    - Agent persistence
    - Agent monitoring and observability
    
    The AgentRuntime ensures that:
    1. All agent communication goes through the Runtime Communication Framework
    2. Agents never communicate directly with each other
    3. All agent operations are tracked and monitored
    4. Failed agents are automatically recovered (if configured)
    5. Agent state is persisted (if configured)
    
    Thread Safety:
        This class is thread-safe for concurrent access.
    
    Example:
        >>> from tangku_agentos.agent_runtime import AgentRuntime, AgentRuntimeConfig
        >>> 
        >>> # Create configuration
        >>> config = AgentRuntimeConfig(
        ...     runtime_id="agent_runtime",
        ...     max_agents=50,
        ...     enable_auto_recovery=True
        ... )
        >>> 
        >>> # Create runtime
        >>> agent_runtime = AgentRuntime(config=config)
        >>> 
        >>> # Initialize runtime
        >>> await agent_runtime.initialize()
        >>> 
        >>> # Start runtime
        >>> await agent_runtime.start()
        >>> 
        >>> # Create an agent
        >>> agent_id = await agent_runtime.create_agent(
        ...     name="research_agent",
        ...     agent_type="researcher",
        ...     capabilities=["search", "analysis"]
        ... )
        >>> 
        >>> # Start the agent
        >>> await agent_runtime.start_agent(agent_id)
    """

    def __init__(
        self,
        config: Optional[AgentRuntimeConfig] = None,
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
        Initialize the Agent Runtime.
        
        Args:
            config: Runtime configuration.
            message_bus: Message bus for communication.
            event_bus: Event bus for events.
            command_bus: Command bus for commands.
            query_bus: Query bus for queries.
            broadcast_bus: Broadcast bus for broadcasts.
            request_response_bus: Request/response bus for req/reply.
            memory_engine: Memory engine for memory operations.
            knowledge_engine: Knowledge engine for knowledge operations.
            planning_runtime: Planning runtime for planning operations.
            reasoning_runtime: Reasoning runtime for reasoning operations.
            provider_runtime: Provider runtime for provider operations.
            model_runtime: Model runtime for model operations.
        """
        # Configuration
        self._config = config or AgentRuntimeConfig()

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

        # Components
        self._registry: Optional["AgentRegistry"] = None
        self._manager: Optional["AgentManager"] = None
        self._lifecycle_manager: Optional["AgentLifecycleManager"] = None
        self._scheduler: Optional["AgentScheduler"] = None
        self._supervisor: Optional["AgentSupervisor"] = None
        self._recovery_manager: Optional["AgentRecoveryManager"] = None

        # State
        self._running = False
        self._initialized = False
        self._started_at: Optional[datetime] = None

        # Lock for thread safety
        self._lock = asyncio.Lock()

        # Callbacks
        self._on_agent_created: List[Callable[["AgentID"], None]] = []
        self._on_agent_started: List[Callable[["AgentID"], None]] = []
        self._on_agent_stopped: List[Callable[["AgentID"], None]] = []
        self._on_agent_destroyed: List[Callable[["AgentID"], None]] = []
        self._on_agent_failed: List[Callable[["AgentID", str], None]] = []
        self._on_agent_recovered: List[Callable[["AgentID"], None]] = []

        # Metrics
        self._metrics: Dict[str, Any] = {
            "agents_created": 0,
            "agents_started": 0,
            "agents_stopped": 0,
            "agents_destroyed": 0,
            "agents_failed": 0,
            "agents_recovered": 0,
            "tasks_scheduled": 0,
            "tasks_completed": 0,
            "tasks_failed": 0,
            "messages_sent": 0,
            "messages_received": 0,
        }

        logger.info(f"AgentRuntime initialized: {self._config.runtime_id}")

    @property
    def config(self) -> AgentRuntimeConfig:
        """Get the runtime configuration."""
        return self._config

    @property
    def registry(self) -> "AgentRegistry":
        """Get the agent registry."""
        if not self._registry:
            raise RuntimeError("AgentRuntime not initialized")
        return self._registry

    @property
    def manager(self) -> "AgentManager":
        """Get the agent manager."""
        if not self._manager:
            raise RuntimeError("AgentRuntime not initialized")
        return self._manager

    @property
    def lifecycle_manager(self) -> "AgentLifecycleManager":
        """Get the lifecycle manager."""
        if not self._lifecycle_manager:
            raise RuntimeError("AgentRuntime not initialized")
        return self._lifecycle_manager

    @property
    def scheduler(self) -> "AgentScheduler":
        """Get the scheduler."""
        if not self._scheduler:
            raise RuntimeError("AgentRuntime not initialized")
        return self._scheduler

    @property
    def supervisor(self) -> "AgentSupervisor":
        """Get the supervisor."""
        if not self._supervisor:
            raise RuntimeError("AgentRuntime not initialized")
        return self._supervisor

    @property
    def recovery_manager(self) -> "AgentRecoveryManager":
        """Get the recovery manager."""
        if not self._recovery_manager:
            raise RuntimeError("AgentRuntime not initialized")
        return self._recovery_manager

    @property
    def is_running(self) -> bool:
        """Check if the runtime is running."""
        return self._running

    @property
    def is_initialized(self) -> bool:
        """Check if the runtime is initialized."""
        return self._initialized

    # =========================================================================
    # LIFECYCLE METHODS
    # =========================================================================

    async def initialize(self) -> None:
        """
        Initialize the Agent Runtime.
        
        This method initializes all components and prepares the runtime for use.
        """
        if self._initialized:
            return

        async with self._lock:
            if self._initialized:
                return

            try:
                # Initialize components
                await self._initialize_components()

                # Update state
                self._initialized = True

                # Publish initialized event
                await self._publish_runtime_event("runtime.initialized", {})

                logger.info(f"AgentRuntime initialized: {self._config.runtime_id}")

            except Exception as e:
                logger.error(f"AgentRuntime initialization failed: {e}")
                raise

    async def _initialize_components(self) -> None:
        """
        Initialize runtime components.
        """
        # Create lifecycle manager
        self._lifecycle_manager = AgentLifecycleManager(
            event_bus=self._event_bus,
            enable_events=True,
            enable_history=True,
            enable_validation=True,
        )

        # Create registry
        self._registry = AgentRegistry(
            lifecycle_manager=self._lifecycle_manager,
            enable_indexing=True,
        )

        # Create scheduler
        from tangku_agentos.agent_runtime.scheduler import RetryPolicy
        retry_policy = RetryPolicy.from_dict(
            self._config.default_retry_policy or {}
        )
        self._scheduler = AgentScheduler(
            max_parallel=self._config.max_parallel_tasks,
            default_timeout=self._config.default_timeout,
            default_retry_policy=retry_policy,
            enable_metrics=True,
        )

        # Create supervisor
        self._supervisor = AgentSupervisor(
            registry=self._registry,
            lifecycle_manager=self._lifecycle_manager,
            event_bus=self._event_bus,
            check_interval=self._config.check_interval,
            enable_alerts=self._config.enable_monitoring,
        )

        # Create recovery manager
        self._recovery_manager = AgentRecoveryManager(
            supervisor=self._supervisor,
            lifecycle_manager=self._lifecycle_manager,
            agent_manager=None,  # Will be set after manager is created
            check_interval=self._config.check_interval,
            enable_auto_recovery=self._config.enable_auto_recovery,
        )

        # Create manager
        self._manager = AgentManager(
            runtime=self,
            registry=self._registry,
            lifecycle_manager=self._lifecycle_manager,
            scheduler=self._scheduler,
            supervisor=self._supervisor,
            recovery_manager=self._recovery_manager,
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
            provider_runtime=self._provider_runtime,
            model_runtime=self._model_runtime,
        )

        # Set manager in recovery manager
        self._recovery_manager.set_agent_manager(self._manager)

        # Register health checks
        self._register_health_checks()

        # Register message handlers
        await self._register_message_handlers()

    def _register_health_checks(self) -> None:
        """
        Register health checks for the runtime.
        """
        from tangku_agentos.agent_runtime.supervisor import HealthCheck

        # Runtime liveness check
        async def runtime_liveness_check(agent_id: str) -> bool:
            return self._running and self._initialized

        self._supervisor.register_check(HealthCheck(
            name="runtime_liveness",
            description="Check if the Agent Runtime is alive",
            check_func=runtime_liveness_check,
            interval=30.0,
            timeout=5.0,
            critical=True,
        ))

        # Registry health check
        async def registry_health_check(agent_id: str) -> bool:
            if not self._registry:
                return False
            return len(self._registry) <= self._config.max_agents

        self._supervisor.register_check(HealthCheck(
            name="registry_health",
            description="Check if the agent registry is healthy",
            check_func=registry_health_check,
            interval=60.0,
            timeout=5.0,
            critical=True,
        ))

        # Scheduler health check
        async def scheduler_health_check(agent_id: str) -> bool:
            if not self._scheduler:
                return False
            return self._scheduler.get_active_count() <= self._config.max_parallel_tasks

        self._supervisor.register_check(HealthCheck(
            name="scheduler_health",
            description="Check if the scheduler is healthy",
            check_func=scheduler_health_check,
            interval=60.0,
            timeout=5.0,
            critical=False,
        ))

    async def _register_message_handlers(self) -> None:
        """
        Register message handlers for the runtime.
        """
        if not self._command_bus:
            return

        # Register command handlers
        from tangku_agentos.runtime_communication import Command

        # Handle create_agent command
        async def handle_create_agent(command: Command) -> Any:
            payload = command.payload or {}
            config_data = payload.get("config", {})
            profile_data = payload.get("profile", {})

            agent_id = await self._manager.create_agent(
                config=config_data,
                profile=profile_data,
            )
            return {"agent_id": agent_id}

        self._command_bus.register_handler(
            "agent.create",
            handle_create_agent,
            self._config.runtime_id,
        )

        # Handle start_agent command
        async def handle_start_agent(command: Command) -> Any:
            payload = command.payload or {}
            agent_id = payload.get("agent_id")

            if not agent_id:
                raise ValueError("agent_id is required")

            await self._manager.start_agent(agent_id)
            return {"status": "started"}

        self._command_bus.register_handler(
            "agent.start",
            handle_start_agent,
            self._config.runtime_id,
        )

        # Handle stop_agent command
        async def handle_stop_agent(command: Command) -> Any:
            payload = command.payload or {}
            agent_id = payload.get("agent_id")

            if not agent_id:
                raise ValueError("agent_id is required")

            await self._manager.stop_agent(agent_id)
            return {"status": "stopped"}

        self._command_bus.register_handler(
            "agent.stop",
            handle_stop_agent,
            self._config.runtime_id,
        )

        # Handle destroy_agent command
        async def handle_destroy_agent(command: Command) -> Any:
            payload = command.payload or {}
            agent_id = payload.get("agent_id")

            if not agent_id:
                raise ValueError("agent_id is required")

            await self._manager.destroy_agent(agent_id)
            return {"status": "destroyed"}

        self._command_bus.register_handler(
            "agent.destroy",
            handle_destroy_agent,
            self._config.runtime_id,
        )

        # Handle list_agents query
        async def handle_list_agents(query: Command) -> Any:
            payload = query.payload or {}
            filter_data = payload.get("filter", {})

            agents = await self._manager.list_agents(**filter_data)
            return {"agents": [agent.to_dict() for agent in agents]}

        self._command_bus.register_handler(
            "agent.list",
            handle_list_agents,
            self._config.runtime_id,
        )

    async def start(self) -> None:
        """
        Start the Agent Runtime.
        
        This method starts all components and makes the runtime ready for use.
        """
        if self._running:
            return

        async with self._lock:
            if self._running:
                return

            try:
                # Ensure initialized
                if not self._initialized:
                    await self.initialize()

                # Start components
                await self._start_components()

                # Update state
                self._running = True
                self._started_at = datetime.utcnow()

                # Publish started event
                await self._publish_runtime_event("runtime.started", {})

                logger.info(f"AgentRuntime started: {self._config.runtime_id}")

            except Exception as e:
                logger.error(f"AgentRuntime startup failed: {e}")
                raise

    async def _start_components(self) -> None:
        """
        Start runtime components.
        """
        # Start supervisor
        if self._supervisor:
            await self._supervisor.start()

        # Start recovery manager
        if self._recovery_manager:
            await self._recovery_manager.start()

        # Start scheduler
        if self._scheduler:
            await self._scheduler.start()

    async def stop(self, force: bool = False) -> None:
        """
        Stop the Agent Runtime.
        
        Args:
            force: Whether to force stop (skip cleanup).
        """
        if not self._running:
            return

        async with self._lock:
            if not self._running:
                return

            try:
                # Stop components
                if not force:
                    await self._stop_components()

                # Update state
                self._running = False

                # Publish stopped event
                await self._publish_runtime_event("runtime.stopped", {"force": force})

                logger.info(f"AgentRuntime stopped: {self._config.runtime_id}")

            except Exception as e:
                logger.error(f"AgentRuntime shutdown failed: {e}")
                raise

    async def _stop_components(self) -> None:
        """
        Stop runtime components.
        """
        # Stop scheduler
        if self._scheduler:
            await self._scheduler.stop()

        # Stop recovery manager
        if self._recovery_manager:
            await self._recovery_manager.stop()

        # Stop supervisor
        if self._supervisor:
            await self._supervisor.stop()

    async def restart(self) -> None:
        """Restart the Agent Runtime."""
        await self.stop()
        await self.start()
        logger.info(f"AgentRuntime restarted: {self._config.runtime_id}")

    # =========================================================================
    # AGENT MANAGEMENT METHODS
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
    ) -> "AgentID":
        """
        Create a new agent.
        
        Args:
            name: Human-readable name of the agent.
            agent_type: Type of the agent.
            version: Version of the agent.
            description: Description of the agent.
            capabilities: List of agent capabilities.
            permissions: List of agent permissions.
            profile: Agent profile.
            config: Agent configuration.
            auto_start: Whether to auto-start the agent.
            persist: Whether to persist the agent.
            
        Returns:
            ID of the created agent.
        """
        if not self._manager:
            raise RuntimeError("AgentRuntime not initialized")

        agent_id = await self._manager.create_agent(
            name=name,
            agent_type=agent_type,
            version=version,
            description=description,
            capabilities=capabilities,
            permissions=permissions,
            profile=profile,
            config=config,
            auto_start=auto_start,
            persist=persist,
        )

        # Update metrics
        self._metrics["agents_created"] += 1

        # Call callbacks
        for callback in self._on_agent_created:
            try:
                callback(agent_id)
            except Exception as e:
                logger.error(f"Error in agent created callback: {e}")

        # Publish event
        await self._publish_runtime_event(
            "agent.created",
            {"agent_id": agent_id, "name": name, "type": agent_type},
        )

        logger.info(f"Agent created: {agent_id} ({name or agent_id})")
        return agent_id

    async def destroy_agent(self, agent_id: "AgentID", force: bool = False) -> bool:
        """
        Destroy an agent.
        
        Args:
            agent_id: ID of the agent to destroy.
            force: Whether to force destroy (skip cleanup).
            
        Returns:
            True if the agent was destroyed, False if not found.
        """
        if not self._manager:
            raise RuntimeError("AgentRuntime not initialized")

        result = await self._manager.destroy_agent(agent_id, force=force)

        if result:
            # Update metrics
            self._metrics["agents_destroyed"] += 1

            # Call callbacks
            for callback in self._on_agent_destroyed:
                try:
                    callback(agent_id)
                except Exception as e:
                    logger.error(f"Error in agent destroyed callback: {e}")

            # Publish event
            await self._publish_runtime_event(
                "agent.destroyed",
                {"agent_id": agent_id, "force": force},
            )

            logger.info(f"Agent destroyed: {agent_id}")

        return result

    async def start_agent(self, agent_id: "AgentID") -> bool:
        """
        Start an agent.
        
        Args:
            agent_id: ID of the agent to start.
            
        Returns:
            True if the agent was started, False if not found or already running.
        """
        if not self._manager:
            raise RuntimeError("AgentRuntime not initialized")

        result = await self._manager.start_agent(agent_id)

        if result:
            # Update metrics
            self._metrics["agents_started"] += 1

            # Call callbacks
            for callback in self._on_agent_started:
                try:
                    callback(agent_id)
                except Exception as e:
                    logger.error(f"Error in agent started callback: {e}")

            # Publish event
            await self._publish_runtime_event(
                "agent.started",
                {"agent_id": agent_id},
            )

            logger.info(f"Agent started: {agent_id}")

        return result

    async def stop_agent(self, agent_id: "AgentID", force: bool = False) -> bool:
        """
        Stop an agent.
        
        Args:
            agent_id: ID of the agent to stop.
            force: Whether to force stop (skip cleanup).
            
        Returns:
            True if the agent was stopped, False if not found or already stopped.
        """
        if not self._manager:
            raise RuntimeError("AgentRuntime not initialized")

        result = await self._manager.stop_agent(agent_id, force=force)

        if result:
            # Update metrics
            self._metrics["agents_stopped"] += 1

            # Call callbacks
            for callback in self._on_agent_stopped:
                try:
                    callback(agent_id)
                except Exception as e:
                    logger.error(f"Error in agent stopped callback: {e}")

            # Publish event
            await self._publish_runtime_event(
                "agent.stopped",
                {"agent_id": agent_id, "force": force},
            )

            logger.info(f"Agent stopped: {agent_id}")

        return result

    async def pause_agent(self, agent_id: "AgentID") -> bool:
        """
        Pause an agent.
        
        Args:
            agent_id: ID of the agent to pause.
            
        Returns:
            True if the agent was paused, False if not found or not running.
        """
        if not self._manager:
            raise RuntimeError("AgentRuntime not initialized")

        return await self._manager.pause_agent(agent_id)

    async def resume_agent(self, agent_id: "AgentID") -> bool:
        """
        Resume a paused agent.
        
        Args:
            agent_id: ID of the agent to resume.
            
        Returns:
            True if the agent was resumed, False if not found or not paused.
        """
        if not self._manager:
            raise RuntimeError("AgentRuntime not initialized")

        return await self._manager.resume_agent(agent_id)

    async def restart_agent(self, agent_id: "AgentID") -> bool:
        """
        Restart an agent.
        
        Args:
            agent_id: ID of the agent to restart.
            
        Returns:
            True if the agent was restarted, False if not found.
        """
        if not self._manager:
            raise RuntimeError("AgentRuntime not initialized")

        return await self._manager.restart_agent(agent_id)

    async def get_agent(self, agent_id: "AgentID") -> Optional["Agent"]:
        """
        Get an agent by ID.
        
        Args:
            agent_id: ID of the agent to retrieve.
            
        Returns:
            Agent if found, None otherwise.
        """
        if not self._manager:
            raise RuntimeError("AgentRuntime not initialized")

        return self._manager.get_agent(agent_id)

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
        """
        List agents matching the given criteria.
        
        Args:
            name: Name to filter by.
            agent_type: Type to filter by.
            owner: Owner to filter by.
            tags: Tags to filter by.
            capabilities: Capabilities to filter by.
            state: Lifecycle state to filter by.
            status: Status to filter by.
            limit: Maximum number of results to return.
            
        Returns:
            List of matching agents.
        """
        if not self._manager:
            raise RuntimeError("AgentRuntime not initialized")

        return await self._manager.list_agents(
            name=name,
            agent_type=agent_type,
            owner=owner,
            tags=tags,
            capabilities=capabilities,
            state=state,
            status=status,
            limit=limit,
        )

    async def get_agent_info(self, agent_id: "AgentID") -> Optional[Dict[str, Any]]:
        """
        Get information about an agent.
        
        Args:
            agent_id: ID of the agent.
            
        Returns:
            Agent information if found, None otherwise.
        """
        if not self._registry:
            raise RuntimeError("AgentRuntime not initialized")

        info = self._registry.get(agent_id)
        return info.to_dict() if info else None

    async def get_agent_state(self, agent_id: "AgentID") -> Optional[Dict[str, Any]]:
        """
        Get the state of an agent.
        
        Args:
            agent_id: ID of the agent.
            
        Returns:
            Agent state if found, None otherwise.
        """
        if not self._manager:
            raise RuntimeError("AgentRuntime not initialized")

        agent = await self._manager.get_agent(agent_id)
        return agent.state.to_dict() if agent else None

    async def get_agent_metrics(self, agent_id: "AgentID") -> Optional[Dict[str, Any]]:
        """
        Get the metrics of an agent.
        
        Args:
            agent_id: ID of the agent.
            
        Returns:
            Agent metrics if found, None otherwise.
        """
        if not self._manager:
            raise RuntimeError("AgentRuntime not initialized")

        agent = await self._manager.get_agent(agent_id)
        return agent.metrics.to_dict() if agent else None

    async def get_agent_health(self, agent_id: "AgentID") -> Optional[Dict[str, Any]]:
        """
        Get the health of an agent.
        
        Args:
            agent_id: ID of the agent.
            
        Returns:
            Agent health if found, None otherwise.
        """
        if not self._supervisor:
            raise RuntimeError("AgentRuntime not initialized")

        health = self._supervisor.get_health(agent_id)
        return health.to_dict() if health else None

    # =========================================================================
    # TASK MANAGEMENT METHODS
    # =========================================================================

    async def schedule_task(
        self,
        agent_id: "AgentID",
        task_name: str,
        payload: Optional[Dict[str, Any]] = None,
        priority: int = 0,
        scheduled_at: Optional[datetime] = None,
        timeout: Optional[float] = None,
        max_retries: Optional[int] = None,
        retry_delay: Optional[float] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> "TaskID":
        """
        Schedule a task for an agent.
        
        Args:
            agent_id: ID of the agent to schedule the task for.
            task_name: Name of the task.
            payload: Task payload.
            priority: Task priority.
            scheduled_at: When to schedule the task.
            timeout: Timeout for the task.
            max_retries: Maximum number of retries.
            retry_delay: Delay between retries.
            metadata: Additional metadata.
            
        Returns:
            ID of the scheduled task.
        """
        if not self._scheduler:
            raise RuntimeError("AgentRuntime not initialized")

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

        # Update metrics
        self._metrics["tasks_scheduled"] += 1

        # Publish event
        await self._publish_runtime_event(
            "task.scheduled",
            {
                "task_id": task_id,
                "agent_id": agent_id,
                "task_name": task_name,
            },
        )

        logger.info(f"Task scheduled: {task_id} (agent={agent_id}, task={task_name})")
        return task_id

    async def cancel_task(self, task_id: "TaskID") -> bool:
        """
        Cancel a scheduled task.
        
        Args:
            task_id: ID of the task to cancel.
            
        Returns:
            True if the task was cancelled, False if not found.
        """
        if not self._scheduler:
            raise RuntimeError("AgentRuntime not initialized")

        result = await self._scheduler.cancel(task_id)

        if result:
            # Publish event
            await self._publish_runtime_event(
                "task.cancelled",
                {"task_id": task_id},
            )

            logger.info(f"Task cancelled: {task_id}")

        return result

    async def get_task(self, task_id: "TaskID") -> Optional[Dict[str, Any]]:
        """
        Get information about a task.
        
        Args:
            task_id: ID of the task.
            
        Returns:
            Task information if found, None otherwise.
        """
        if not self._scheduler:
            raise RuntimeError("AgentRuntime not initialized")

        task = await self._scheduler.get_task(task_id)
        return task.to_dict() if task else None

    async def list_tasks(
        self,
        agent_id: Optional["AgentID"] = None,
        status: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        List tasks matching the given criteria.
        
        Args:
            agent_id: Filter by agent ID.
            status: Filter by status.
            limit: Maximum number of results to return.
            
        Returns:
            List of matching tasks.
        """
        if not self._scheduler:
            raise RuntimeError("AgentRuntime not initialized")

        tasks = await self._scheduler.list_tasks(
            agent_id=agent_id,
            status=status,
            limit=limit,
        )
        return [task.to_dict() for task in tasks]

    # =========================================================================
    # COMMUNICATION METHODS
    # =========================================================================

    async def send_message(
        self,
        sender_id: str,
        recipient_id: str,
        message_type: str,
        payload: Optional[Dict[str, Any]] = None,
        priority: str = "normal",
        timeout: Optional[float] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Any:
        """
        Send a message from one agent to another.
        
        Args:
            sender_id: ID of the sender agent.
            recipient_id: ID of the recipient agent.
            message_type: Type of the message.
            payload: Message payload.
            priority: Message priority.
            timeout: Timeout in seconds.
            metadata: Additional metadata.
            
        Returns:
            Response from the recipient (if any).
        """
        if not self._message_bus:
            raise RuntimeError("Message bus not configured")

        from tangku_agentos.runtime_communication import Message, MessageType

        message = Message(
            message_type=MessageType.MESSAGE,
            sender_id=sender_id,
            recipient_id=recipient_id,
            payload=payload or {},
            priority=priority,
            timeout=timeout or self._config.default_timeout,
            metadata=metadata or {},
        )

        # Update metrics
        self._metrics["messages_sent"] += 1

        # Publish event
        await self._publish_runtime_event(
            "message.sent",
            {
                "sender_id": sender_id,
                "recipient_id": recipient_id,
                "message_type": message_type,
            },
        )

        # Send the message
        return await self._message_bus.send(message)

    async def broadcast_message(
        self,
        sender_id: str,
        message_type: str,
        payload: Optional[Dict[str, Any]] = None,
        channels: Optional[List[str]] = None,
        priority: str = "normal",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> int:
        """
        Broadcast a message from an agent to multiple recipients.
        
        Args:
            sender_id: ID of the sender agent.
            message_type: Type of the message.
            payload: Message payload.
            channels: Channels to broadcast to.
            priority: Message priority.
            metadata: Additional metadata.
            
        Returns:
            Number of recipients that received the message.
        """
        if not self._broadcast_bus:
            raise RuntimeError("Broadcast bus not configured")

        from tangku_agentos.runtime_communication import Broadcast, MessageType

        broadcast = Broadcast(
            message_type=MessageType.BROADCAST,
            sender_id=sender_id,
            broadcast_type=message_type,
            payload=payload or {},
            channels=channels,
            priority=priority,
            metadata=metadata or {},
        )

        # Update metrics
        self._metrics["messages_sent"] += 1

        # Publish event
        await self._publish_runtime_event(
            "message.broadcast",
            {
                "sender_id": sender_id,
                "message_type": message_type,
                "channels": channels,
            },
        )

        # Broadcast the message
        return await self._broadcast_bus.broadcast(broadcast)

    # =========================================================================
    # CALLBACK REGISTRATION
    # =========================================================================

    def on_agent_created(self, callback: Callable[["AgentID"], None]) -> None:
        """
        Register a callback for agent creation.
        
        Args:
            callback: Callback function to call when an agent is created.
        """
        self._on_agent_created.append(callback)

    def on_agent_started(self, callback: Callable[["AgentID"], None]) -> None:
        """
        Register a callback for agent start.
        
        Args:
            callback: Callback function to call when an agent is started.
        """
        self._on_agent_started.append(callback)

    def on_agent_stopped(self, callback: Callable[["AgentID"], None]) -> None:
        """
        Register a callback for agent stop.
        
        Args:
            callback: Callback function to call when an agent is stopped.
        """
        self._on_agent_stopped.append(callback)

    def on_agent_destroyed(self, callback: Callable[["AgentID"], None]) -> None:
        """
        Register a callback for agent destruction.
        
        Args:
            callback: Callback function to call when an agent is destroyed.
        """
        self._on_agent_destroyed.append(callback)

    def on_agent_failed(self, callback: Callable[["AgentID", str], None]) -> None:
        """
        Register a callback for agent failure.
        
        Args:
            callback: Callback function to call when an agent fails.
        """
        self._on_agent_failed.append(callback)

    def on_agent_recovered(self, callback: Callable[["AgentID"], None]) -> None:
        """
        Register a callback for agent recovery.
        
        Args:
            callback: Callback function to call when an agent is recovered.
        """
        self._on_agent_recovered.append(callback)

    # =========================================================================
    # UTILITY METHODS
    # =========================================================================

    async def _publish_runtime_event(
        self,
        event_type: str,
        data: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Publish a runtime event.
        
        Args:
            event_type: Type of the event.
            data: Event data.
        """
        if not self._event_bus:
            return

        try:
            from tangku_agentos.runtime_communication import Event, MessageType

            event = Event(
                message_type=MessageType.EVENT,
                sender_id=self._config.runtime_id,
                event_type=event_type,
                payload=data or {},
                timestamp=datetime.utcnow(),
            )
            await self._event_bus.publish(event)
        except Exception as e:
            logger.error(f"Failed to publish runtime event: {e}")

    def get_metrics(self) -> Dict[str, Any]:
        """
        Get runtime metrics.
        
        Returns:
            Dictionary of metrics.
        """
        metrics = {
            "runtime": self._metrics,
            "registry": self._registry.get_metrics() if self._registry else {},
            "scheduler": self._scheduler.get_metrics() if self._scheduler else {},
            "supervisor": self._supervisor.get_metrics() if self._supervisor else {},
            "recovery_manager": self._recovery_manager.get_metrics() if self._recovery_manager else {},
        }
        return metrics

    def get_status(self) -> Dict[str, Any]:
        """
        Get runtime status.
        
        Returns:
            Dictionary of status information.
        """
        return {
            "runtime_id": self._config.runtime_id,
            "name": self._config.name,
            "version": self._config.version,
            "is_running": self._running,
            "is_initialized": self._initialized,
            "started_at": self._started_at.isoformat() if self._started_at else None,
            "agents": {
                "total": self._registry.count() if self._registry else 0,
                "running": self._lifecycle_manager._metrics.get("agents_registered", 0) if self._lifecycle_manager else 0,
            } if self._registry else {},
            "tasks": {
                "queued": self._scheduler.get_queue_size() if self._scheduler else 0,
                "active": self._scheduler.get_active_count() if self._scheduler else 0,
            } if self._scheduler else {},
        }

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the runtime to a dictionary.
        
        Returns:
            Dictionary representation of the runtime.
        """
        return {
            "config": self._config.to_dict(),
            "is_running": self._running,
            "is_initialized": self._initialized,
            "started_at": self._started_at.isoformat() if self._started_at else None,
            "status": self.get_status(),
            "metrics": self.get_metrics(),
        }

    def __repr__(self) -> str:
        """Return string representation."""
        return (
            f"AgentRuntime(id={self._config.runtime_id}, "
            f"name={self._config.name}, "
            f"running={self._running}, "
            f"agents={self._registry.count() if self._registry else 0})"
        )
