"""AI Cognitive System - Learning Engine"""
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

class LearningType(Enum):
    EXPERIENCE=auto(); PATTERN=auto(); SKILL=auto(); FAILURE=auto()
    SUCCESS=auto(); FEEDBACK=auto(); PREFERENCE=auto(); MEMORY=auto()
    KNOWLEDGE=auto()

@dataclass
class LearningResult:
    learning_id: str; reflection: Any; learning_type: LearningType
    lessons_learned: List[str]=field(default_factory=list)
    patterns_identified: List[str]=field(default_factory=list)
    skills_improved: List[str]=field(default_factory=list)
    knowledge_updated: List[str]=field(default_factory=list)
    memory_updates: List[str]=field(default_factory=list)
    confidence: float=0.0; timestamp: datetime=field(default_factory=datetime.utcnow)
    duration: float=0.0

class LearningEngine:
    def __init__(self, config: "CognitiveConfig", state: "CognitiveState"):
        self._config=config; self._state=state; self._initialized=False; self._started=False
        self._learned_lessons: List[str]=[]; self._identified_patterns: List[str]=[]
        self._improved_skills: List[str]=[]; self._metrics={"learning_operations":0,"errors":0}
    
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
    
    async def learn(
        self,
        reflection: Any,
        context: Optional[Dict[str, Any]]=None
    ) -> LearningResult:
        """Learn from a reflection or experience."""
        from tangku_agentos.cognitive_system.exceptions import LearningError
        import time
        start_time=time.time()
        
        try:
            # Determine learning type
            learning_type=self._determine_learning_type(reflection, context)
            
            # Extract lessons
            lessons_learned=self._extract_lessons(reflection, learning_type)
            
            # Identify patterns
            patterns_identified=self._identify_patterns(reflection, context, learning_type)
            
            # Improve skills
            skills_improved=self._improve_skills(reflection, context, learning_type)
            
            # Update knowledge
            knowledge_updated=self._update_knowledge(reflection, context, learning_type)
            
            # Update memory
            memory_updates=self._update_memory(reflection, context, learning_type)
            
            # Calculate confidence
            confidence=self._calculate_confidence(lessons_learned, patterns_identified, skills_improved)
            
            # Create learning result
            result=LearningResult(
                learning_id=self._generate_id(),
                reflection=reflection,
                learning_type=learning_type,
                lessons_learned=lessons_learned,
                patterns_identified=patterns_identified,
                skills_improved=skills_improved,
                knowledge_updated=knowledge_updated,
                memory_updates=memory_updates,
                confidence=confidence,
                duration=time.time()-start_time
            )
            
            # Store learned information
            self._learned_lessons.extend(lessons_learned)
            self._identified_patterns.extend(patterns_identified)
            self._improved_skills.extend(skills_improved)
            
            self._metrics["learning_operations"]+=1
            return result
            
        except Exception as e:
            self._metrics["errors"]+=1
            raise LearningError(f"Learning failed: {e}") from e
    
    def _generate_id(self) -> str:
        """Generate a unique learning ID."""
        import hashlib
        return f"learn_{hashlib.sha256(datetime.utcnow().isoformat().encode()).hexdigest()[:16]}"
    
    def _determine_learning_type(self, reflection: Any, context: Optional[Dict[str, Any]]) -> LearningType:
        """Determine the type of learning to perform."""
        if context and "learning_type" in context:
            try:
                return LearningType[context["learning_type"].upper()]
            except KeyError:
                pass
        
        # Default to experience learning
        return LearningType.EXPERIENCE
    
    def _extract_lessons(self, reflection: Any, learning_type: LearningType) -> List[str]:
        """Extract lessons from the reflection."""
        lessons=[]
        
        if isinstance(reflection, dict):
            if "lessons" in reflection:
                lessons.extend(reflection["lessons"])
            if "lesson" in reflection:
                lessons.append(reflection["lesson"])
        elif isinstance(reflection, str):
            # Simple lesson extraction
            if "lesson" in reflection.lower():
                lessons.append(reflection)
        
        # Type-specific lessons
        if learning_type==LearningType.FAILURE:
            lessons.extend(self._extract_failure_lessons(reflection))
        elif learning_type==LearningType.SUCCESS:
            lessons.extend(self._extract_success_lessons(reflection))
        elif learning_type==LearningType.FEEDBACK:
            lessons.extend(self._extract_feedback_lessons(reflection))
        
        return lessons[:5]  # Limit to 5 lessons
    
    def _extract_failure_lessons(self, reflection: Any) -> List[str]:
        """Extract lessons from failures."""
        lessons=[]
        
        if isinstance(reflection, dict):
            if "error" in reflection:
                lessons.append(f"Avoid: {reflection['error']}")
            if "mistake" in reflection:
                lessons.append(f"Don't repeat: {reflection['mistake']}")
        elif isinstance(reflection, str):
            if "error" in reflection.lower():
                lessons.append(f"Avoid errors like: {reflection}")
            if "failed" in reflection.lower():
                lessons.append(f"Learn from failure: {reflection}")
        
        return lessons
    
    def _extract_success_lessons(self, reflection: Any) -> List[str]:
        """Extract lessons from successes."""
        lessons=[]
        
        if isinstance(reflection, dict):
            if "success" in reflection:
                lessons.append(f"Continue: {reflection.get('success', reflection)}")
        elif isinstance(reflection, str):
            if "success" in reflection.lower():
                lessons.append(f"Reinforce success: {reflection}")
        
        return lessons
    
    def _extract_feedback_lessons(self, reflection: Any) -> List[str]:
        """Extract lessons from feedback."""
        lessons=[]
        
        if isinstance(reflection, dict):
            if "feedback" in reflection:
                feedback=reflection["feedback"]
                if isinstance(feedback, str):
                    lessons.append(f"Apply feedback: {feedback}")
                elif isinstance(feedback, list):
                    for fb in feedback:
                        lessons.append(f"Apply feedback: {fb}")
        
        return lessons
    
    def _identify_patterns(self, reflection: Any, context: Optional[Dict[str, Any]], learning_type: LearningType) -> List[str]:
        """Identify patterns from the reflection."""
        patterns=[]
        
        # Simple pattern identification
        if isinstance(reflection, dict):
            for key, value in reflection.items():
                if isinstance(value, (list, dict)):
                    patterns.append(f"Pattern in {key}: {len(value)} items")
        
        # Type-specific patterns
        if learning_type==LearningType.PATTERN:
            patterns.extend(self._identify_data_patterns(reflection))
        
        return patterns[:5]  # Limit to 5 patterns
    
    def _identify_data_patterns(self, data: Any) -> List[str]:
        """Identify patterns in data."""
        patterns=[]
        
        if isinstance(data, list):
            patterns.append(f"List pattern: {len(data)} items")
            if len(data)>1:
                first=str(data[0])
                if all(str(item)==first for item in data[1:]):
                    patterns.append("All items are identical")
        elif isinstance(data, dict):
            patterns.append(f"Dictionary pattern: {len(data)} keys")
        
        return patterns
    
    def _improve_skills(self, reflection: Any, context: Optional[Dict[str, Any]], learning_type: LearningType) -> List[str]:
        """Identify skills that can be improved."""
        skills=[]
        
        # Simple skill improvement identification
        if isinstance(reflection, dict):
            if "skill" in reflection:
                skills.append(f"Improve: {reflection['skill']}")
            if "skills" in reflection:
                skills.extend([f"Improve: {s}" for s in reflection["skills"]])
        
        return skills[:5]  # Limit to 5 skills
    
    def _update_knowledge(self, reflection: Any, context: Optional[Dict[str, Any]], learning_type: LearningType) -> List[str]:
        """Identify knowledge updates."""
        updates=[]
        
        # Simple knowledge update identification
        if isinstance(reflection, dict):
            if "knowledge" in reflection:
                updates.append(f"Update: {reflection['knowledge']}")
            if "new_info" in reflection:
                updates.append(f"Add: {reflection['new_info']}")
        
        return updates[:5]  # Limit to 5 updates
    
    def _update_memory(self, reflection: Any, context: Optional[Dict[str, Any]], learning_type: LearningType) -> List[str]:
        """Identify memory updates."""
        updates=[]
        
        # Simple memory update identification
        if isinstance(reflection, dict):
            if "memory" in reflection:
                updates.append(f"Remember: {reflection['memory']}")
        
        return updates[:5]  # Limit to 5 updates
    
    def _calculate_confidence(
        self,
        lessons: List[str],
        patterns: List[str],
        skills: List[str]
    ) -> float:
        """Calculate confidence in the learning."""
        # More lessons = higher confidence
        lesson_score=min(1.0, len(lessons)*0.2)
        
        # More patterns = higher confidence
        pattern_score=min(1.0, len(patterns)*0.2)
        
        # More skills = higher confidence
        skill_score=min(1.0, len(skills)*0.2)
        
        # Average the scores
        confidence=(lesson_score + pattern_score + skill_score)/3
        
        return round(confidence, 2)
    
    async def get_learned_lessons(self) -> List[str]:
        """Get all learned lessons."""
        return self._learned_lessons.copy()
    
    async def get_identified_patterns(self) -> List[str]:
        """Get all identified patterns."""
        return self._identified_patterns.copy()
    
    async def get_improved_skills(self) -> List[str]:
        """Get all improved skills."""
        return self._improved_skills.copy()
    
    async def clear_learning(self) -> None:
        """Clear all learned information."""
        self._learned_lessons.clear()
        self._identified_patterns.clear()
        self._improved_skills.clear()
    
    def get_metrics(self) -> Dict[str, Any]:
        return self._metrics.copy()
    
    def __repr__(self) -> str:
        return f"LearningEngine(initialized={self._initialized}, lessons={len(self._learned_lessons)})"
