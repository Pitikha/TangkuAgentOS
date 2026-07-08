"""
AI Cognitive System - Models

This package contains data models for the AI Cognitive System.
These models define the structure of inputs, outputs, and intermediate
data used by the cognitive engines.
"""

from tangku_agentos.cognitive_system.models.cognitive_input import CognitiveInput
from tangku_agentos.cognitive_system.models.cognitive_output import CognitiveOutput
from tangku_agentos.cognitive_system.models.other_models import (
    MemoryEntry,
    KnowledgeQuery,
    ReasoningResult,
    PlanningResult,
    DecisionResult,
    ActionPlan,
)

# For backward compatibility, also import CognitiveContext from core
from tangku_agentos.cognitive_system.core.cognitive_state import CognitiveContext

__all__ = [
    "CognitiveInput",
    "CognitiveOutput",
    "CognitiveContext",
    "MemoryEntry",
    "KnowledgeQuery",
    "ReasoningResult",
    "PlanningResult",
    "DecisionResult",
    "ActionPlan",
]
