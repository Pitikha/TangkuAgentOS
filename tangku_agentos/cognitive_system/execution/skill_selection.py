"""Skill Selection Engine for Cognitive System"""
import asyncio, logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, TYPE_CHECKING
if TYPE_CHECKING:
    from tangku_agentos.cognitive_system.core.cognitive_config import CognitiveConfig
    from tangku_agentos.cognitive_system.core.cognitive_state import CognitiveState
logger = logging.getLogger(__name__)

@dataclass
class SkillMatch:
    skill_id: str; skill_name: str; match_score: float=0.0
    parameters: Dict[str, Any]=field(default_factory=dict)

class SkillSelectionEngine:
    def __init__(self, config: "CognitiveConfig", state: "CognitiveState"):
        self._config=config; self._state=state; self._skills: Dict[str, Dict[str, Any]]= {}
        self._metrics={"selections":0,"errors":0}
    
    async def initialize(self)->None: pass
    async def start(self)->None: pass
    async def stop(self)->None: pass
    
    async def select(self, task: Any, context: Optional[Dict[str, Any]]=None) -> List[SkillMatch]:
        """Select the best skills for a given task."""
        from tangku_agentos.cognitive_system.exceptions import ExecutionError
        try:
            task_str=str(task).lower()
            matches=[]
            
            for skill_id, skill in self._skills.items():
                score=self._calculate_match_score(skill, task_str, context)
                if score>0.1:
                    matches.append(SkillMatch(
                        skill_id=skill_id,
                        skill_name=skill.get("name", skill_id),
                        match_score=score
                    ))
            
            # Sort by match score
            matches.sort(key=lambda x: x.match_score, reverse=True)
            self._metrics["selections"]+=1
            return matches[:5]  # Return top 5 matches
            
        except Exception as e:
            self._metrics["errors"]+=1
            raise ExecutionError(f"Skill selection failed: {e}") from e
    
    def _calculate_match_score(self, skill: Dict[str, Any], task: str, context: Optional[Dict[str, Any]]) -> float:
        """Calculate match score between skill and task."""
        score=0.0
        
        # Match skill name
        skill_name=skill.get("name", "").lower()
        if task in skill_name:
            score+=0.5
        
        # Match skill description
        description=skill.get("description", "").lower()
        if task in description:
            score+=0.3
        
        # Match skill tags
        tags=skill.get("tags", [])
        for tag in tags:
            if task in tag.lower():
                score+=0.2
        
        # Match context
        if context:
            for key, value in context.items():
                if str(value).lower() in skill_name or str(value).lower() in description:
                    score+=0.1
        
        return min(1.0, score)
    
    async def register_skill(self, skill_id: str, skill_data: Dict[str, Any]) -> None:
        """Register a new skill."""
        self._skills[skill_id]=skill_data
    
    async def unregister_skill(self, skill_id: str) -> bool:
        """Unregister a skill."""
        if skill_id in self._skills:
            del self._skills[skill_id]
            return True
        return False
    
    async def get_skill(self, skill_id: str) -> Optional[Dict[str, Any]]:
        """Get a skill by ID."""
        return self._skills.get(skill_id)
    
    async def list_skills(self) -> List[str]:
        """List all registered skills."""
        return list(self._skills.keys())
    
    async def clear_skills(self) -> None:
        """Clear all registered skills."""
        self._skills.clear()
    
    def get_metrics(self) -> Dict[str, Any]: return self._metrics.copy()
