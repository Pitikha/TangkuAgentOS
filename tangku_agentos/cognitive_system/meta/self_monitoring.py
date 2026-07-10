"""Self-Monitoring Engine for Cognitive System"""
import asyncio, logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, TYPE_CHECKING
if TYPE_CHECKING:
    from tangku_agentos.cognitive_system.core.cognitive_config import CognitiveConfig
    from tangku_agentos.cognitive_system.core.cognitive_state import CognitiveState
logger = logging.getLogger(__name__)

@dataclass
class MonitoringResult:
    monitoring_id: str; component: str; status: str
    metrics: Dict[str, Any]=field(default_factory=dict)
    issues: List[str]=field(default_factory=list)
    timestamp: datetime=field(default_factory=datetime.utcnow)

class SelfMonitoringEngine:
    def __init__(self, config: "CognitiveConfig", state: "CognitiveState"):
        self._config=config; self._state=state; self._metrics={"checks":0,"errors":0}
    
    async def initialize(self)->None: pass
    async def start(self)->None: pass
    async def stop(self)->None: pass
    
    async def monitor(self, component: str, data: Any) -> MonitoringResult:
        """Monitor a cognitive component."""
        from tangku_agentos.cognitive_system.exceptions import MonitoringError
        try:
            # Check component health
            status, metrics, issues=self._check_component(component, data)
            
            result=MonitoringResult(
                monitoring_id=self._generate_id(),
                component=component,
                status=status,
                metrics=metrics,
                issues=issues
            )
            
            self._metrics["checks"]+=1
            return result
            
        except Exception as e:
            self._metrics["errors"]+=1
            raise MonitoringError(f"Monitoring failed: {e}") from e
    
    def _generate_id(self) -> str:
        import hashlib
        return f"mon_{hashlib.sha256(datetime.utcnow().isoformat().encode()).hexdigest()[:16]}"
    
    def _check_component(self, component: str, data: Any) -> Tuple[str, Dict[str, Any], List[str]]:
        """Check the health of a component."""
        status="healthy"
        metrics={}
        issues=[]
        
        if component=="reasoning":
            metrics, issues=self._check_reasoning(data)
        elif component=="memory":
            metrics, issues=self._check_memory(data)
        elif component=="knowledge":
            metrics, issues=self._check_knowledge(data)
        elif component=="planning":
            metrics, issues=self._check_planning(data)
        elif component=="decision":
            metrics, issues=self._check_decision(data)
        else:
            metrics={"status": "unknown"}
        
        if issues:
            status="degraded" if len(issues)<3 else "unhealthy"
        
        return status, metrics, issues
    
    def _check_reasoning(self, data: Any) -> Tuple[Dict[str, Any], List[str]]:
        """Check reasoning component."""
        metrics={}
        issues=[]
        
        if isinstance(data, dict):
            if "confidence" in data:
                metrics["confidence"]=data["confidence"]
                if data["confidence"]<0.5:
                    issues.append("Low reasoning confidence")
            if "steps" in data:
                metrics["steps"]=len(data["steps"])
                if len(data["steps"])>10:
                    issues.append("Too many reasoning steps")
        
        return metrics, issues
    
    def _check_memory(self, data: Any) -> Tuple[Dict[str, Any], List[str]]:
        """Check memory component."""
        metrics={}
        issues=[]
        
        if isinstance(data, dict):
            if "size" in data:
                metrics["size"]=data["size"]
                max_size=self._config.memory.working_memory_size if self._config else 1000
                if data["size"]>max_size*0.9:
                    issues.append("Memory usage high")
            if "errors" in data:
                metrics["errors"]=data["errors"]
                if data["errors"]>0:
                    issues.append(f"Memory errors: {data['errors']}")
        
        return metrics, issues
    
    def _check_knowledge(self, data: Any) -> Tuple[Dict[str, Any], List[str]]:
        """Check knowledge component."""
        metrics={}
        issues=[]
        
        if isinstance(data, dict):
            if "count" in data:
                metrics["count"]=data["count"]
            if "confidence" in data:
                metrics["avg_confidence"]=data["confidence"]
                if data["confidence"]<0.6:
                    issues.append("Low knowledge confidence")
        
        return metrics, issues
    
    def _check_planning(self, data: Any) -> Tuple[Dict[str, Any], List[str]]:
        """Check planning component."""
        metrics={}
        issues=[]
        
        if isinstance(data, dict):
            if "feasibility" in data:
                metrics["feasibility"]=data["feasibility"]
                if data["feasibility"]<0.5:
                    issues.append("Low plan feasibility")
            if "risk" in data:
                metrics["risk"]=data["risk"]
                if data["risk"]>0.7:
                    issues.append("High plan risk")
        
        return metrics, issues
    
    def _check_decision(self, data: Any) -> Tuple[Dict[str, Any], List[str]]:
        """Check decision component."""
        metrics={}
        issues=[]
        
        if isinstance(data, dict):
            if "confidence" in data:
                metrics["confidence"]=data["confidence"]
                if data["confidence"]<0.5:
                    issues.append("Low decision confidence")
            if "utility" in data:
                metrics["utility"]=data["utility"]
        
        return metrics, issues
    
    async def self_evaluate(self) -> Dict[str, Any]:
        """Perform self-evaluation of the cognitive system."""
        results={}
        
        # Evaluate each component
        components=["reasoning", "memory", "knowledge", "planning", "decision"]
        for component in components:
            result=await self.monitor(component, {})
            results[component]=result.status
        
        return {"component_status": results, "overall": self._calculate_overall_status(results)}
    
    def _calculate_overall_status(self, component_status: Dict[str, str]) -> str:
        """Calculate overall system status."""
        healthy_count=sum(1 for status in component_status.values() if status=="healthy")
        total=len(component_status)
        
        if healthy_count==total:
            return "healthy"
        elif healthy_count>=total*0.7:
            return "degraded"
        else:
            return "unhealthy"
    
    def get_metrics(self) -> Dict[str, Any]: return self._metrics.copy()
