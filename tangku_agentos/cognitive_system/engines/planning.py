"""AI Cognitive System - Planning Engine"""
from __future__ import annotations
import asyncio, logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from typing import Any, Dict, List, Optional, TYPE_CHECKING
if TYPE_CHECKING:
    from tangku_agentos.cognitive_system.core.cognitive_config import CognitiveConfig
    from tangku_agentos.cognitive_system.core.cognitive_state import CognitiveState
logger = logging.getLogger(__name__)

class PlanStatus(Enum):
    PENDING=auto(); PLANNING=auto(); READY=auto(); EXECUTING=auto()
    COMPLETED=auto(); FAILED=auto(); CANCELLED=auto()

@dataclass
class PlanStep:
    step_id: str; action: str; description: str=""
    parameters: Dict[str, Any]=field(default_factory=dict)
    dependencies: List[str]=field(default_factory=list)
    resources: List[str]=field(default_factory=list)
    estimated_duration: float=0.0; priority: int=1
    status: PlanStatus=PlanStatus.PENDING

@dataclass
class PlanningResult:
    plan_id: str; goal: str; steps: List[PlanStep]=field(default_factory=list)
    dependencies: Dict[str, List[str]]=field(default_factory=dict)
    resources: Dict[str, Any]=field(default_factory=dict)
    timeline: Dict[str, Any]=field(default_factory=dict)
    confidence: float=0.0; feasibility: float=0.0; risk: float=0.0
    cost: float=0.0; status: PlanStatus=PlanStatus.PENDING
    timestamp: datetime=field(default_factory=datetime.utcnow)
    duration: float=0.0

