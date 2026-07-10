"""Action Executor for Cognitive System"""
import asyncio, logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, TYPE_CHECKING
if TYPE_CHECKING:
    from tangku_agentos.cognitive_system.core.cognitive_config import CognitiveConfig
    from tangku_agentos.cognitive_system.core.cognitive_state import CognitiveState
logger = logging.getLogger(__name__)

@dataclass
class ExecutionResult:
    execution_id: str; action: str; success: bool=False
    result: Any=None; error: Optional[str]=None
    start_time: datetime=field(default_factory=datetime.utcnow)
    end_time: datetime=field(default_factory=datetime.utcnow)
    duration: float=0.0

class ActionExecutor:
    def __init__(self, config: "CognitiveConfig", state: "CognitiveState"):
        self._config=config; self._state=state; self._executing: Dict[str, bool]= {}
        self._metrics={"executions":0,"successes":0,"failures":0}
    
    async def initialize(self)->None: pass
    async def start(self)->None: pass
    async def stop(self)->None: pass
    
    async def execute(
        self,
        tools: List[Any],
        skills: Optional[List[Any]]=None,
        context: Optional[Dict[str, Any]]=None
    ) -> Dict[str, Any]:
        """Execute a list of actions (tools and skills)."""
        from tangku_agentos.cognitive_system.exceptions import ExecutionError
        import time
        
        results=[]
        start_time=time.time()
        
        try:
            # Execute tools
            for tool in tools:
                if isinstance(tool, dict):
                    tool_id=tool.get("tool_id", "unknown")
                    tool_name=tool.get("tool_name", tool_id)
                else:
                    tool_id=str(tool)
                    tool_name=tool_id
                
                result=await self._execute_tool(tool_id, tool_name, context)
                results.append(result)
            
            # Execute skills
            if skills:
                for skill in skills:
                    if isinstance(skill, dict):
                        skill_id=skill.get("skill_id", "unknown")
                        skill_name=skill.get("skill_name", skill_id)
                    else:
                        skill_id=str(skill)
                        skill_name=skill_id
                    
                    result=await self._execute_skill(skill_id, skill_name, context)
                    results.append(result)
            
            self._metrics["executions"]+=len(tools)+(len(skills) if skills else 0)
            self._metrics["successes"]+=sum(1 for r in results if r.success)
            self._metrics["failures"]+=sum(1 for r in results if not r.success)
            
            return {
                "results": results,
                "success_count": sum(1 for r in results if r.success),
                "failure_count": sum(1 for r in results if not r.success),
                "total_duration": time.time()-start_time
            }
            
        except Exception as e:
            self._metrics["failures"]+=1
            raise ExecutionError(f"Action execution failed: {e}") from e
    
    async def _execute_tool(self, tool_id: str, tool_name: str, context: Optional[Dict[str, Any]]) -> ExecutionResult:
        """Execute a single tool."""
        import time, hashlib
        start_time=time.time()
        execution_id=f"exec_{hashlib.sha256(f'{tool_id}:{start_time}'.encode()).hexdigest()[:16]}"
        
        try:
            # Simulate tool execution
            # In a real implementation, this would call the actual tool
            result=f"Result from {tool_name}"
            
            return ExecutionResult(
                execution_id=execution_id,
                action=f"tool:{tool_id}",
                success=True,
                result=result,
                start_time=datetime.utcnow(),
                end_time=datetime.utcnow(),
                duration=time.time()-start_time
            )
        except Exception as e:
            return ExecutionResult(
                execution_id=execution_id,
                action=f"tool:{tool_id}",
                success=False,
                error=str(e),
                start_time=datetime.utcnow(),
                end_time=datetime.utcnow(),
                duration=time.time()-start_time
            )
    
    async def _execute_skill(self, skill_id: str, skill_name: str, context: Optional[Dict[str, Any]]) -> ExecutionResult:
        """Execute a single skill."""
        import time, hashlib
        start_time=time.time()
        execution_id=f"exec_{hashlib.sha256(f'{skill_id}:{start_time}'.encode()).hexdigest()[:16]}"
        
        try:
            # Simulate skill execution
            result=f"Result from {skill_name}"
            
            return ExecutionResult(
                execution_id=execution_id,
                action=f"skill:{skill_id}",
                success=True,
                result=result,
                start_time=datetime.utcnow(),
                end_time=datetime.utcnow(),
                duration=time.time()-start_time
            )
        except Exception as e:
            return ExecutionResult(
                execution_id=execution_id,
                action=f"skill:{skill_id}",
                success=False,
                error=str(e),
                start_time=datetime.utcnow(),
                end_time=datetime.utcnow(),
                duration=time.time()-start_time
            )
    
    def get_metrics(self) -> Dict[str, Any]: return self._metrics.copy()
