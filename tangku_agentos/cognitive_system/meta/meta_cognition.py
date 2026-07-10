"""Meta-Cognition Engine for Cognitive System"""
import asyncio, logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, TYPE_CHECKING
if TYPE_CHECKING:
    from tangku_agentos.cognitive_system.core.cognitive_config import CognitiveConfig
    from tangku_agentos.cognitive_system.core.cognitive_state import CognitiveState
logger = logging.getLogger(__name__)

@dataclass
class MetaCognitionResult:
    meta_id: str; analysis: Dict[str, Any]; actions: List[str]=field(default_factory=list)
    timestamp: datetime=field(default_factory=datetime.utcnow)

class MetaCognitionEngine:
    def __init__(self, config: "CognitiveConfig", state: "CognitiveState"):
        self._config=config; self._state=state; self._metrics={"analyses":0,"errors":0}
    
    async def initialize(self)->None: pass
    async def start(self)->None: pass
    async def stop(self)->None: pass
    
    async def analyze(
        self,
        cognitive_state: Any,
        context: Optional[Dict[str, Any]]=None
    ) -> MetaCognitionResult:
        """Perform meta-cognitive analysis."""
        from tangku_agentos.cognitive_system.exceptions import MetaCognitionError
        try:
            # Analyze cognitive state
            analysis=self._analyze_cognitive_state(cognitive_state)
            
            # Generate meta-cognitive actions
            actions=self._generate_actions(analysis, context)
            
            result=MetaCognitionResult(
                meta_id=self._generate_id(),
                analysis=analysis,
                actions=actions
            )
            
            self._metrics["analyses"]+=1
            return result
            
        except Exception as e:
            self._metrics["errors"]+=1
            raise MetaCognitionError(f"Meta-cognition failed: {e}") from e
    
    def _generate_id(self) -> str:
        import hashlib
        return f"meta_{hashlib.sha256(datetime.utcnow().isoformat().encode()).hexdigest()[:16]}"
    
    def _analyze_cognitive_state(self, state: Any) -> Dict[str, Any]:
        """Analyze the cognitive state."""
        analysis={}
        
        if isinstance(state, dict):
            # Analyze each component
            if "reasoning" in state:
                analysis["reasoning"]=self._analyze_reasoning(state["reasoning"])
            if "memory" in state:
                analysis["memory"]=self._analyze_memory(state["memory"])
            if "knowledge" in state:
                analysis["knowledge"]=self._analyze_knowledge(state["knowledge"])
            if "planning" in state:
                analysis["planning"]=self._analyze_planning(state["planning"])
            if "decision" in state:
                analysis["decision"]=self._analyze_decision(state["decision"])
            if "learning" in state:
                analysis["learning"]=self._analyze_learning(state["learning"])
        
        # Calculate overall metrics
        analysis["overall"]=self._calculate_overall_metrics(analysis)
        
        return analysis
    
    def _analyze_reasoning(self, reasoning_state: Any) -> Dict[str, Any]:
        """Analyze reasoning state."""
        analysis={}
        
        if isinstance(reasoning_state, dict):
            if "confidence" in reasoning_state:
                analysis["confidence"]=reasoning_state["confidence"]
            if "steps" in reasoning_state:
                analysis["step_count"]=len(reasoning_state["steps"])
            if "duration" in reasoning_state:
                analysis["duration"]=reasoning_state["duration"]
        
        return analysis
    
    def _analyze_memory(self, memory_state: Any) -> Dict[str, Any]:
        """Analyze memory state."""
        analysis={}
        
        if isinstance(memory_state, dict):
            if "size" in memory_state:
                analysis["size"]=memory_state["size"]
            if "usage" in memory_state:
                analysis["usage"]=memory_state["usage"]
        
        return analysis
    
    def _analyze_knowledge(self, knowledge_state: Any) -> Dict[str, Any]:
        """Analyze knowledge state."""
        analysis={}
        
        if isinstance(knowledge_state, dict):
            if "count" in knowledge_state:
                analysis["count"]=knowledge_state["count"]
            if "confidence" in knowledge_state:
                analysis["avg_confidence"]=knowledge_state["confidence"]
        
        return analysis
    
    def _analyze_planning(self, planning_state: Any) -> Dict[str, Any]:
        """Analyze planning state."""
        analysis={}
        
        if isinstance(planning_state, dict):
            if "feasibility" in planning_state:
                analysis["feasibility"]=planning_state["feasibility"]
            if "risk" in planning_state:
                analysis["risk"]=planning_state["risk"]
        
        return analysis
    
    def _analyze_decision(self, decision_state: Any) -> Dict[str, Any]:
        """Analyze decision state."""
        analysis={}
        
        if isinstance(decision_state, dict):
            if "confidence" in decision_state:
                analysis["confidence"]=decision_state["confidence"]
            if "utility" in decision_state:
                analysis["utility"]=decision_state["utility"]
        
        return analysis
    
    def _analyze_learning(self, learning_state: Any) -> Dict[str, Any]:
        """Analyze learning state."""
        analysis={}
        
        if isinstance(learning_state, dict):
            if "lessons" in learning_state:
                analysis["lesson_count"]=len(learning_state["lessons"])
            if "patterns" in learning_state:
                analysis["pattern_count"]=len(learning_state["patterns"])
        
        return analysis
    
    def _calculate_overall_metrics(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate overall metrics from component analyses."""
        overall={}
        
        # Calculate average confidence
        confidences=[
            analysis.get("reasoning", {}).get("confidence", 0.5),
            analysis.get("knowledge", {}).get("avg_confidence", 0.5),
            analysis.get("decision", {}).get("confidence", 0.5)
        ]
        overall["avg_confidence"]=sum(confidences)/len(confidences) if confidences else 0.5
        
        # Calculate performance score
        performance_scores=[
            analysis.get("planning", {}).get("feasibility", 0.5),
            1-analysis.get("planning", {}).get("risk", 0.5)
        ]
        overall["performance"]=sum(performance_scores)/len(performance_scores) if performance_scores else 0.5
        
        return overall
    
    def _generate_actions(self, analysis: Dict[str, Any], context: Optional[Dict[str, Any]]) -> List[str]:
        """Generate meta-cognitive actions."""
        actions=[]
        
        # Check reasoning confidence
        reasoning_conf=analysis.get("reasoning", {}).get("confidence", 0.5)
        if reasoning_conf<0.6:
            actions.append("Adjust reasoning strategy for higher confidence")
        
        # Check knowledge confidence
        knowledge_conf=analysis.get("knowledge", {}).get("avg_confidence", 0.5)
        if knowledge_conf<0.6:
            actions.append("Verify knowledge sources for accuracy")
        
        # Check planning feasibility
        feasibility=analysis.get("planning", {}).get("feasibility", 0.5)
        if feasibility<0.6:
            actions.append("Re-evaluate plan for better feasibility")
        
        # Check planning risk
        risk=analysis.get("planning", {}).get("risk", 0.5)
        if risk>0.7:
            actions.append("Reduce plan risk through alternative approaches")
        
        # Check decision confidence
        decision_conf=analysis.get("decision", {}).get("confidence", 0.5)
        if decision_conf<0.6:
            actions.append("Gather more information for better decisions")
        
        # Check memory usage
        memory_size=analysis.get("memory", {}).get("size", 0)
        max_size=self._config.memory.working_memory_size if self._config else 1000
        if memory_size>max_size*0.8:
            actions.append("Optimize memory usage")
        
        # Check learning progress
        lesson_count=analysis.get("learning", {}).get("lesson_count", 0)
        if lesson_count<5:
            actions.append("Increase learning opportunities")
        
        return actions
    
    async def adjust_strategy(self, component: str, adjustment: str) -> Dict[str, Any]:
        """Adjust the strategy for a cognitive component."""
        # In a real implementation, this would adjust the component's strategy
        return {"component": component, "adjustment": adjustment, "status": "applied"}
    
    async def optimize_performance(self) -> Dict[str, Any]:
        """Optimize overall cognitive performance."""
        # Analyze current state
        state=self._state.get_state_info() if self._state else {}
        analysis=await self.analyze(state)
        
        # Apply optimizations
        optimizations=[]
        for action in analysis.actions:
            optimizations.append(await self.adjust_strategy("system", action))
        
        return {"analysis": analysis, "optimizations": optimizations}
    
    def get_metrics(self) -> Dict[str, Any]: return self._metrics.copy()
