"""
TangkuAgentOS Agent Runtime - Agent Class

This module defines the main Agent class, which represents an autonomous AI agent.

The Agent class is the core of the Agent Runtime, providing:
- Agent identity and configuration
- Agent lifecycle management
- Agent components (memory, knowledge, planner, reasoner, tools, skills)
- Agent communication
- Agent task execution
- Agent state management
- Agent observability

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
        MemoryType,
        KnowledgeType,
        PermissionType,
        CommunicationType,
    )
    from tangku_agentos.agent_runtime.core import (
        AgentConfig,
        AgentProfile,
        AgentIdentity,
        AgentCapabilities,
        AgentContext,
        AgentMemory,
        AgentKnowledge,
    )
    from tangku_agentos.agent_runtime.lifecycle import AgentLifecycleManager
    from tangku_agentos.agent_runtime.manager import AgentManager
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

logger = logging.getLogger(__name__)


# =============================================================================
# AGENT STATE
# =============================================================================

@dataclass
class AgentState:
    """
    Runtime state of an agent.
    
    This class tracks the current state of an agent, including its:
    - Current task
    - Task queue
    - Memory state
    - Knowledge state
    - Planning state
    - Reasoning state
    - Communication state
    - Resource usage
    - Metrics
    
    Attributes:
        agent_id: ID of the agent.
        current_task: ID of the current task being executed.
        task_queue: List of queued task IDs.
        memory_state: State of the agent's memory.
        knowledge_state: State of the agent's knowledge.
        planning_state: State of the agent's planner.
        reasoning_state: State of the agent's reasoner.
        communication_state: State of the agent's communication.
        resources: Current resource usage.
        metrics: Agent metrics.
        last_updated: When the state was last updated.
    """

    agent_id: "AgentID"
    current_task: Optional["TaskID"] = None
    task_queue: List["TaskID"] = field(default_factory=list)
    memory_state: Dict[str, Any] = field(default_factory=dict)
    knowledge_state: Dict[str, Any] = field(default_factory=dict)
    planning_state: Dict[str, Any] = field(default_factory=dict)
    reasoning_state: Dict[str, Any] = field(default_factory=dict)
    communication_state: Dict[str, Any] = field(default_factory=dict)
    resources: Dict[str, Any] = field(default_factory=dict)
    metrics: Dict[str, Any] = field(default_factory=dict)
    last_updated: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "agent_id": self.agent_id,
            "current_task": self.current_task,
            "task_queue": self.task_queue,
            "memory_state": self.memory_state,
            "knowledge_state": self.knowledge_state,
            "planning_state": self.planning_state,
            "reasoning_state": self.reasoning_state,
            "communication_state": self.communication_state,
            "resources": self.resources,
            "metrics": self.metrics,
            "last_updated": self.last_updated.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AgentState":
        """Create from dictionary."""
        return cls(
            agent_id=data["agent_id"],
            current_task=data.get("current_task"),
            task_queue=data.get("task_queue", []),
            memory_state=data.get("memory_state", {}),
            knowledge_state=data.get("knowledge_state", {}),
            planning_state=data.get("planning_state", {}),
            reasoning_state=data.get("reasoning_state", {}),
            communication_state=data.get("communication_state", {}),
            resources=data.get("resources", {}),
            metrics=data.get("metrics", {}),
            last_updated=datetime.fromisoformat(data["last_updated"]),
        )

    def __repr__(self) -> str:
        """Return string representation."""
        return (
            f"AgentState(agent={self.agent_id}, "
            f"current_task={self.current_task}, "
            f"queue_size={len(self.task_queue)})"
        )


# =============================================================================
# AGENT METRICS
# =============================================================================

@dataclass
class AgentMetrics:
    """
    Metrics for an agent.
    
    This class tracks various metrics for monitoring agent performance.
    
    Attributes:
        agent_id: ID of the agent.
        tasks_started: Number of tasks started.
        tasks_completed: Number of tasks completed.
        tasks_failed: Number of tasks failed.
        tasks_cancelled: Number of tasks cancelled.
        tasks_timed_out: Number of tasks timed out.
        messages_sent: Number of messages sent.
        messages_received: Number of messages received.
        memory_operations: Number of memory operations.
        knowledge_operations: Number of knowledge operations.
        planning_operations: Number of planning operations.
        reasoning_operations: Number of reasoning operations.
        tool_operations: Number of tool operations.
        execution_time: Total execution time in seconds.
        idle_time: Total idle time in seconds.
        last_activity: When the agent was last active.
    """

    agent_id: "AgentID"
    tasks_started: int = 0
    tasks_completed: int = 0
    tasks_failed: int = 0
    tasks_cancelled: int = 0
    tasks_timed_out: int = 0
    messages_sent: int = 0
    messages_received: int = 0
    memory_operations: int = 0
    knowledge_operations: int = 0
    planning_operations: int = 0
    reasoning_operations: int = 0
    tool_operations: int = 0
    execution_time: float = 0.0
    idle_time: float = 0.0
    last_activity: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "agent_id": self.agent_id,
            "tasks_started": self.tasks_started,
            "tasks_completed": self.tasks_completed,
            "tasks_failed": self.tasks_failed,
            "tasks_cancelled": self.tasks_cancelled,
            "tasks_timed_out": self.tasks_timed_out,
            "messages_sent": self.messages_sent,
            "messages_received": self.messages_received,
            "memory_operations": self.memory_operations,
            "knowledge_operations": self.knowledge_operations,
            "planning_operations": self.planning_operations,
            "reasoning_operations": self.reasoning_operations,
            "tool_operations": self.tool_operations,
            "execution_time": self.execution_time,
            "idle_time": self.idle_time,
            "last_activity": self.last_activity.isoformat() if self.last_activity else None,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AgentMetrics":
        """Create from dictionary."""
        return cls(
            agent_id=data["agent_id"],
            tasks_started=data.get("tasks_started", 0),
            tasks_completed=data.get("tasks_completed", 0),
            tasks_failed=data.get("tasks_failed", 0),
            tasks_cancelled=data.get("tasks_cancelled", 0),
            tasks_timed_out=data.get("tasks_timed_out", 0),
            messages_sent=data.get("messages_sent", 0),
            messages_received=data.get("messages_received", 0),
            memory_operations=data.get("memory_operations", 0),
            knowledge_operations=data.get("knowledge_operations", 0),
            planning_operations=data.get("planning_operations", 0),
            reasoning_operations=data.get("reasoning_operations", 0),
            tool_operations=data.get("tool_operations", 0),
            execution_time=data.get("execution_time", 0.0),
            idle_time=data.get("idle_time", 0.0),
            last_activity=datetime.fromisoformat(data["last_activity"])
            if data.get("last_activity")
            else None,
        )

    def update_last_activity(self) -> None:
        """Update the last activity timestamp."""
        self.last_activity = datetime.utcnow()

    def __repr__(self) -> str:
        """Return string representation."""
        return (
            f"AgentMetrics(agent={self.agent_id}, "
            f"tasks={self.tasks_completed}/{self.tasks_started}, "
            f"messages={self.messages_sent}/{self.messages_received})"
        )


# =============================================================================
# AGENT HEALTH
# =============================================================================

@dataclass
class AgentHealth:
    """
    Health status of an agent.
    
    This class tracks the health of an agent, including:
    - Overall health status
    - Component health
    - Resource usage
    - Error tracking
    
    Attributes:
        agent_id: ID of the agent.
        status: Overall health status.
        components: Health of individual components.
        resources: Resource usage.
        errors: Recent errors.
        last_checked: When the health was last checked.
        last_error: When the last error occurred.
        error_count: Number of errors.
    """

    agent_id: "AgentID"
    status: str = "HEALTHY"
    components: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    resources: Dict[str, Any] = field(default_factory=dict)
    errors: List[Dict[str, Any]] = field(default_factory=list)
    last_checked: Optional[datetime] = None
    last_error: Optional[datetime] = None
    error_count: int = 0

    def is_healthy(self) -> bool:
        """Check if the agent is healthy."""
        return self.status == "HEALTHY"

    def add_error(self, error: str, details: Optional[Dict[str, Any]] = None) -> None:
        """
        Add an error to the error list.
        
        Args:
            error: Error message.
            details: Additional error details.
        """
        self.errors.append({
            "error": error,
            "details": details or {},
            "timestamp": datetime.utcnow().isoformat(),
        })
        self.last_error = datetime.utcnow()
        self.error_count += 1
        # Keep only the last 100 errors
        if len(self.errors) > 100:
            self.errors = self.errors[-100:]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "agent_id": self.agent_id,
            "status": self.status,
            "components": self.components,
            "resources": self.resources,
            "errors": self.errors,
            "last_checked": self.last_checked.isoformat() if self.last_checked else None,
            "last_error": self.last_error.isoformat() if self.last_error else None,
            "error_count": self.error_count,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AgentHealth":
        """Create from dictionary."""
        return cls(
            agent_id=data["agent_id"],
            status=data.get("status", "HEALTHY"),
            components=data.get("components", {}),
            resources=data.get("resources", {}),
            errors=data.get("errors", []),
            last_checked=datetime.fromisoformat(data["last_checked"])
            if data.get("last_checked")
            else None,
            last_error=datetime.fromisoformat(data["last_error"])
            if data.get("last_error")
            else None,
            error_count=data.get("error_count", 0),
        )

    def __repr__(self) -> str:
        """Return string representation."""
        return f"AgentHealth(agent={self.agent_id}, status={self.status})"


# =============================================================================
# AGENT EVENT STREAM
# =============================================================================

@dataclass
class AgentEvent:
    """
    Event generated by an agent.
    
    Attributes:
        agent_id: ID of the agent that generated the event.
        event_type: Type of the event.
        data: Event data.
        timestamp: When the event occurred.
        metadata: Additional metadata.
    """

    agent_id: "AgentID"
    event_type: str
    data: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "agent_id": self.agent_id,
            "event_type": self.event_type,
            "data": self.data,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AgentEvent":
        """Create from dictionary."""
        return cls(
            agent_id=data["agent_id"],
            event_type=data["event_type"],
            data=data.get("data", {}),
            timestamp=datetime.fromisoformat(data["timestamp"]),
            metadata=data.get("metadata", {}),
        )


class AgentEventStream:
    """
    Event stream for an agent.
    
    This class provides a buffer for agent events, allowing consumers
    to subscribe to and retrieve events.
    
    Example:
        >>> from tangku_agentos.agent_runtime.agent import AgentEventStream
        >>> 
        >>> stream = AgentEventStream(max_events=1000)
        >>> 
        >>> # Subscribe to events
        >>> def handle_event(event):
        ...     print(f"Event: {event.event_type}")
        >>> stream.subscribe(handle_event)
        >>> 
        >>> # Publish an event
        >>> stream.publish("agent_1", "task.completed", {"task_id": "task_1"})
    """

    def __init__(self, max_events: int = 1000):
        """
        Initialize the event stream.
        
        Args:
            max_events: Maximum number of events to buffer.
        """
        self._max_events = max_events
        self._events: List[AgentEvent] = []
        self._subscribers: List[Callable[[AgentEvent], None]] = []
        self._lock = asyncio.Lock()

    async def publish(
        self,
        agent_id: "AgentID",
        event_type: str,
        data: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Publish an event to the stream.
        
        Args:
            agent_id: ID of the agent.
            event_type: Type of the event.
            data: Event data.
            metadata: Additional metadata.
        """
        event = AgentEvent(
            agent_id=agent_id,
            event_type=event_type,
            data=data or {},
            metadata=metadata or {},
        )

        async with self._lock:
            # Add to buffer
            self._events.append(event)
            if len(self._events) > self._max_events:
                self._events = self._events[-self._max_events:]

            # Notify subscribers
            for subscriber in self._subscribers:
                try:
                    subscriber(event)
                except Exception as e:
                    logger.error(f"Error in event subscriber: {e}")

    async def get_events(
        self,
        agent_id: Optional["AgentID"] = None,
        event_type: Optional[str] = None,
        limit: Optional[int] = None,
        since: Optional[datetime] = None,
    ) -> List[AgentEvent]:
        """
        Get events from the stream.
        
        Args:
            agent_id: Filter by agent ID.
            event_type: Filter by event type.
            limit: Maximum number of events to return.
            since: Only return events after this timestamp.
            
        Returns:
            List of matching events.
        """
        async with self._lock:
            events = self._events.copy()

        results = []
        for event in events:
            if agent_id and event.agent_id != agent_id:
                continue
            if event_type and event.event_type != event_type:
                continue
            if since and event.timestamp < since:
                continue
            results.append(event)
            if limit and len(results) >= limit:
                break

        return results

    def subscribe(self, callback: Callable[[AgentEvent], None]) -> None:
        """
        Subscribe to events.
        
        Args:
            callback: Callback function to call for each event.
        """
        self._subscribers.append(callback)

    def unsubscribe(self, callback: Callable[[AgentEvent], None]) -> bool:
        """
        Unsubscribe from events.
        
        Args:
            callback: Callback function to remove.
            
        Returns:
            True if the callback was removed, False if not found.
        """
        try:
            self._subscribers.remove(callback)
            return True
        except ValueError:
            return False

    async def clear(self) -> int:
        """
        Clear all events from the stream.
        
        Returns:
            Number of events cleared.
        """
        async with self._lock:
            count = len(self._events)
            self._events.clear()
            return count

    def __len__(self) -> int:
        """Get the number of events in the stream."""
        return len(self._events)

    def __repr__(self) -> str:
        """Return string representation."""
        return f"AgentEventStream(events={len(self._events)}, subscribers={len(self._subscribers)})"


