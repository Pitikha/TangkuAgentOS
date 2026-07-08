"""
AI Cognitive System - Core Components

This package contains the core components of the AI Cognitive System:
- CognitiveAgent: The main agent class
- CognitiveConfig: Configuration for cognitive agents
- CognitiveState: State management for cognitive processes
- CognitiveLoop: The continuous thinking cycle
- CognitiveProfile: Thinking style configurations
"""

from tangku_agentos.cognitive_system.core.cognitive_agent import CognitiveAgent
from tangku_agentos.cognitive_system.core.cognitive_config import CognitiveConfig
from tangku_agentos.cognitive_system.core.cognitive_state import CognitiveState
from tangku_agentos.cognitive_system.core.cognitive_loop import CognitiveLoop
from tangku_agentos.cognitive_system.core.cognitive_profile import CognitiveProfile

__all__ = [
    "CognitiveAgent",
    "CognitiveConfig",
    "CognitiveState",
    "CognitiveLoop",
    "CognitiveProfile",
]
