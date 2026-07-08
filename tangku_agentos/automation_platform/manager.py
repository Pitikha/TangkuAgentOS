from __future__ import annotations

from typing import Dict

from .interfaces import AutomationManagerInterface
from .models import AutomationDefinition, AutomationSessionModel
from .registry import AutomationRegistry


class AutomationManager(AutomationManagerInterface):
    """Manager for automation platform operations."""

    def __init__(self, registry: AutomationRegistry) -> None:
        self._registry = registry
        self._sessions: Dict[str, AutomationSessionModel] = {}

    def register_automation(self, automation: AutomationDefinition) -> None:
        self._registry.register(automation)

    def schedule_automation(self, automation_id: str) -> None:
        _ = self._registry.resolve(automation_id)

    def enqueue_automation(self, automation_id: str) -> None:
        _ = self._registry.resolve(automation_id)

    def start_session(self, session_id: str, automation_id: str) -> AutomationSessionModel:
        automation = self._registry.resolve(automation_id)
        session = AutomationSessionModel(session_id=session_id, automation_id=automation.automation_id, status="started", active=True)
        self._sessions[session_id] = session
        return session
