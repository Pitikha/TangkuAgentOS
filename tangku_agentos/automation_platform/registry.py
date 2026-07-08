from __future__ import annotations

from typing import Dict

from .interfaces import AutomationRegistryInterface
from .models import AutomationDefinition


class AutomationRegistry(AutomationRegistryInterface):
    """Registry for automation definitions."""

    def __init__(self) -> None:
        self._automations: Dict[str, AutomationDefinition] = {}

    def register(self, automation: AutomationDefinition) -> None:
        self._automations[automation.automation_id] = automation

    def resolve(self, automation_id: str) -> AutomationDefinition:
        return self._automations[automation_id]

    def list_registered(self) -> list[str]:
        return list(self._automations.keys())
