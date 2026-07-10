"""AI Cognitive System - Reflection Engine"""
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

class ReflectionType(Enum):
    OUTCOME=auto(); PROCESS=auto(); STRATEGY=auto(); PERFORMANCE=auto()
    LEARNING=auto(); META=auto()

@dataclass
class ReflectionResult:
    reflection_id: str; observation: Any; reflection_type: ReflectionType
    insights: List[str]=field(default_factory=list)
    lessons: List[str]=field(default_factory=list)
    improvements: List[str]=field(default_factory=list)
    confidence: float=0.0; timestamp: datetime=field(default_factory=datetime.utcnow)
    duration: float=0.0

class ReflectionEngine:
    def __init__(self, config: "CognitiveConfig", state: "CognitiveState"):
        self._config=config; self._state=state; self._initialized=False; self._started=False
        self._reflections: List[ReflectionResult]=[]; self._metrics={"reflections":0,"errors":0}
    
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
    
    async def reflect(
        self,
        observation: Any,
        context: Optional[Dict[str, Any]]=None,
        reflection_type: Optional[ReflectionType]=None
    ) -> ReflectionResult:
        """Reflect on an observation to generate insights and lessons."""
        from tangku_agentos.cognitive_system.exceptions import ReflectionError
        import time
        start_time=time.time()
        
        try:
            # Determine reflection type
            actual_type=reflection_type or ReflectionType.OUTCOME
            
            # Analyze the observation
            analysis=self._analyze_observation(observation, context)
            
            # Generate insights
            insights=self._generate_insights(analysis, actual_type)
            
            # Generate lessons
            lessons=self._generate_lessons(insights, actual_type)
            
            # Generate improvements
            improvements=self._generate_improvements(lessons, actual_type)
            
            # Calculate confidence
            confidence=self._calculate_confidence(insights, lessons, improvements)
            
            # Create reflection result
            result=ReflectionResult(
                reflection_id=self._generate_id(),
                observation=observation,
                reflection_type=actual_type,
                insights=insights,
                lessons=lessons,
                improvements=improvements,
                confidence=confidence,
                duration=time.time()-start_time
            )
            
            # Store reflection
            self._reflections.append(result)
            self._metrics["reflections"]+=1
            
            return result
            
        except Exception as e:
            self._metrics["errors"]+=1
            raise ReflectionError(f"Reflection failed: {e}") from e
    
    def _generate_id(self) -> str:
        """Generate a unique reflection ID."""
        import hashlib
        return f"refl_{hashlib.sha256(datetime.utcnow().isoformat().encode()).hexdigest()[:16]}"
    
    def _analyze_observation(self, observation: Any, context: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze the observation to extract key information."""
        analysis={"observation": observation}
        
        # Extract type
        if isinstance(observation, dict):
            analysis["type"]="structured"
            analysis.update(observation)
        elif isinstance(observation, str):
            analysis["type"]="text"
            analysis["content"]=observation
        else:
            analysis["type"]="other"
            analysis["content"]=str(observation)
        
        # Extract success/failure
        if isinstance(observation, dict):
            if "success" in observation:
                analysis["success"]=observation["success"]
            if "error" in observation:
                analysis["error"]=observation["error"]
        
        # Add context
        if context:
            analysis["context"]=context
        
        return analysis
    
    def _generate_insights(self, analysis: Dict[str, Any], reflection_type: ReflectionType) -> List[str]:
        """Generate insights from the analysis."""
        insights=[]
        
        # Common insights
        if "success" in analysis:
            if analysis["success"]:
                insights.append("The operation was successful")
            else:
                insights.append("The operation failed")
        
        if "error" in analysis:
            insights.append(f"Error occurred: {analysis['error']}")
        
        # Type-specific insights
        if reflection_type==ReflectionType.OUTCOME:
            insights.extend(self._generate_outcome_insights(analysis))
        elif reflection_type==ReflectionType.PROCESS:
            insights.extend(self._generate_process_insights(analysis))
        elif reflection_type==ReflectionType.STRATEGY:
            insights.extend(self._generate_strategy_insights(analysis))
        elif reflection_type==ReflectionType.PERFORMANCE:
            insights.extend(self._generate_performance_insights(analysis))
        
        return insights[:5]  # Limit to 5 insights
    
    def _generate_outcome_insights(self, analysis: Dict[str, Any]) -> List[str]:
        """Generate insights about outcomes."""
        insights=[]
        
        if "success" in analysis:
            if analysis["success"]:
                insights.append("Positive outcome achieved")
            else:
                insights.append("Negative outcome - operation failed")
        
        if "content" in analysis:
            content=str(analysis["content"])
            if "error" in content.lower():
                insights.append("Error mentioned in content")
            if "success" in content.lower():
                insights.append("Success mentioned in content")
        
        return insights
    
    def _generate_process_insights(self, analysis: Dict[str, Any]) -> List[str]:
        """Generate insights about the process."""
        insights=[]
        
        if "duration" in analysis:
            duration=analysis["duration"]
            if duration>10:
                insights.append("Process took longer than expected")
            else:
                insights.append("Process completed quickly")
        
        if "steps" in analysis:
            steps=analysis["steps"]
            insights.append(f"Process involved {len(steps)} steps")
        
        return insights
    
    def _generate_strategy_insights(self, analysis: Dict[str, Any]) -> List[str]:
        """Generate insights about strategy."""
        insights=[]
        
        if "strategy" in analysis:
            insights.append(f"Strategy used: {analysis['strategy']}")
        
        if "alternatives" in analysis:
            insights.append(f"{len(analysis['alternatives'])} alternative strategies considered")
        
        return insights
    
    def _generate_performance_insights(self, analysis: Dict[str, Any]) -> List[str]:
        """Generate insights about performance."""
        insights=[]
        
        if "metrics" in analysis:
            metrics=analysis["metrics"]
            if "accuracy" in metrics:
                insights.append(f"Accuracy: {metrics['accuracy']}")
            if "speed" in metrics:
                insights.append(f"Speed: {metrics['speed']}")
        
        return insights
    
    def _generate_lessons(self, insights: List[str], reflection_type: ReflectionType) -> List[str]:
        """Generate lessons from insights."""
        lessons=[]
        
        for insight in insights:
            # Convert insight to lesson
            if "success" in insight.lower():
                lessons.append(f"Lesson: {insight} - continue this approach")
            elif "error" in insight.lower() or "failed" in insight.lower():
                lessons.append(f"Lesson: {insight} - avoid this in the future")
            elif "longer" in insight.lower():
                lessons.append(f"Lesson: {insight} - optimize for speed")
            else:
                lessons.append(f"Lesson: {insight}")
        
        return lessons[:5]  # Limit to 5 lessons
    
    def _generate_improvements(self, lessons: List[str], reflection_type: ReflectionType) -> List[str]:
        """Generate improvements from lessons."""
        improvements=[]
        
        for lesson in lessons:
            # Convert lesson to improvement
            if "avoid" in lesson.lower():
                improvements.append(f"Improvement: {lesson.replace('Lesson:', '').replace('avoid', 'prevent')}")
            elif "continue" in lesson.lower():
                improvements.append(f"Improvement: {lesson.replace('Lesson:', '').replace('continue', 'reinforce')}")
            else:
                improvements.append(f"Improvement: {lesson.replace('Lesson:', '')}")
        
        return improvements[:5]  # Limit to 5 improvements
    
    def _calculate_confidence(self, insights: List[str], lessons: List[str], improvements: List[str]) -> float:
        """Calculate confidence in the reflection."""
        # More insights = higher confidence
        insight_score=min(1.0, len(insights)*0.2)
        
        # More lessons = higher confidence
        lesson_score=min(1.0, len(lessons)*0.2)
        
        # More improvements = higher confidence
        improvement_score=min(1.0, len(improvements)*0.2)
        
        # Average the scores
        confidence=(insight_score + lesson_score + improvement_score)/3
        
        return round(confidence, 2)
    
    async def get_reflection(self, reflection_id: str) -> Optional[ReflectionResult]:
        """Get a reflection by ID."""
        for reflection in self._reflections:
            if reflection.reflection_id==reflection_id:
                return reflection
        return None
    
    async def get_reflections(self, reflection_type: Optional[ReflectionType]=None) -> List[ReflectionResult]:
        """Get all reflections of a specific type."""
        if reflection_type:
            return [r for r in self._reflections if r.reflection_type==reflection_type]
        return self._reflections.copy()
    
    async def clear_reflections(self) -> None:
        """Clear all reflections."""
        self._reflections.clear()
    
    def get_metrics(self) -> Dict[str, Any]:
        return self._metrics.copy()
    
    def __repr__(self) -> str:
        return f"ReflectionEngine(initialized={self._initialized}, reflections={len(self._reflections)})"
