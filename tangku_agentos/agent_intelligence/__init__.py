"""Agent Intelligence module for TangkuAgentOS.

This module provides the core functionality for managing agent intelligence,
including reasoning, planning, and decision-making capabilities.
"""

from .manager import AgentIntelligenceManager
from .models import AgentIntelligenceModel

__all__ = [
    "AgentIntelligenceManager",
    "AgentIntelligenceModel",
]