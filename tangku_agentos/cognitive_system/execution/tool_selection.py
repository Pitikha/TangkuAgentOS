"""Tool Selection Engine for Cognitive System"""
import asyncio, logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, TYPE_CHECKING
if TYPE_CHECKING:
    from tangku_agentos.cognitive_system.core.cognitive_config import CognitiveConfig
    from tangku_agentos.cognitive_system.core.cognitive_state import CognitiveState
logger = logging.getLogger(__name__)

@dataclass
class ToolMatch:
    tool_id: str; tool_name: str; match_score: float=0.0
    parameters: Dict[str, Any]=field(default_factory=dict)

class ToolSelectionEngine:
    def __init__(self, config: "CognitiveConfig", state: "CognitiveState"):
        self._config=config; self._state=state; self._tools: Dict[str, Dict[str, Any]]= {}
        self._metrics={"selections":0,"errors":0}
    
    async def initialize(self)->None: pass
    async def start(self)->None: pass
    async def stop(self)->None: pass
    
    async def select(self, task: Any, context: Optional[Dict[str, Any]]=None) -> List[ToolMatch]:
        """Select the best tools for a given task."""
        from tangku_agentos.cognitive_system.exceptions import ExecutionError
        try:
            task_str=str(task).lower()
            matches=[]
            
            for tool_id, tool in self._tools.items():
                score=self._calculate_match_score(tool, task_str, context)
                if score>0.1:
                    matches.append(ToolMatch(
                        tool_id=tool_id,
                        tool_name=tool.get("name", tool_id),
                        match_score=score
                    ))
            
            matches.sort(key=lambda x: x.match_score, reverse=True)
            self._metrics["selections"]+=1
            return matches[:5]
            
        except Exception as e:
            self._metrics["errors"]+=1
            raise ExecutionError(f"Tool selection failed: {e}") from e
    
    def _calculate_match_score(self, tool: Dict[str, Any], task: str, context: Optional[Dict[str, Any]]) -> float:
        """Calculate match score between tool and task."""
        score=0.0
        
        tool_name=tool.get("name", "").lower()
        if task in tool_name: score+=0.5
        
        description=tool.get("description", "").lower()
        if task in description: score+=0.3
        
        tags=tool.get("tags", [])
        for tag in tags:
            if task in tag.lower(): score+=0.2
        
        if context:
            for key, value in context.items():
                val_str=str(value).lower()
                if val_str in tool_name or val_str in description: score+=0.1
        
        return min(1.0, score)
    
    async def register_tool(self, tool_id: str, tool_data: Dict[str, Any]) -> None:
        """Register a new tool."""
        self._tools[tool_id]=tool_data
    
    async def unregister_tool(self, tool_id: str) -> bool:
        """Unregister a tool."""
        if tool_id in self._tools:
            del self._tools[tool_id]
            return True
        return False
    
    async def get_tool(self, tool_id: str) -> Optional[Dict[str, Any]]:
        """Get a tool by ID."""
        return self._tools.get(tool_id)
    
    async def list_tools(self) -> List[str]:
        """List all registered tools."""
        return list(self._tools.keys())
    
    async def clear_tools(self) -> None:
        """Clear all registered tools."""
        self._tools.clear()
    
    def get_metrics(self) -> Dict[str, Any]: return self._metrics.copy()
