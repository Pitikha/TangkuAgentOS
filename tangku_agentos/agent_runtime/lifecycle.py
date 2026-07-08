"""
TangkuAgentOS Agent Runtime - Agent Lifecycle Management

This module provides lifecycle management for agents, including:
- AgentLifecycleManager: Manages agent lifecycle transitions
- AgentLifecycleState: Enum of all lifecycle states
- AgentLifecycleTransition: Represents a state transition
- State machine for agent lifecycle

The lifecycle ensures that agents transition between states in a controlled
manner, with proper validation and event publishing.

Author: TangkuAgentOS Team
License: MIT
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, TYPE_CHECKING

if TYPE_CHECKING:
    from tangku_agentos.agent_runtime.types import AgentID, AgentLifecycleState
    from tangku_agentos.agent_runtime.core import Agent
    from tangku_agentos.runtime_communication import EventBus
    from tangku_agentos.runtime_communication.integration import SystemEvents

logger = logging.getLogger(__name__)


# =============================================================================
# LIFECYCLE STATES
# =============================================================================

# Note: AgentLifecycleState is defined in types.py, but we redefine it here
# for clarity and to avoid circular imports in documentation

class LifecycleState(Enum):
    """
    Lifecycle states of an agent.
    
    These represent the complete lifecycle of an agent from creation to destruction.
    
    State Transitions:
        CREATED -> INITIALIZING -> IDLE
        IDLE -> THINKING -> IDLE
        IDLE -> PLANNING -> IDLE
        IDLE -> EXECUTING -> IDLE
        IDLE -> WAITING -> IDLE
        IDLE -> COMMUNICATING -> IDLE
        IDLE -> LEARNING -> IDLE
        IDLE -> SLEEPING -> IDLE
        IDLE -> PAUSED
        PAUSED -> IDLE
        IDLE -> STOPPED
        STOPPED -> DESTROYED
        
        Any state -> FAILED -> RECOVERING -> Any state
        Any state -> DESTROYED
    """

    # Initial states
    CREATED = auto()
    INITIALIZING = auto()

    # Active states
    IDLE = auto()
    THINKING = auto()
    PLANNING = auto()
    EXECUTING = auto()
    WAITING = auto()
    COMMUNICATING = auto()
    LEARNING = auto()
    SLEEPING = auto()

    # Inactive states
    PAUSED = auto()
    STOPPED = auto()
    FAILED = auto()
    RECOVERING = auto()
    DESTROYED = auto()


# =============================================================================
# VALID TRANSITIONS
# =============================================================================

# Define valid state transitions
VALID_TRANSITIONS: Dict[LifecycleState, Set[LifecycleState]] = {
    # Initial states
    LifecycleState.CREATED: {LifecycleState.INITIALIZING},
    LifecycleState.INITIALIZING: {LifecycleState.IDLE, LifecycleState.FAILED},

    # Active states
    LifecycleState.IDLE: {
        LifecycleState.THINKING,
        LifecycleState.PLANNING,
        LifecycleState.EXECUTING,
        LifecycleState.WAITING,
        LifecycleState.COMMUNICATING,
        LifecycleState.LEARNING,
        LifecycleState.SLEEPING,
        LifecycleState.PAUSED,
        LifecycleState.STOPPED,
        LifecycleState.FAILED,
    },
    LifecycleState.THINKING: {LifecycleState.IDLE, LifecycleState.FAILED},
    LifecycleState.PLANNING: {LifecycleState.IDLE, LifecycleState.FAILED},
    LifecycleState.EXECUTING: {LifecycleState.IDLE, LifecycleState.FAILED},
    LifecycleState.WAITING: {LifecycleState.IDLE, LifecycleState.FAILED},
    LifecycleState.COMMUNICATING: {LifecycleState.IDLE, LifecycleState.FAILED},
    LifecycleState.LEARNING: {LifecycleState.IDLE, LifecycleState.FAILED},
    LifecycleState.SLEEPING: {LifecycleState.IDLE, LifecycleState.FAILED},

    # Inactive states
    LifecycleState.PAUSED: {LifecycleState.IDLE, LifecycleState.STOPPED, LifecycleState.FAILED},
    LifecycleState.STOPPED: {LifecycleState.IDLE, LifecycleState.DESTROYED, LifecycleState.FAILED},
    LifecycleState.FAILED: {LifecycleState.RECOVERING, LifecycleState.DESTROYED},
    LifecycleState.RECOVERING: {
        LifecycleState.IDLE,
        LifecycleState.THINKING,
        LifecycleState.PLANNING,
        LifecycleState.EXECUTING,
        LifecycleState.WAITING,
        LifecycleState.COMMUNICATING,
        LifecycleState.LEARNING,
        LifecycleState.SLEEPING,
        LifecycleState.FAILED,
    },
    LifecycleState.DESTROYED: set(),  # Terminal state
}


# =============================================================================
# LIFECYCLE TRANSITION
# =============================================================================

@dataclass
class LifecycleTransition:
    """
    Represents a transition between lifecycle states.
    
    Attributes:
        agent_id: ID of the agent.
        from_state: State transitioning from.
        to_state: State transitioning to.
        timestamp: When the transition occurred.
        reason: Reason for the transition.
        metadata: Additional metadata about the transition.
    """

    agent_id: "AgentID"
    from_state: LifecycleState
    to_state: LifecycleState
    timestamp: datetime = field(default_factory=datetime.utcnow)
    reason: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

    def is_valid(self) -> bool:
        """Check if this transition is valid."""
        return self.to_state in VALID_TRANSITIONS.get(self.from_state, set())

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "agent_id": self.agent_id,
            "from_state": self.from_state.name,
            "to_state": self.to_state.name,
            "timestamp": self.timestamp.isoformat(),
            "reason": self.reason,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "LifecycleTransition":
        """Create from dictionary."""
        return cls(
            agent_id=data["agent_id"],
            from_state=LifecycleState[data["from_state"]],
            to_state=LifecycleState[data["to_state"]],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            reason=data.get("reason", ""),
            metadata=data.get("metadata", {}),
        )

    def __repr__(self) -> str:
        """Return string representation."""
        return (
            f"LifecycleTransition(agent={self.agent_id}, "
            f"{self.from_state.name} -> {self.to_state.name})"
        )


# =============================================================================
# LIFECYCLE MANAGER
# =============================================================================

class AgentLifecycleManager:
    """
    Manages the lifecycle of agents.
    
    This class is responsible for:
    - Tracking the current state of each agent
    - Validating state transitions
    - Executing state transition callbacks
    - Publishing lifecycle events
    - Managing lifecycle history
    
    Thread Safety:
        This class is thread-safe for concurrent access.
    
    Example:
        >>> from tangku_agentos.agent_runtime.lifecycle import AgentLifecycleManager
        >>> 
        >>> manager = AgentLifecycleManager()
        >>> 
        >>> # Register an agent
        >>> manager.register("agent_1")
        >>> 
        >>> # Transition to initializing
        >>> manager.transition("agent_1", LifecycleState.INITIALIZING)
        >>> 
        >>> # Transition to idle
        >>> manager.transition("agent_1", LifecycleState.IDLE)
    """

    def __init__(
        self,
        event_bus: Optional["EventBus"] = None,
        enable_events: bool = True,
        enable_history: bool = True,
        enable_validation: bool = True,
    ):
        """
        Initialize the lifecycle manager.
        
        Args:
            event_bus: Event bus for publishing lifecycle events.
            enable_events: Whether to publish lifecycle events.
            enable_history: Whether to track lifecycle history.
            enable_validation: Whether to validate state transitions.
        """
        self._states: Dict["AgentID", LifecycleState] = {}
        self._lock = asyncio.Lock()
        self._event_bus = event_bus
        self._enable_events = enable_events
        self._enable_history = enable_history
        self._enable_validation = enable_validation

        # History tracking
        self._history: Dict["AgentID", List[LifecycleTransition]] = {}
        self._max_history: int = 100

        # Callbacks
        self._on_transition: List[Callable[[LifecycleTransition], None]] = []
        self._on_state_change: Dict[LifecycleState, List[Callable[["AgentID"], None]]] = {}

        # Metrics
        self._metrics: Dict[str, Any] = {
            "transitions": 0,
            "invalid_transitions": 0,
            "state_changes": 0,
            "agents_registered": 0,
            "agents_unregistered": 0,
        }

        logger.info("AgentLifecycleManager initialized")

    async def register(self, agent_id: "AgentID", initial_state: LifecycleState = LifecycleState.CREATED) -> None:
        """
        Register an agent with the lifecycle manager.
        
        Args:
            agent_id: ID of the agent to register.
            initial_state: Initial state of the agent.
        """
        async with self._lock:
            if agent_id in self._states:
                logger.warning(f"Agent already registered: {agent_id}")
                return

            self._states[agent_id] = initial_state
            if self._enable_history:
                self._history[agent_id] = []

            self._metrics["agents_registered"] += 1

            logger.debug(f"Agent registered: {agent_id} (state={initial_state.name})")

            # Publish event
            if self._enable_events and self._event_bus:
                await self._publish_lifecycle_event(
                    agent_id,
                    "agent.registered",
                    {"initial_state": initial_state.name},
                )

    async def unregister(self, agent_id: "AgentID") -> bool:
        """
        Unregister an agent from the lifecycle manager.
        
        Args:
            agent_id: ID of the agent to unregister.
            
        Returns:
            True if the agent was unregistered, False if not found.
        """
        async with self._lock:
            if agent_id not in self._states:
                return False

            del self._states[agent_id]
            if self._enable_history and agent_id in self._history:
                del self._history[agent_id]

            self._metrics["agents_unregistered"] += 1

            logger.debug(f"Agent unregistered: {agent_id}")

            # Publish event
            if self._enable_events and self._event_bus:
                await self._publish_lifecycle_event(
                    agent_id,
                    "agent.unregistered",
                    {},
                )

            return True

    async def transition(
        self,
        agent_id: "AgentID",
        new_state: LifecycleState,
        reason: str = "",
        metadata: Optional[Dict[str, Any]] = None,
        force: bool = False,
    ) -> bool:
        """
        Transition an agent to a new state.
        
        Args:
            agent_id: ID of the agent.
            new_state: New state to transition to.
            reason: Reason for the transition.
            metadata: Additional metadata.
            force: Whether to force the transition (skip validation).
            
        Returns:
            True if the transition was successful, False otherwise.
            
        Raises:
            AgentNotFoundError: If the agent is not registered.
            AgentLifecycleError: If the transition is invalid and force is False.
        """
        async with self._lock:
            if agent_id not in self._states:
                from tangku_agentos.agent_runtime.exceptions import AgentNotFoundError
                raise AgentNotFoundError(f"Agent not found: {agent_id}")

            current_state = self._states[agent_id]

            # Check if transition is valid
            if not force and self._enable_validation:
                if new_state not in VALID_TRANSITIONS.get(current_state, set()):
                    from tangku_agentos.agent_runtime.exceptions import AgentLifecycleError
                    raise AgentLifecycleError(
                        f"Invalid transition: {current_state.name} -> {new_state.name}",
                        agent_id=agent_id,
                        from_state=current_state.name,
                        to_state=new_state.name,
                    )

            # Create transition
            transition = LifecycleTransition(
                agent_id=agent_id,
                from_state=current_state,
                to_state=new_state,
                reason=reason,
                metadata=metadata or {},
            )

            # Update state
            self._states[agent_id] = new_state
            self._metrics["transitions"] += 1
            self._metrics["state_changes"] += 1

            # Track history
            if self._enable_history:
                if agent_id not in self._history:
                    self._history[agent_id] = []
                self._history[agent_id].append(transition)
                # Trim history if too long
                if len(self._history[agent_id]) > self._max_history:
                    self._history[agent_id] = self._history[agent_id][-self._max_history:]

            # Call transition callbacks
            for callback in self._on_transition:
                try:
                    callback(transition)
                except Exception as e:
                    logger.error(f"Error in transition callback: {e}")

            # Call state change callbacks
            if new_state in self._on_state_change:
                for callback in self._on_state_change[new_state]:
                    try:
                        callback(agent_id)
                    except Exception as e:
                        logger.error(f"Error in state change callback: {e}")

            logger.debug(
                f"Agent transition: {agent_id} {current_state.name} -> {new_state.name}"
            )

            # Publish event
            if self._enable_events and self._event_bus:
                await self._publish_lifecycle_event(
                    agent_id,
                    f"agent.{new_state.name.lower()}",
                    {
                        "from_state": current_state.name,
                        "to_state": new_state.name,
                        "reason": reason,
                    },
                )

            return True

    async def get_state(self, agent_id: "AgentID") -> Optional[LifecycleState]:
        """
        Get the current state of an agent.
        
        Args:
            agent_id: ID of the agent.
            
        Returns:
            Current state of the agent, or None if not found.
        """
        async with self._lock:
            return self._states.get(agent_id)

    async def get_history(self, agent_id: "AgentID") -> List[LifecycleTransition]:
        """
        Get the lifecycle history of an agent.
        
        Args:
            agent_id: ID of the agent.
            
        Returns:
            List of lifecycle transitions for the agent.
        """
        async with self._lock:
            return self._history.get(agent_id, []).copy()

    async def is_in_state(self, agent_id: "AgentID", state: LifecycleState) -> bool:
        """
        Check if an agent is in a specific state.
        
        Args:
            agent_id: ID of the agent.
            state: State to check.
            
        Returns:
            True if the agent is in the specified state, False otherwise.
        """
        current_state = await self.get_state(agent_id)
        return current_state == state

    async def is_active(self, agent_id: "AgentID") -> bool:
        """
        Check if an agent is active (not in a terminal state).
        
        Args:
            agent_id: ID of the agent.
            
        Returns:
            True if the agent is active, False otherwise.
        """
        current_state = await self.get_state(agent_id)
        if current_state is None:
            return False
        return current_state not in {
            LifecycleState.DESTROYED,
            LifecycleState.FAILED,
        }

    async def is_available(self, agent_id: "AgentID") -> bool:
        """
        Check if an agent is available (idle or active).
        
        Args:
            agent_id: ID of the agent.
            
        Returns:
            True if the agent is available, False otherwise.
        """
        current_state = await self.get_state(agent_id)
        if current_state is None:
            return False
        return current_state in {
            LifecycleState.IDLE,
            LifecycleState.THINKING,
            LifecycleState.PLANNING,
            LifecycleState.EXECUTING,
            LifecycleState.WAITING,
            LifecycleState.COMMUNICATING,
            LifecycleState.LEARNING,
        }

    async def can_transition(self, agent_id: "AgentID", new_state: LifecycleState) -> bool:
        """
        Check if an agent can transition to a new state.
        
        Args:
            agent_id: ID of the agent.
            new_state: State to transition to.
            
        Returns:
            True if the transition is valid, False otherwise.
        """
        current_state = await self.get_state(agent_id)
        if current_state is None:
            return False
        return new_state in VALID_TRANSITIONS.get(current_state, set())

    def on_transition(self, callback: Callable[[LifecycleTransition], None]) -> None:
        """
        Register a callback for state transitions.
        
        Args:
            callback: Callback function to call on each transition.
        """
        self._on_transition.append(callback)

    def on_state_change(
        self,
        state: LifecycleState,
        callback: Callable[["AgentID"], None],
    ) -> None:
        """
        Register a callback for when agents enter a specific state.
        
        Args:
            state: State to watch for.
            callback: Callback function to call when an agent enters the state.
        """
        if state not in self._on_state_change:
            self._on_state_change[state] = []
        self._on_state_change[state].append(callback)

    def set_event_bus(self, event_bus: "EventBus") -> None:
        """
        Set the event bus for publishing lifecycle events.
        
        Args:
            event_bus: Event bus instance.
        """
        self._event_bus = event_bus

    async def _publish_lifecycle_event(
        self,
        agent_id: "AgentID",
        event_type: str,
        data: Dict[str, Any],
    ) -> None:
        """
        Publish a lifecycle event.
        
        Args:
            agent_id: ID of the agent.
            event_type: Type of event.
            data: Event data.
        """
        if not self._event_bus:
            return

        try:
            from tangku_agentos.runtime_communication import Event, MessageType
            
            event = Event(
                message_type=MessageType.EVENT,
                sender_id="agent_runtime",
                event_type=event_type,
                payload={"agent_id": agent_id, **data},
                timestamp=datetime.utcnow(),
            )
            await self._event_bus.publish(event)
        except Exception as e:
            logger.error(f"Failed to publish lifecycle event: {e}")

    def get_metrics(self) -> Dict[str, Any]:
        """
        Get lifecycle manager metrics.
        
        Returns:
            Dictionary of metrics.
        """
        return {
            **self._metrics,
            "agents": len(self._states),
            "active_agents": sum(
                1 for state in self._states.values()
                if state not in {LifecycleState.DESTROYED, LifecycleState.FAILED}
            ),
        }

    def clear(self) -> int:
        """
        Clear all registered agents.
        
        Returns:
            Number of agents cleared.
        """
        async with self._lock:
            count = len(self._states)
            self._states.clear()
            self._history.clear()
            self._metrics = {
                "transitions": 0,
                "invalid_transitions": 0,
                "state_changes": 0,
                "agents_registered": 0,
                "agents_unregistered": 0,
            }
            return count

    def shutdown(self) -> None:
        """Shutdown the lifecycle manager."""
        self._states.clear()
        self._history.clear()
        self._on_transition.clear()
        self._on_state_change.clear()
        self._metrics = {
            "transitions": 0,
            "invalid_transitions": 0,
            "state_changes": 0,
            "agents_registered": 0,
            "agents_unregistered": 0,
        }
        logger.info("AgentLifecycleManager shutdown complete")

    def __len__(self) -> int:
        """Get the number of registered agents."""
        return len(self._states)

    def __contains__(self, agent_id: "AgentID") -> bool:
        """Check if an agent is registered."""
        return agent_id in self._states

    def __repr__(self) -> str:
        """Return string representation."""
        return (
            f"AgentLifecycleManager(agents={len(self._states)}, "
            f"active={sum(1 for s in self._states.values() if s not in {LifecycleState.DESTROYED, LifecycleState.FAILED})})"
        )