class PlanningEngine:
    def __init__(self, config: "CognitiveConfig", state: "CognitiveState"):
        self._config=config; self._state=state; self._initialized=False; self._started=False
        self._plans: Dict[str, PlanningResult]={}; self._metrics={"plans_created":0,"errors":0}
    
    async def initialize(self)->None:
        if self._initialized: return
        self._initialized=True
    
    async def start(self)->None:
        if self._started: return
        if not self._initialized: await self.initialize()
        self._started=True
    
    async def stop(self)->None:
        if not self._started: return
        self._started=False
    
    async def plan(
        self,
        goal: str,
        context: Optional[Dict[str, Any]]=None,
        reasoning: Optional[Any]=None
    ) -> PlanningResult:
        """Create a plan to achieve the given goal."""
        from tangku_agentos.cognitive_system.exceptions import PlanningError
        import time
        start_time=time.time()
        
        try:
            # Generate plan ID
            plan_id=self._generate_plan_id(goal)
            
            # Decompose goal into sub-goals
            sub_goals=self._decompose_goal(goal, context)
            
            # Create steps for each sub-goal
            steps=self._create_steps(sub_goals, context)
            
            # Build dependency graph
            dependencies=self._build_dependencies(steps)
            
            # Calculate resources
            resources=self._calculate_resources(steps, context)
            
            # Create timeline
            timeline=self._create_timeline(steps)
            
            # Calculate metrics
            confidence=self._calculate_confidence(steps, context)
            feasibility=self._calculate_feasibility(steps, resources)
            risk, cost=self._calculate_risk_and_cost(steps, context)
            
            # Create planning result
            result=PlanningResult(
                plan_id=plan_id,
                goal=goal,
                steps=steps,
                dependencies=dependencies,
                resources=resources,
                timeline=timeline,
                confidence=confidence,
                feasibility=feasibility,
                risk=risk,
                cost=cost,
                duration=time.time()-start_time
            )
            
            # Store plan
            self._plans[plan_id]=result
            self._metrics["plans_created"]+=1
            
            return result
            
        except Exception as e:
            self._metrics["errors"]+=1
            raise PlanningError(f"Planning failed: {e}") from e
    
    def _generate_plan_id(self, goal: str) -> str:
        """Generate a unique plan ID."""
        import hashlib
        goal_str=goal[:50]
        return f"plan_{hashlib.sha256(f'{goal_str}:{datetime.utcnow().isoformat()}'.encode()).hexdigest()[:16]}"
    
    def _decompose_goal(self, goal: str, context: Optional[Dict[str, Any]]) -> List[str]:
        """Decompose a goal into sub-goals."""
        sub_goals=[]
        
        # Simple decomposition based on goal structure
        if " and " in goal.lower():
            # Split compound goals
            parts=goal.split(" and ")
            for i, part in enumerate(parts):
                sub_goals.append(f"Sub-goal {i+1}: {part.strip()}")
        elif " then " in goal.lower():
            # Split sequential goals
            parts=goal.split(" then ")
            for i, part in enumerate(parts):
                sub_goals.append(f"Step {i+1}: {part.strip()}")
        else:
            # Single goal - create implementation steps
            sub_goals=[
                f"Understand: {goal}",
                f"Prepare: {goal}",
                f"Execute: {goal}",
                f"Verify: {goal}"
            ]
        
        return sub_goals
    
    def _create_steps(self, sub_goals: List[str], context: Optional[Dict[str, Any]]) -> List[PlanStep]:
        """Create plan steps from sub-goals."""
        steps=[]
        
        for i, sub_goal in enumerate(sub_goals):
            step_id=f"step_{i+1}"
            
            # Extract action from sub-goal
            action=self._extract_action(sub_goal)
            
            # Create step
            step=PlanStep(
                step_id=step_id,
                action=action,
                description=sub_goal,
                priority=len(sub_goals)-i,  # Higher priority for earlier steps
                estimated_duration=self._estimate_duration(action, context)
            )
            steps.append(step)
        
        return steps
    
    def _extract_action(self, sub_goal: str) -> str:
        """Extract the action from a sub-goal."""
        # Remove prefixes like "Step 1:", "Sub-goal 2:", etc.
        cleaned=re.sub(r'^(step|sub-goal|goal)\s+\d+:\s*', '', sub_goal, flags=re.IGNORECASE)
        
        # Extract the verb (action)
        words=cleaned.split()
        if words:
            # Return the first word as the action
            return words[0].lower()
        
        return "execute"
    
    def _estimate_duration(self, action: str, context: Optional[Dict[str, Any]]) -> float:
        """Estimate duration for an action."""
        # Simple duration estimation based on action type
        action_durations={
            "understand": 5.0,
            "prepare": 10.0,
            "execute": 15.0,
            "verify": 5.0,
            "analyze": 10.0,
            "create": 20.0,
            "build": 30.0,
            "test": 15.0,
            "deploy": 20.0,
        }
        
        return action_durations.get(action.lower(), 10.0)
    
    def _build_dependencies(self, steps: List[PlanStep]) -> Dict[str, List[str]]:
        """Build dependency graph for steps."""
        dependencies={}
        
        # Simple dependency: each step depends on the previous one
        for i, step in enumerate(steps):
            if i>0:
                dependencies[step.step_id]=[steps[i-1].step_id]
            else:
                dependencies[step.step_id]=[]
        
        return dependencies
    
    def _calculate_resources(self, steps: List[PlanStep], context: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate resources required for the plan."""
        resources={"cpu": 0, "memory": 0, "storage": 0, "time": 0}
        
        for step in steps:
            # Add estimated time
            resources["time"]+=step.estimated_duration
            
            # Add resource estimates based on action
            if step.action in ["build", "create", "deploy"]:
                resources["cpu"]+=2
                resources["memory"]+=1
            elif step.action in ["analyze", "test", "verify"]:
                resources["cpu"]+=1
                resources["memory"]+=0.5
            else:
                resources["cpu"]+=0.5
        
        return resources
    
    def _create_timeline(self, steps: List[PlanStep]) -> Dict[str, Any]:
        """Create a timeline for the plan."""
        timeline={"start_time": datetime.utcnow().isoformat(), "steps": []}
        current_time=0.0
        
        for step in steps:
            step_timeline={
                "step_id": step.step_id,
                "action": step.action,
                "start_time": current_time,
                "end_time": current_time + step.estimated_duration,
                "duration": step.estimated_duration
            }
            timeline["steps"].append(step_timeline)
            current_time+=step.estimated_duration
        
        timeline["total_duration"]=current_time
        timeline["end_time"]=current_time
        
        return timeline
    
    def _calculate_confidence(self, steps: List[PlanStep], context: Optional[Dict[str, Any]]) -> float:
        """Calculate confidence in the plan."""
        if not steps:
            return 0.0
        
        # Simple confidence calculation
        # More steps = lower confidence
        step_penalty=len(steps)*0.05
        
        # Known actions = higher confidence
        known_actions={"understand", "prepare", "execute", "verify", "analyze", "create", "build", "test", "deploy"}
        action_confidence=sum(1 for step in steps if step.action.lower() in known_actions)/len(steps)
        
        confidence=0.8 - step_penalty + (action_confidence*0.2)
        return min(1.0, max(0.0, confidence))
    
    def _calculate_feasibility(self, steps: List[PlanStep], resources: Dict[str, Any]) -> float:
        """Calculate feasibility of the plan."""
        if not steps:
            return 0.0
        
        # Simple feasibility calculation
        # Check if we have enough resources
        resource_feasibility=1.0
        
        # Check time feasibility
        total_time=resources.get("time", 0)
        if total_time>3600:  # More than 1 hour
            resource_feasibility*=0.7
        elif total_time>1800:  # More than 30 minutes
            resource_feasibility*=0.85
        
        # Check CPU feasibility
        cpu=resources.get("cpu", 0)
        if cpu>4:
            resource_feasibility*=0.7
        
        return min(1.0, max(0.0, resource_feasibility))
    
    def _calculate_risk_and_cost(self, steps: List[PlanStep], context: Optional[Dict[str, Any]]) -> Tuple[float, float]:
        """Calculate risk and cost of the plan."""
        risk=0.0
        cost=0.0
        
        for step in steps:
            # Calculate risk based on action
            action_risk={
                "understand": 0.1,
                "prepare": 0.1,
                "execute": 0.3,
                "verify": 0.1,
                "analyze": 0.2,
                "create": 0.4,
                "build": 0.5,
                "test": 0.2,
                "deploy": 0.6,
            }.get(step.action.lower(), 0.2)
            
            risk+=action_risk
            cost+=step.estimated_duration*0.1  # Cost per time unit
        
        # Normalize risk
        risk=min(1.0, risk/len(steps) if steps else 0.0)
        
        return risk, cost
    
    async def get_plan(self, plan_id: str) -> Optional[PlanningResult]:
        """Get a plan by ID."""
        return self._plans.get(plan_id)
    
    async def update_plan_status(self, plan_id: str, status: PlanStatus) -> bool:
        """Update the status of a plan."""
        if plan_id not in self._plans:
            return False
        
        self._plans[plan_id].status=status
        return True
    
    async def cancel_plan(self, plan_id: str) -> bool:
        """Cancel a plan."""
        if plan_id not in self._plans:
            return False
        
        self._plans[plan_id].status=PlanStatus.CANCELLED
        return True
    
    async def get_plans(self) -> List[PlanningResult]:
        """Get all plans."""
        return list(self._plans.values())
    
    async def clear_plans(self) -> None:
        """Clear all plans."""
        self._plans.clear()
    
    def get_metrics(self) -> Dict[str, Any]:
        return self._metrics.copy()
    
    def __repr__(self) -> str:
        return f"PlanningEngine(initialized={self._initialized}, plans={len(self._plans)})"
