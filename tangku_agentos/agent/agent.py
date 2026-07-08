"""
Agent Model and Base Class

Defines the core agent interface and lifecycle management.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, Optional, List, Callable
from datetime import datetime, timedelta
from enum import Enum
import uuid
import logging

logger = logging.getLogger(__name__)


class AgentState(Enum):
    """Agent lifecycle states."""
    UNINITIALIZED = "uninitialized"
    INITIALIZING = "initializing"
    READY = "ready"
    BUSY = "busy"
    PAUSED = "paused"
    STOPPING = "stopping"
    STOPPED = "stopped"
    ERROR = "error"
    UNHEALTHY = "unhealthy"


class AgentCapability(Enum):
    """Standard agent capabilities."""
    TASK_EXECUTION = "task_execution"
    MESSAGE_HANDLING = "message_handling"
    WORKFLOW_ORCHESTRATION = "workflow_orchestration"
    STATE_MANAGEMENT = "state_management"
    RESOURCE_ALLOCATION = "resource_allocation"
    MONITORING = "monitoring"
    PERSISTENCE = "persistence"
    CACHING = "caching"


@dataclass
class AgentHealth:
    """Agent health status."""
    status: str = "healthy"  # healthy, degraded, unhealthy
    last_heartbeat: datetime = field(default_factory=datetime.utcnow)
    error_count: int = 0
    error_rate: float = 0.0  # Percentage of failed operations
    memory_usage_mb: float = 0.0
    cpu_usage_percent: float = 0.0
    response_time_ms: float = 0.0
    uptime_seconds: float = 0.0


@dataclass
class AgentMetrics:
    """Agent performance metrics."""
    messages_received: int = 0
    messages_processed: int = 0
    messages_failed: int = 0
    tasks_executed: int = 0
    tasks_completed: int = 0
    tasks_failed: int = 0
    total_processing_time_ms: float = 0.0
    average_response_time_ms: float = 0.0
    peak_memory_usage_mb: float = 0.0
    started_at: datetime = field(default_factory=datetime.utcnow)

    def uptime_seconds(self) -> float:
        """Get agent uptime in seconds."""
        return (datetime.utcnow() - self.started_at).total_seconds()

    def success_rate(self) -> float:
        """Calculate success rate for processed messages."""
        total = self.messages_processed
        if total == 0:
            return 100.0
        return (self.messages_processed - self.messages_failed) / total * 100


class Agent:
    """
    Base agent class with lifecycle management.
    
    Every agent in TangkuAgentOS inherits from this class.
    """

    def __init__(
        self,
        name: str,
        agent_type: str = "generic",
        capabilities: Optional[List[AgentCapability]] = None,
    ):
        self.agent_id: str = str(uuid.uuid4())
        self.name = name
        self.agent_type = agent_type
        self.capabilities = capabilities or [AgentCapability.MESSAGE_HANDLING]
        
        self.state = AgentState.UNINITIALIZED
        self.health = AgentHealth()
        self.metrics = AgentMetrics()
        
        self.created_at = datetime.utcnow()
        self.started_at: Optional[datetime] = None
        self.stopped_at: Optional[datetime] = None
        
        self.metadata: Dict[str, Any] = {}
        self.tags: List[str] = []
        
        self.message_handlers: Dict[str, Callable] = {}
        self.error_callbacks: List[Callable] = []
        
        self.config: Dict[str, Any] = {}

    async def initialize(self) -> bool:
        """
        Initialize agent.
        
        Called once when agent is created.
        Subclasses should override to perform setup.
        
        Returns:
            True if successful
        """
        try:
            self.state = AgentState.INITIALIZING
            logger.info(f"Agent {self.name} ({self.agent_id}) initializing")
            
            # Perform initialization
            await self._setup()
            
            self.state = AgentState.READY
            self.started_at = datetime.utcnow()
            logger.info(f"Agent {self.name} ready")
            return True
            
        except Exception as e:
            logger.error(f"Agent {self.name} initialization failed: {e}")
            self.state = AgentState.ERROR
            self.health.status = "unhealthy"
            return False

    async def start(self) -> None:
        """Start agent main loop."""
        self.state = AgentState.READY
        logger.info(f"Agent {self.name} started")

    async def shutdown(self) -> None:
        """Shutdown agent gracefully."""
        try:
            self.state = AgentState.STOPPING
            logger.info(f"Agent {self.name} shutting down")
            
            await self._cleanup()
            
            self.state = AgentState.STOPPED
            self.stopped_at = datetime.utcnow()
            logger.info(f"Agent {self.name} stopped")
            
        except Exception as e:
            logger.error(f"Error shutting down agent {self.name}: {e}")
            self.state = AgentState.ERROR

    async def _setup(self) -> None:
        """
        Override this method to perform agent-specific setup.
        """
        pass

    async def _cleanup(self) -> None:
        """
        Override this method to perform agent-specific cleanup.
        """
        pass

    async def handle_message(self, message: Any) -> Any:
        """
        Handle incoming message.
        
        Override in subclass to implement message handling logic.
        """
        self.metrics.messages_received += 1
        
        try:
            # Call registered handler if exists
            message_type = getattr(message, 'message_type', 'unknown')
            handler = self.message_handlers.get(message_type)
            
            if handler:
                result = await handler(message) if callable(handler) else None
                self.metrics.messages_processed += 1
                return result
            else:
                logger.warning(
                    f"No handler for message type: {message_type}"
                )
                return None
                
        except Exception as e:
            logger.error(f"Error handling message: {e}")
            self.metrics.messages_failed += 1
            await self._call_error_callbacks(e)
            raise

    def register_message_handler(
        self,
        message_type: str,
        handler: Callable,
    ) -> None:
        """Register handler for message type."""
        self.message_handlers[message_type] = handler
        logger.debug(f"Handler registered for {message_type}")

    def register_error_callback(self, callback: Callable) -> None:
        """Register callback for errors."""
        self.error_callbacks.append(callback)

    async def _call_error_callbacks(self, error: Exception) -> None:
        """Call all registered error callbacks."""
        for callback in self.error_callbacks:
            try:
                await callback(error) if callable(callback) else None
            except Exception as e:
                logger.error(f"Error in error callback: {e}")

    def add_capability(self, capability: AgentCapability) -> None:
        """Add capability to agent."""
        if capability not in self.capabilities:
            self.capabilities.append(capability)

    def has_capability(self, capability: AgentCapability) -> bool:
        """Check if agent has capability."""
        return capability in self.capabilities

    def is_healthy(self) -> bool:
        """Check if agent is healthy."""
        return self.health.status == "healthy"

    def is_ready(self) -> bool:
        """Check if agent is ready to handle tasks."""
        return self.state == AgentState.READY

    def pause(self) -> None:
        """Pause agent."""
        if self.state == AgentState.READY:
            self.state = AgentState.PAUSED
            logger.info(f"Agent {self.name} paused")

    def resume(self) -> None:
        """Resume paused agent."""
        if self.state == AgentState.PAUSED:
            self.state = AgentState.READY
            logger.info(f"Agent {self.name} resumed")

    def to_dict(self) -> Dict[str, Any]:
        """Serialize agent to dictionary."""
        return {
            "agent_id": self.agent_id,
            "name": self.name,
            "type": self.agent_type,
            "state": self.state.value,
            "health": self.health.status,
            "capabilities": [c.value for c in self.capabilities],
            "created_at": self.created_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "metrics": {
                "messages_received": self.metrics.messages_received,
                "messages_processed": self.metrics.messages_processed,
                "success_rate": self.metrics.success_rate(),
            },
        }
