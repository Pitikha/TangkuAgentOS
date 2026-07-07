from __future__ import annotations

from typing import Dict

from .interfaces import CodingManagerInterface
from .models import CodingConfigurationModel, CodingSession
from .registry import CodingRegistry


class CodingManager(CodingManagerInterface):
    """Manager for coding platform sessions and language support."""

    def __init__(self, registry: CodingRegistry) -> None:
        self._registry = registry
        self._sessions: Dict[str, CodingSession] = {}

    def create_session(self, session_id: str, configuration: CodingConfigurationModel) -> CodingSession:
        session = CodingSession(session_id=session_id, configuration=configuration)
        self._sessions[session_id] = session
        return session

    def get_session(self, session_id: str) -> CodingSession:
        return self._sessions[session_id]

    def list_sessions(self) -> list[CodingSession]:
        return list(self._sessions.values())

    def register_language_support(self, support: "ProgrammingLanguageSupport") -> None:
        for language in support.get_supported_languages():
            self._registry.register(language.value, support)

    def get_language_support(self, language: "ProgrammingLanguage") -> "ProgrammingLanguageSupport":
        return self._registry.resolve(language.value)
