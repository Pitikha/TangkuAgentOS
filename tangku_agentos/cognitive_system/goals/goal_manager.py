"""Goal Manager for Cognitive System"""
import asyncio, logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from typing import Any, Dict, List, Optional, TYPE_CHECKING
if TYPE_CHECKING:
    from tangku_agentos.cognitive_system.core.cognitive_config import CognitiveConfig
    from tangku_agentos.cognitive_system.core.cognitive_state import CognitiveState
logger = logging.getLogger(__name__)

class GoalStatus(Enum):
    PENDING=auto(); ACTIVE=auto(); PAUSED=auto(); COMPLETED=auto()
    FAILED=auto(); CANCELLED=auto()

class GoalPriority(Enum):
    CRITICAL=auto(); HIGH=auto(); NORMAL=auto(); LOW=auto(); BACKGROUND=auto()

@dataclass
class Goal:
    goal_id: str; description: str; priority: GoalPriority=GoalPriority.NORMAL
    status: GoalStatus=GoalStatus.PENDING; created_at: datetime=field(default_factory=datetime.utcnow)
    updated_at: datetime=field(default_factory=datetime.utcnow)
    sub_goals: List[str]=field(default_factory=list)
    dependencies: List[str]=field(default_factory=list)
    progress: float=0.0; metadata: Dict[str, Any]=field(default_factory=dict)

class GoalManager:
    def __init__(self, config: "CognitiveConfig", state: "CognitiveState"):
        self._config=config; self._state=state; self._goals: Dict[str, Goal]={}
        self._metrics={"goals_created":0,"goals_completed":0,"errors":0}
    
    async def initialize(self)->None: pass
    async def start(self)->None: pass
    async def stop(self)->None: pass
    
    async def set_goal(
        self,
        description: str,
        priority: GoalPriority=GoalPriority.NORMAL,
        sub_goals: Optional[List[str]]=None,
        dependencies: Optional[List[str]]=None,
        metadata: Optional[Dict[str, Any]]=None
    ) -> str:
        """Set a new goal."""
        from tangku_agentos.cognitive_system.exceptions import PlanningError
        try:
            import hashlib
            goal_id=f"goal_{hashlib.sha256(f'{description}:{datetime.utcnow().isoformat()}'.encode()).hexdigest()[:16]}"
            
            goal=Goal(
                goal_id=goal_id,
                description=description,
                priority=priority,
                sub_goals=sub_goals or [],
                dependencies=dependencies or [],
                metadata=metadata or {}
            )
            
            self._goals[goal_id]=goal
            self._metrics["goals_created"]+=1
            
            logger.info(f"Goal set: {goal_id}")
            return goal_id
            
        except Exception as e:
            self._metrics["errors"]+=1
            raise PlanningError(f"Failed to set goal: {e}") from e
    
    async def get_goal(self, goal_id: str) -> Optional[Goal]:
        """Get a goal by ID."""
        return self._goals.get(goal_id)
    
    async def get_goals(self, status: Optional[GoalStatus]=None) -> List[Goal]:
        """Get all goals, optionally filtered by status."""
        if status:
            return [goal for goal in self._goals.values() if goal.status==status]
        return list(self._goals.values())
    
    async def update_goal(
        self,
        goal_id: str,
        description: Optional[str]=None,
        priority: Optional[GoalPriority]=None,
        status: Optional[GoalStatus]=None,
        progress: Optional[float]=None,
        metadata: Optional[Dict[str, Any]]=None
    ) -> bool:
        """Update a goal."""
        if goal_id not in self._goals:
            return False
        
        goal=self._goals[goal_id]
        if description: goal.description=description
        if priority: goal.priority=priority
        if status: goal.status=status
        if progress is not None: goal.progress=progress
        if metadata: goal.metadata.update(metadata)
        goal.updated_at=datetime.utcnow()
        
        return True
    
    async def complete_goal(self, goal_id: str) -> bool:
        """Mark a goal as completed."""
        if goal_id not in self._goals:
            return False
        
        self._goals[goal_id].status=GoalStatus.COMPLETED
        self._goals[goal_id].progress=1.0
        self._goals[goal_id].updated_at=datetime.utcnow()
        self._metrics["goals_completed"]+=1
        
        logger.info(f"Goal completed: {goal_id}")
        return True
    
    async def fail_goal(self, goal_id: str, reason: str="") -> bool:
        """Mark a goal as failed."""
        if goal_id not in self._goals:
            return False
        
        self._goals[goal_id].status=GoalStatus.FAILED
        self._goals[goal_id].metadata["failure_reason"]=reason
        self._goals[goal_id].updated_at=datetime.utcnow()
        
        return True
    
    async def cancel_goal(self, goal_id: str, reason: str="") -> bool:
        """Cancel a goal."""
        if goal_id not in self._goals:
            return False
        
        self._goals[goal_id].status=GoalStatus.CANCELLED
        self._goals[goal_id].metadata["cancel_reason"]=reason
        self._goals[goal_id].updated_at=datetime.utcnow()
        
        return True
    
    async def activate_goal(self, goal_id: str) -> bool:
        """Activate a goal."""
        if goal_id not in self._goals:
            return False
        
        self._goals[goal_id].status=GoalStatus.ACTIVE
        self._goals[goal_id].updated_at=datetime.utcnow()
        
        return True
    
    async def pause_goal(self, goal_id: str) -> bool:
        """Pause a goal."""
        if goal_id not in self._goals:
            return False
        
        self._goals[goal_id].status=GoalStatus.PAUSED
        self._goals[goal_id].updated_at=datetime.utcnow()
        
        return True
    
    async def remove_goal(self, goal_id: str) -> bool:
        """Remove a goal."""
        if goal_id not in self._goals:
            return False
        
        del self._goals[goal_id]
        return True
    
    async def clear_goals(self) -> None:
        """Clear all goals."""
        self._goals.clear()
    
    async def get_active_goals(self) -> List[Goal]:
        """Get all active goals."""
        return [goal for goal in self._goals.values() if goal.status==GoalStatus.ACTIVE]
    
    async def get_high_priority_goals(self) -> List[Goal]:
        """Get all high priority goals."""
        return [goal for goal in self._goals.values() if goal.priority in [GoalPriority.CRITICAL, GoalPriority.HIGH]]
    
    async def update_progress(self, goal_id: str, progress: float) -> bool:
        """Update the progress of a goal."""
        if goal_id not in self._goals:
            return False
        
        self._goals[goal_id].progress=progress
        self._goals[goal_id].updated_at=datetime.utcnow()
        
        return True
    
    def get_metrics(self) -> Dict[str, Any]: return self._metrics.copy()
