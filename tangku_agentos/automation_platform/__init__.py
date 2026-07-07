"""Automation platform architecture for Tangku AgentOS."""

from .interfaces import (
    AutomationContext,
    AutomationExecutor,
    AutomationManagerInterface,
    AutomationQueue,
    AutomationRegistryInterface,
    AutomationScheduler,
    AutomationSession,
    AutomationType,
)
from .manager import AutomationManager
from .registry import AutomationRegistry
from .models import AutomationDefinition, AutomationSessionModel

__all__ = [
    "AutomationManager",
    "AutomationManagerInterface",
    "AutomationRegistry",
    "AutomationRegistryInterface",
    "AutomationScheduler",
    "AutomationQueue",
    "AutomationExecutor",
    "AutomationContext",
    "AutomationSession",
    "AutomationType",
    "AutomationDefinition",
    "AutomationSessionModel",
]