# =============================================================================
# AGENT CLASS
# =============================================================================

class Agent:
    """
    Autonomous AI agent.
    
    This is the main agent class, representing an autonomous AI agent
    that can perform tasks, communicate with other agents, and manage
    its own state.
    
    The agent consists of:
    - Identity: Unique identifier, name, type, version
    - Configuration: Settings and capabilities
    - Profile: Personality and behavior
    - State: Current runtime state
    - Memory: Short-term and long-term memory
    - Knowledge: Access to knowledge sources
    - Planner: Task planning and execution
    - Reasoner: Reasoning and decision making
    - Tools: Available tools and their usage
    - Skills: Reusable capabilities
    - Communication: Message sending and receiving
    - Metrics: Performance tracking
    - Health: Health monitoring
    - Events: Event stream
    
    Thread Safety:
        This class is thread-safe for concurrent access.
    
    Example:
        >>> from tangku_agentos.agent_runtime.agent import Agent
        >>> from tangku_agentos.agent_runtime.core import AgentConfig, AgentIdentity
        >>> 
        >>> # Create agent identity
        >>> identity = AgentIdentity(id="agent_1", name="Research Agent")
        >>> 
        >>> # Create agent config
        >>> config = AgentConfig(identity=identity)
        >>> 
        >>> # Create agent
        >>> agent = Agent(config=config)
        >>> 
        >>> # Initialize agent
        >>> await agent.initialize()
        >>> 
        >>> # Start agent
        >>> await agent.start()
        >>> 
        >>> # Execute a task
        >>> result = await agent.execute_task("analyze_data", {"data": "..."})
    """

    def __init__(
        self,
        config: "AgentConfig",
        profile: Optional["AgentProfile"] = None,
        manager: Optional["AgentManager"] = None,
        lifecycle_manager: Optional["AgentLifecycleManager"] = None,
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
    ):
        """
        Initialize the agent.
        
        Args:
            config: Agent configuration.
            profile: Agent profile.
            manager: Agent manager for agent operations.
            lifecycle_manager: Lifecycle manager for state tracking.
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
        """
        # Identity and configuration
        self._config = config
        self._profile = profile or AgentProfile()
        self._identity = config.identity

        # Manager references
        self._manager = manager
        self._lifecycle_manager = lifecycle_manager

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

        # State
        self._state = AgentState(agent_id=self._identity.id)
        self._metrics = AgentMetrics(agent_id=self._identity.id)
        self._health = AgentHealth(agent_id=self._identity.id)

        # Event stream
        self._event_stream = AgentEventStream()

        # Lock for thread safety
        self._lock = asyncio.Lock()

        # Running state
        self._running = False
        self._initialized = False

        # Callbacks
        self._on_task_start: List[Callable[[str, Dict[str, Any]], None]] = []
        self._on_task_complete: List[Callable[[str, Any], None]] = []
        self._on_task_fail: List[Callable[[str, str], None]] = []
        self._on_message_received: List[Callable[[Dict[str, Any]], None]] = []
        self._on_event: List[Callable[[AgentEvent], None]] = []

        logger.info(f"Agent created: {self._identity.id} ({self._identity.name})")

    @property
    def id(self) -> "AgentID":
        """Get the agent ID."""
        return self._identity.id

    @property
    def name(self) -> "AgentName":
        """Get the agent name."""
        return self._identity.name

    @property
    def type(self) -> "AgentType":
        """Get the agent type."""
        return self._identity.type

    @property
    def version(self) -> "AgentVersion":
        """Get the agent version."""
        return self._identity.version

    @property
    def config(self) -> "AgentConfig":
        """Get the agent configuration."""
        return self._config

    @property
    def profile(self) -> "AgentProfile":
        """Get the agent profile."""
        return self._profile

    @property
    def identity(self) -> "AgentIdentity":
        """Get the agent identity."""
        return self._identity

    @property
    def capabilities(self) -> "AgentCapabilities":
        """Get the agent capabilities."""
        return self._config.capabilities

    @property
    def state(self) -> AgentState:
        """Get the agent state."""
        return self._state

    @property
    def metrics(self) -> AgentMetrics:
        """Get the agent metrics."""
        return self._metrics

    @property
    def health(self) -> AgentHealth:
        """Get the agent health."""
        return self._health

    @property
    def event_stream(self) -> AgentEventStream:
        """Get the agent event stream."""
        return self._event_stream

    @property
    def is_running(self) -> bool:
        """Check if the agent is running."""
        return self._running

    @property
    def is_initialized(self) -> bool:
        """Check if the agent is initialized."""
        return self._initialized

    # =========================================================================
    # LIFECYCLE METHODS
    # =========================================================================

    async def initialize(self) -> None:
        """
        Initialize the agent.
        
        This method initializes the agent's components and prepares it for execution.
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
                await self._publish_event("agent.initialized", {})

                # Update lifecycle
                if self._lifecycle_manager:
                    from tangku_agentos.agent_runtime.types import AgentLifecycleState
                    await self._lifecycle_manager.transition(
                        self._identity.id,
                        AgentLifecycleState.IDLE,
                        reason="initialization_complete",
                    )

                logger.info(f"Agent initialized: {self._identity.id}")

            except Exception as e:
                logger.error(f"Agent initialization failed: {self._identity.id}: {e}")
                self._health.add_error(f"Initialization failed: {e}")
                raise

    async def _initialize_components(self) -> None:
        """
        Initialize agent components.
        
        This method can be overridden by subclasses to initialize custom components.
        """
        # Initialize health checks
        self._initialize_health_checks()

        # Initialize metrics
        self._metrics.last_activity = datetime.utcnow()

    def _initialize_health_checks(self) -> None:
        """
        Initialize health checks for the agent.
        
        This method sets up the default health checks for the agent.
        """
        # Add a basic liveness check
        async def liveness_check(agent_id: "AgentID") -> bool:
            return self._running and self._initialized

        self._health.components["liveness"] = {
            "status": "HEALTHY",
            "check_func": liveness_check,
            "interval": 30.0,
        }

    async def start(self) -> None:
        """
        Start the agent.
        
        This method starts the agent and makes it ready to execute tasks.
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

                # Publish started event
                await self._publish_event("agent.started", {})

                # Update lifecycle
                if self._lifecycle_manager:
                    from tangku_agentos.agent_runtime.types import AgentLifecycleState
                    await self._lifecycle_manager.transition(
                        self._identity.id,
                        AgentLifecycleState.IDLE,
                        reason="started",
                    )

                logger.info(f"Agent started: {self._identity.id}")

            except Exception as e:
                logger.error(f"Agent startup failed: {self._identity.id}: {e}")
                self._health.add_error(f"Startup failed: {e}")
                raise

    async def _start_components(self) -> None:
        """
        Start agent components.
        
        This method can be overridden by subclasses to start custom components.
        """
        pass

    async def stop(self, force: bool = False) -> None:
        """
        Stop the agent.
        
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
                await self._publish_event("agent.stopped", {"force": force})

                # Update lifecycle
                if self._lifecycle_manager:
                    from tangku_agentos.agent_runtime.types import AgentLifecycleState
                    await self._lifecycle_manager.transition(
                        self._identity.id,
                        AgentLifecycleState.STOPPED,
                        reason="stopped",
                    )

                logger.info(f"Agent stopped: {self._identity.id}")

            except Exception as e:
                logger.error(f"Agent shutdown failed: {self._identity.id}: {e}")
                self._health.add_error(f"Shutdown failed: {e}")
                raise

    async def _stop_components(self) -> None:
        """
        Stop agent components.
        
        This method can be overridden by subclasses to stop custom components.
        """
        pass

    async def pause(self) -> None:
        """Pause the agent."""
        if not self._running:
            return

        async with self._lock:
            if not self._running:
                return

            try:
                # Pause components
                await self._pause_components()

                # Update state
                self._running = False

                # Publish paused event
                await self._publish_event("agent.paused", {})

                # Update lifecycle
                if self._lifecycle_manager:
                    from tangku_agentos.agent_runtime.types import AgentLifecycleState
                    await self._lifecycle_manager.transition(
                        self._identity.id,
                        AgentLifecycleState.PAUSED,
                        reason="paused",
                    )

                logger.info(f"Agent paused: {self._identity.id}")

            except Exception as e:
                logger.error(f"Agent pause failed: {self._identity.id}: {e}")
                self._health.add_error(f"Pause failed: {e}")
                raise

    async def _pause_components(self) -> None:
        """
        Pause agent components.
        
        This method can be overridden by subclasses to pause custom components.
        """
        pass

    async def resume(self) -> None:
        """Resume the agent."""
        if self._running:
            return

        async with self._lock:
            if self._running:
                return

            try:
                # Resume components
                await self._resume_components()

                # Update state
                self._running = True

                # Publish resumed event
                await self._publish_event("agent.resumed", {})

                # Update lifecycle
                if self._lifecycle_manager:
                    from tangku_agentos.agent_runtime.types import AgentLifecycleState
                    await self._lifecycle_manager.transition(
                        self._identity.id,
                        AgentLifecycleState.IDLE,
                        reason="resumed",
                    )

                logger.info(f"Agent resumed: {self._identity.id}")

            except Exception as e:
                logger.error(f"Agent resume failed: {self._identity.id}: {e}")
                self._health.add_error(f"Resume failed: {e}")
                raise

    async def _resume_components(self) -> None:
        """
        Resume agent components.
        
        This method can be overridden by subclasses to resume custom components.
        """
        pass

    async def restart(self) -> None:
        """Restart the agent."""
        await self.stop()
        await self.start()
        logger.info(f"Agent restarted: {self._identity.id}")

    # =========================================================================
    # TASK EXECUTION METHODS
    # =========================================================================

    async def execute_task(
        self,
        task_name: str,
        payload: Optional[Dict[str, Any]] = None,
        timeout: Optional[float] = None,
        priority: int = 0,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Any:
        """
        Execute a task.
        
        Args:
            task_name: Name of the task to execute.
            payload: Task payload/data.
            timeout: Timeout in seconds.
            priority: Task priority.
            metadata: Additional task metadata.
            
        Returns:
            Result of the task execution.
        """
        task_id = f"task_{self._identity.id}_{uuid.uuid4().hex[:8]}"

        # Update state
        self._state.current_task = task_id
        self._state.last_updated = datetime.utcnow()

        # Update metrics
        self._metrics.tasks_started += 1
        self._metrics.update_last_activity()

        # Publish task started event
        await self._publish_event(
            "agent.task_started",
            {"task_id": task_id, "task_name": task_name, "payload": payload},
        )

        # Call task start callbacks
        for callback in self._on_task_start:
            try:
                callback(task_name, payload or {})
            except Exception as e:
                logger.error(f"Error in task start callback: {e}")

        try:
            # Execute the task
            result = await self._execute_task_internal(
                task_id=task_id,
                task_name=task_name,
                payload=payload or {},
                timeout=timeout or self._config.timeout,
                metadata=metadata or {},
            )

            # Update state
            self._state.current_task = None
            self._state.last_updated = datetime.utcnow()

            # Update metrics
            self._metrics.tasks_completed += 1
            self._metrics.update_last_activity()

            # Publish task completed event
            await self._publish_event(
                "agent.task_completed",
                {"task_id": task_id, "task_name": task_name, "result": result},
            )

            # Call task complete callbacks
            for callback in self._on_task_complete:
                try:
                    callback(task_name, result)
                except Exception as e:
                    logger.error(f"Error in task complete callback: {e}")

            return result

        except asyncio.TimeoutError:
            # Update state
            self._state.current_task = None
            self._state.last_updated = datetime.utcnow()

            # Update metrics
            self._metrics.tasks_timed_out += 1

            # Publish task timed out event
            await self._publish_event(
                "agent.task_timed_out",
                {"task_id": task_id, "task_name": task_name},
            )

            # Call task fail callbacks
            for callback in self._on_task_fail:
                try:
                    callback(task_name, "Task timed out")
                except Exception as e:
                    logger.error(f"Error in task fail callback: {e}")

            raise

        except Exception as e:
            # Update state
            self._state.current_task = None
            self._state.last_updated = datetime.utcnow()

            # Update metrics
            self._metrics.tasks_failed += 1

            # Update health
            self._health.add_error(f"Task failed: {task_name}: {e}")

            # Publish task failed event
            await self._publish_event(
                "agent.task_failed",
                {"task_id": task_id, "task_name": task_name, "error": str(e)},
            )

            # Call task fail callbacks
            for callback in self._on_task_fail:
                try:
                    callback(task_name, str(e))
                except Exception as e:
                    logger.error(f"Error in task fail callback: {e}")

            raise

    async def _execute_task_internal(
        self,
        task_id: "TaskID",
        task_name: str,
        payload: Dict[str, Any],
        timeout: float,
        metadata: Dict[str, Any],
    ) -> Any:
        """
        Internal task execution.
        
        This method can be overridden by subclasses to provide custom
        task execution logic.
        
        Args:
            task_id: ID of the task.
            task_name: Name of the task.
            payload: Task payload.
            timeout: Timeout in seconds.
            metadata: Task metadata.
            
        Returns:
            Result of the task execution.
        """
        # Default implementation: use planning and reasoning
        if self._planning_runtime:
            # Create a plan for the task
            plan = await self._planning_runtime.create_plan(
                task=task_name,
                context=payload,
            )
            self._state.planning_state["current_plan"] = plan

            # Execute the plan
            result = await self._planning_runtime.execute_plan(plan["plan_id"])
            return result

        # Fallback: just return the payload
        return payload

    async def cancel_task(self, task_id: "TaskID") -> bool:
        """
        Cancel a task.
        
        Args:
            task_id: ID of the task to cancel.
            
        Returns:
            True if the task was cancelled, False if not found.
        """
        if self._state.current_task == task_id:
            # Cancel the current task
            self._state.current_task = None
            self._state.last_updated = datetime.utcnow()

            # Update metrics
            self._metrics.tasks_cancelled += 1

            # Publish task cancelled event
            await self._publish_event(
                "agent.task_cancelled",
                {"task_id": task_id},
            )

            return True
        return False

    # =========================================================================
    # COMMUNICATION METHODS
    # =========================================================================

    async def send_message(
        self,
        recipient_id: str,
        message_type: str,
        payload: Optional[Dict[str, Any]] = None,
        priority: str = "normal",
        timeout: Optional[float] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Any:
        """
        Send a message to another agent or runtime.
        
        Args:
            recipient_id: ID of the recipient.
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
            sender_id=self._identity.id,
            recipient_id=recipient_id,
            payload=payload or {},
            priority=priority,
            timeout=timeout or self._config.timeout,
            metadata=metadata or {},
        )

        # Update metrics
        self._metrics.messages_sent += 1
        self._metrics.update_last_activity()

        # Publish message sent event
        await self._publish_event(
            "agent.message_sent",
            {
                "recipient_id": recipient_id,
                "message_type": message_type,
                "payload": payload,
            },
        )

        # Send the message
        return await self._message_bus.send(message)

    async def send_command(
        self,
        recipient_id: str,
        command_type: str,
        payload: Optional[Dict[str, Any]] = None,
        priority: str = "normal",
        timeout: Optional[float] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Any:
        """
        Send a command to another agent or runtime.
        
        Args:
            recipient_id: ID of the recipient.
            command_type: Type of the command.
            payload: Command payload.
            priority: Command priority.
            timeout: Timeout in seconds.
            metadata: Additional metadata.
            
        Returns:
            Result of the command execution.
        """
        if not self._command_bus:
            raise RuntimeError("Command bus not configured")

        from tangku_agentos.runtime_communication import Command, MessageType

        command = Command(
            message_type=MessageType.COMMAND,
            sender_id=self._identity.id,
            recipient_id=recipient_id,
            command_type=command_type,
            payload=payload or {},
            priority=priority,
            timeout=timeout or self._config.timeout,
            metadata=metadata or {},
        )

        # Update metrics
        self._metrics.messages_sent += 1
        self._metrics.update_last_activity()

        # Publish command sent event
        await self._publish_event(
            "agent.command_sent",
            {
                "recipient_id": recipient_id,
                "command_type": command_type,
                "payload": payload,
            },
        )

        # Send the command
        return await self._command_bus.send(command)

    async def send_query(
        self,
        recipient_id: str,
        query_type: str,
        payload: Optional[Dict[str, Any]] = None,
        priority: str = "normal",
        timeout: Optional[float] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Any:
        """
        Send a query to another agent or runtime.
        
        Args:
            recipient_id: ID of the recipient.
            query_type: Type of the query.
            payload: Query payload.
            priority: Query priority.
            timeout: Timeout in seconds.
            metadata: Additional metadata.
            
        Returns:
            Result of the query.
        """
        if not self._query_bus:
            raise RuntimeError("Query bus not configured")

        from tangku_agentos.runtime_communication import Query, MessageType

        query = Query(
            message_type=MessageType.QUERY,
            sender_id=self._identity.id,
            recipient_id=recipient_id,
            query_type=query_type,
            payload=payload or {},
            priority=priority,
            timeout=timeout or self._config.timeout,
            metadata=metadata or {},
        )

        # Update metrics
        self._metrics.messages_sent += 1
        self._metrics.update_last_activity()

        # Publish query sent event
        await self._publish_event(
            "agent.query_sent",
            {
                "recipient_id": recipient_id,
                "query_type": query_type,
                "payload": payload,
            },
        )

        # Send the query
        return await self._query_bus.ask(query)

    async def publish_event(
        self,
        event_type: str,
        payload: Optional[Dict[str, Any]] = None,
        priority: str = "normal",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Publish an event.
        
        Args:
            event_type: Type of the event.
            payload: Event payload.
            priority: Event priority.
            metadata: Additional metadata.
        """
        if not self._event_bus:
            raise RuntimeError("Event bus not configured")

        from tangku_agentos.runtime_communication import Event, MessageType

        event = Event(
            message_type=MessageType.EVENT,
            sender_id=self._identity.id,
            event_type=event_type,
            payload=payload or {},
            priority=priority,
            metadata=metadata or {},
        )

        # Update metrics
        self._metrics.messages_sent += 1
        self._metrics.update_last_activity()

        # Publish the event
        await self._event_bus.publish(event)

        # Also publish to agent event stream
        await self._event_stream.publish(
            self._identity.id,
            event_type,
            payload or {},
            metadata or {},
        )

    async def broadcast(
        self,
        message_type: str,
        payload: Optional[Dict[str, Any]] = None,
        channels: Optional[List[str]] = None,
        priority: str = "normal",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> int:
        """
        Broadcast a message to multiple recipients.
        
        Args:
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
            sender_id=self._identity.id,
            broadcast_type=message_type,
            payload=payload or {},
            channels=channels,
            priority=priority,
            metadata=metadata or {},
        )

        # Update metrics
        self._metrics.messages_sent += 1
        self._metrics.update_last_activity()

        # Publish broadcast event
        await self._publish_event(
            "agent.broadcast_sent",
            {
                "message_type": message_type,
                "payload": payload,
                "channels": channels,
            },
        )

        # Broadcast the message
        return await self._broadcast_bus.broadcast(broadcast)

    async def request_response(
        self,
        recipient_id: str,
        request_type: str,
        payload: Optional[Dict[str, Any]] = None,
        timeout: Optional[float] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Any:
        """
        Send a request and wait for a response.
        
        Args:
            recipient_id: ID of the recipient.
            request_type: Type of the request.
            payload: Request payload.
            timeout: Timeout in seconds.
            metadata: Additional metadata.
            
        Returns:
            Response from the recipient.
        """
        if not self._request_response_bus:
            raise RuntimeError("Request/response bus not configured")

        from tangku_agentos.runtime_communication import Message, MessageType

        request = Message(
            message_type=MessageType.QUERY,
            sender_id=self._identity.id,
            recipient_id=recipient_id,
            payload={"type": request_type, **(payload or {})},
            timeout=timeout or self._config.timeout,
            metadata=metadata or {},
        )

        # Update metrics
        self._metrics.messages_sent += 1
        self._metrics.update_last_activity()

        # Publish request sent event
        await self._publish_event(
            "agent.request_sent",
            {
                "recipient_id": recipient_id,
                "request_type": request_type,
                "payload": payload,
            },
        )

        # Send the request
        return await self._request_response_bus.request(request, timeout=timeout)

    async def receive_message(self, message: Dict[str, Any]) -> None:
        """
        Receive a message.
        
        This method is called when the agent receives a message.
        Subclasses can override this to handle specific message types.
        
        Args:
            message: Received message.
        """
        # Update metrics
        self._metrics.messages_received += 1
        self._metrics.update_last_activity()

        # Publish message received event
        await self._publish_event(
            "agent.message_received",
            {"message": message},
        )

        # Call message received callbacks
        for callback in self._on_message_received:
            try:
                callback(message)
            except Exception as e:
                logger.error(f"Error in message received callback: {e}")

    # =========================================================================
    # MEMORY METHODS
    # =========================================================================

    async def save_memory(
        self,
        memory_id: Optional["MemoryID"] = None,
        data: Optional[Dict[str, Any]] = None,
        memory_type: "MemoryType" = MemoryType.WORKING,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> "MemoryID":
        """
        Save data to memory.
        
        Args:
            memory_id: ID of the memory entry (generated if not provided).
            data: Data to save.
            memory_type: Type of memory.
            metadata: Additional metadata.
            
        Returns:
            ID of the saved memory entry.
        """
        if not self._memory_engine:
            raise RuntimeError("Memory engine not configured")

        # Generate memory ID if not provided
        if not memory_id:
            memory_id = f"memory_{self._identity.id}_{uuid.uuid4().hex[:8]}"

        # Save to memory engine
        await self._memory_engine.save(
            memory_id=memory_id,
            data=data or {},
            metadata={
                "agent_id": self._identity.id,
                "memory_type": memory_type.value if hasattr(memory_type, 'value') else str(memory_type),
                **(metadata or {}),
            },
        )

        # Update metrics
        self._metrics.memory_operations += 1
        self._metrics.update_last_activity()

        # Update state
        self._state.memory_state["last_saved"] = memory_id
        self._state.last_updated = datetime.utcnow()

        # Publish memory saved event
        await self._publish_event(
            "agent.memory_saved",
            {"memory_id": memory_id, "memory_type": memory_type.value},
        )

        return memory_id

    async def load_memory(
        self,
        memory_id: "MemoryID",
    ) -> Optional[Dict[str, Any]]:
        """
        Load data from memory.
        
        Args:
            memory_id: ID of the memory entry to load.
            
        Returns:
            Data from the memory entry, or None if not found.
        """
        if not self._memory_engine:
            raise RuntimeError("Memory engine not configured")

        # Load from memory engine
        data = await self._memory_engine.load(memory_id)

        # Update metrics
        self._metrics.memory_operations += 1
        self._metrics.update_last_activity()

        # Update state
        self._state.memory_state["last_loaded"] = memory_id
        self._state.last_updated = datetime.utcnow()

        # Publish memory loaded event
        await self._publish_event(
            "agent.memory_loaded",
            {"memory_id": memory_id},
        )

        return data

    async def delete_memory(
        self,
        memory_id: "MemoryID",
    ) -> bool:
        """
        Delete a memory entry.
        
        Args:
            memory_id: ID of the memory entry to delete.
            
        Returns:
            True if the memory was deleted, False if not found.
        """
        if not self._memory_engine:
            raise RuntimeError("Memory engine not configured")

        # Delete from memory engine
        result = await self._memory_engine.delete(memory_id)

        # Update metrics
        self._metrics.memory_operations += 1
        self._metrics.update_last_activity()

        # Update state
        self._state.memory_state["last_deleted"] = memory_id
        self._state.last_updated = datetime.utcnow()

        # Publish memory deleted event
        await self._publish_event(
            "agent.memory_deleted",
            {"memory_id": memory_id},
        )

        return result

    async def search_memory(
        self,
        query: str,
        memory_type: Optional["MemoryType"] = None,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        """
        Search memory entries.
        
        Args:
            query: Search query.
            memory_type: Type of memory to search.
            limit: Maximum number of results to return.
            
        Returns:
            List of matching memory entries.
        """
        if not self._memory_engine:
            raise RuntimeError("Memory engine not configured")

        # Search memory engine
        results = await self._memory_engine.search(
            query=query,
            filter={"agent_id": self._identity.id},
            limit=limit,
        )

        # Update metrics
        self._metrics.memory_operations += 1
        self._metrics.update_last_activity()

        # Publish memory searched event
        await self._publish_event(
            "agent.memory_searched",
            {"query": query, "results_count": len(results)},
        )

        return results

    # =========================================================================
    # KNOWLEDGE METHODS
    # =========================================================================

    async def search_knowledge(
        self,
        query: str,
        knowledge_type: Optional["KnowledgeType"] = None,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        """
        Search knowledge.
        
        Args:
            query: Search query.
            knowledge_type: Type of knowledge to search.
            limit: Maximum number of results to return.
            
        Returns:
            List of matching knowledge entries.
        """
        if not self._knowledge_engine:
            raise RuntimeError("Knowledge engine not configured")

        # Search knowledge engine
        results = await self._knowledge_engine.search(
            query=query,
            limit=limit,
        )

        # Update metrics
        self._metrics.knowledge_operations += 1
        self._metrics.update_last_activity()

        # Update state
        self._state.knowledge_state["last_searched"] = query
        self._state.last_updated = datetime.utcnow()

        # Publish knowledge searched event
        await self._publish_event(
            "agent.knowledge_searched",
            {"query": query, "results_count": len(results)},
        )

        return results

    async def index_knowledge(
        self,
        document_id: str,
        content: str,
        source: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> "KnowledgeID":
        """
        Index a knowledge document.
        
        Args:
            document_id: ID of the document.
            content: Content to index.
            source: Source of the document.
            metadata: Additional metadata.
            
        Returns:
            ID of the indexed knowledge entry.
        """
        if not self._knowledge_engine:
            raise RuntimeError("Knowledge engine not configured")

        # Index in knowledge engine
        knowledge_id = await self._knowledge_engine.index(
            document_id=document_id,
            content=content,
            source=source,
            metadata={
                "agent_id": self._identity.id,
                **(metadata or {}),
            },
        )

        # Update metrics
        self._metrics.knowledge_operations += 1
        self._metrics.update_last_activity()

        # Update state
        self._state.knowledge_state["last_indexed"] = knowledge_id
        self._state.last_updated = datetime.utcnow()

        # Publish knowledge indexed event
        await self._publish_event(
            "agent.knowledge_indexed",
            {"knowledge_id": knowledge_id, "document_id": document_id},
        )

        return knowledge_id

    async def get_knowledge(
        self,
        knowledge_id: "KnowledgeID",
    ) -> Optional[Dict[str, Any]]:
        """
        Get a knowledge entry.
        
        Args:
            knowledge_id: ID of the knowledge entry to retrieve.
            
        Returns:
            Knowledge entry if found, None otherwise.
        """
        if not self._knowledge_engine:
            raise RuntimeError("Knowledge engine not configured")

        # Get from knowledge engine
        knowledge = await self._knowledge_engine.get(knowledge_id)

        # Update metrics
        self._metrics.knowledge_operations += 1
        self._metrics.update_last_activity()

        # Update state
        self._state.knowledge_state["last_retrieved"] = knowledge_id
        self._state.last_updated = datetime.utcnow()

        # Publish knowledge retrieved event
        await self._publish_event(
            "agent.knowledge_retrieved",
            {"knowledge_id": knowledge_id},
        )

        return knowledge

    # =========================================================================
    # PLANNING METHODS
    # =========================================================================

    async def create_plan(
        self,
        task: str,
        context: Optional[Dict[str, Any]] = None,
        constraints: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Create a plan for a task.
        
        Args:
            task: Task to plan.
            context: Context for the task.
            constraints: List of constraints.
            
        Returns:
            Plan for the task.
        """
        if not self._planning_runtime:
            raise RuntimeError("Planning runtime not configured")

        # Create plan using planning runtime
        plan = await self._planning_runtime.create_plan(
            task=task,
            context=context or {},
            constraints=constraints or [],
        )

        # Update metrics
        self._metrics.planning_operations += 1
        self._metrics.update_last_activity()

        # Update state
        self._state.planning_state["last_plan"] = plan.get("plan_id")
        self._state.last_updated = datetime.utcnow()

        # Publish plan created event
        await self._publish_event(
            "agent.plan_created",
            {"plan_id": plan.get("plan_id"), "task": task},
        )

        return plan

    async def execute_plan(
        self,
        plan_id: "PlanID",
    ) -> Any:
        """
        Execute a plan.
        
        Args:
            plan_id: ID of the plan to execute.
            
        Returns:
            Result of the plan execution.
        """
        if not self._planning_runtime:
            raise RuntimeError("Planning runtime not configured")

        # Execute plan using planning runtime
        result = await self._planning_runtime.execute_plan(plan_id)

        # Update metrics
        self._metrics.planning_operations += 1
        self._metrics.update_last_activity()

        # Update state
        self._state.planning_state["last_executed"] = plan_id
        self._state.last_updated = datetime.utcnow()

        # Publish plan executed event
        await self._publish_event(
            "agent.plan_executed",
            {"plan_id": plan_id},
        )

        return result

    async def get_plan_status(
        self,
        plan_id: "PlanID",
    ) -> Dict[str, Any]:
        """
        Get the status of a plan.
        
        Args:
            plan_id: ID of the plan.
            
        Returns:
            Status of the plan.
        """
        if not self._planning_runtime:
            raise RuntimeError("Planning runtime not configured")

        # Get plan status from planning runtime
        status = await self._planning_runtime.get_plan_status(plan_id)

        # Update metrics
        self._metrics.planning_operations += 1
        self._metrics.update_last_activity()

        return status

    # =========================================================================
    # REASONING METHODS
    # =========================================================================

    async def start_reasoning(
        self,
        task: str,
        context: Optional[Dict[str, Any]] = None,
        model_id: Optional[str] = None,
    ) -> "ReasoningID":
        """
        Start a reasoning session.
        
        Args:
            task: Task to reason about.
            context: Context for the reasoning.
            model_id: ID of the model to use.
            
        Returns:
            ID of the reasoning session.
        """
        if not self._reasoning_runtime:
            raise RuntimeError("Reasoning runtime not configured")

        # Start reasoning using reasoning runtime
        reasoning_id = await self._reasoning_runtime.start_reasoning(
            task=task,
            context=context or {},
            model_id=model_id,
        )

        # Update metrics
        self._metrics.reasoning_operations += 1
        self._metrics.update_last_activity()

        # Update state
        self._state.reasoning_state["current_reasoning"] = reasoning_id
        self._state.last_updated = datetime.utcnow()

        # Publish reasoning started event
        await self._publish_event(
            "agent.reasoning_started",
            {"reasoning_id": reasoning_id, "task": task},
        )

        return reasoning_id

    async def get_reasoning_state(
        self,
        reasoning_id: "ReasoningID",
    ) -> Dict[str, Any]:
        """
        Get the state of a reasoning session.
        
        Args:
            reasoning_id: ID of the reasoning session.
            
        Returns:
            State of the reasoning session.
        """
        if not self._reasoning_runtime:
            raise RuntimeError("Reasoning runtime not configured")

        # Get reasoning state from reasoning runtime
        state = await self._reasoning_runtime.get_reasoning_state(reasoning_id)

        # Update metrics
        self._metrics.reasoning_operations += 1
        self._metrics.update_last_activity()

        return state

    async def stop_reasoning(
        self,
        reasoning_id: "ReasoningID",
    ) -> bool:
        """
        Stop a reasoning session.
        
        Args:
            reasoning_id: ID of the reasoning session to stop.
            
        Returns:
            True if the reasoning was stopped, False if not found.
        """
        if not self._reasoning_runtime:
            raise RuntimeError("Reasoning runtime not configured")

        # Stop reasoning using reasoning runtime
        result = await self._reasoning_runtime.stop_reasoning(reasoning_id)

        # Update metrics
        self._metrics.reasoning_operations += 1
        self._metrics.update_last_activity()

        # Update state
        if reasoning_id in self._state.reasoning_state.get("current_reasoning", ""):
            del self._state.reasoning_state["current_reasoning"]
        self._state.last_updated = datetime.utcnow()

        # Publish reasoning stopped event
        await self._publish_event(
            "agent.reasoning_stopped",
            {"reasoning_id": reasoning_id},
        )

        return result

    # =========================================================================
    # CALLBACK REGISTRATION
    # =========================================================================

    def on_task_start(self, callback: Callable[[str, Dict[str, Any]], None]) -> None:
        """
        Register a callback for task start.
        
        Args:
            callback: Callback function to call when a task starts.
        """
        self._on_task_start.append(callback)

    def on_task_complete(self, callback: Callable[[str, Any], None]) -> None:
        """
        Register a callback for task completion.
        
        Args:
            callback: Callback function to call when a task completes.
        """
        self._on_task_complete.append(callback)

    def on_task_fail(self, callback: Callable[[str, str], None]) -> None:
        """
        Register a callback for task failure.
        
        Args:
            callback: Callback function to call when a task fails.
        """
        self._on_task_fail.append(callback)

    def on_message_received(self, callback: Callable[[Dict[str, Any]], None]) -> None:
        """
        Register a callback for message received.
        
        Args:
            callback: Callback function to call when a message is received.
        """
        self._on_message_received.append(callback)

    def on_event(self, callback: Callable[[AgentEvent], None]) -> None:
        """
        Register a callback for agent events.
        
        Args:
            callback: Callback function to call for agent events.
        """
        self._on_event.append(callback)
        self._event_stream.subscribe(callback)

    # =========================================================================
    # UTILITY METHODS
    # =========================================================================

    async def _publish_event(
        self,
        event_type: str,
        data: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Publish an agent event.
        
        Args:
            event_type: Type of the event.
            data: Event data.
        """
        await self._event_stream.publish(
            self._identity.id,
            event_type,
            data or {},
        )

        # Call event callbacks
        for callback in self._on_event:
            try:
                event = AgentEvent(
                    agent_id=self._identity.id,
                    event_type=event_type,
                    data=data or {},
                )
                callback(event)
            except Exception as e:
                logger.error(f"Error in event callback: {e}")

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the agent to a dictionary.
        
        Returns:
            Dictionary representation of the agent.
        """
        return {
            "id": self._identity.id,
            "name": self._identity.name,
            "type": self._identity.type,
            "version": self._identity.version,
            "config": self._config.to_dict(),
            "profile": self._profile.to_dict(),
            "state": self._state.to_dict(),
            "metrics": self._metrics.to_dict(),
            "health": self._health.to_dict(),
            "is_running": self._running,
            "is_initialized": self._initialized,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any], **kwargs) -> "Agent":
        """
        Create an agent from a dictionary.
        
        Args:
            data: Dictionary representation of the agent.
            **kwargs: Additional arguments for initialization.
            
        Returns:
            Agent instance.
        """
        from tangku_agentos.agent_runtime.core import AgentConfig, AgentIdentity, AgentProfile

        identity_data = data.get("identity", data.get("id", {}))
        if isinstance(identity_data, str):
            identity = AgentIdentity(id=identity_data, name=data.get("name", ""))
        else:
            identity = AgentIdentity.from_dict(identity_data)

        config_data = data.get("config", {})
        config = AgentConfig.from_dict(config_data)

        profile_data = data.get("profile", {})
        profile = AgentProfile.from_dict(profile_data)

        # Create agent with provided kwargs
        agent = cls(config=config, profile=profile, **kwargs)

        # Restore state if available
        if "state" in data:
            agent._state = AgentState.from_dict(data["state"])
        if "metrics" in data:
            agent._metrics = AgentMetrics.from_dict(data["metrics"])
        if "health" in data:
            agent._health = AgentHealth.from_dict(data["health"])
        if "is_running" in data:
            agent._running = data["is_running"]
        if "is_initialized" in data:
            agent._initialized = data["is_initialized"]

        return agent

    def __repr__(self) -> str:
        """Return string representation."""
        return (
            f"Agent(id={self._identity.id}, name={self._identity.name}, "
            f"type={self._identity.type}, running={self._running})"
        )
