from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Iterable

from .models import (
    CodingConfigurationModel,
    CodingStatisticsModel,
    ProgrammingLanguage,
    ProgrammingLanguageProfile,
)


class CodingManagerInterface(ABC):
    """Interface for coding platform management."""

    @abstractmethod
    def create_session(self, session_id: str, configuration: CodingConfigurationModel) -> "CodingSession":
        ...

    @abstractmethod
    def get_session(self, session_id: str) -> "CodingSession":
        ...

    @abstractmethod
    def list_sessions(self) -> list["CodingSession"]:
        ...

    @abstractmethod
    def register_language_support(self, support: "ProgrammingLanguageSupport") -> None:
        ...

    @abstractmethod
    def get_language_support(self, language: ProgrammingLanguage) -> "ProgrammingLanguageSupport":
        ...


class CodingCoordinator(ABC):
    """Interface for orchestrating coding work."""

    @abstractmethod
    def coordinate(self, session_id: str, tasks: Iterable[str]) -> None:
        ...


class CodingSessionManager(ABC):
    """Interface for managing coding sessions."""

    @abstractmethod
    def start_session(self, session_id: str) -> None:
        ...

    @abstractmethod
    def end_session(self, session_id: str) -> None:
        ...

    @abstractmethod
    def pause_session(self, session_id: str) -> None:
        ...

    @abstractmethod
    def resume_session(self, session_id: str) -> None:
        ...


class CodingRegistryInterface(ABC):
    """Interface for coding platform registry operations."""

    @abstractmethod
    def register(self, key: str, value: Any) -> None:
        ...

    @abstractmethod
    def resolve(self, key: str) -> Any:
        ...

    @abstractmethod
    def list_registered(self) -> list[str]:
        ...


class CodingConfiguration(ABC):
    """Interface for coding configuration."""

    @abstractmethod
    def get_configuration(self) -> CodingConfigurationModel:
        ...

    @abstractmethod
    def set_configuration(self, configuration: CodingConfigurationModel) -> None:
        ...


class CodingStatistics(ABC):
    """Interface for coding statistics."""

    @abstractmethod
    def record_metric(self, metric_name: str, value: Any) -> None:
        ...

    @abstractmethod
    def get_metrics(self) -> CodingStatisticsModel:
        ...


class ProgrammingLanguageSupport(ABC):
    """Interface for programming language support providers."""

    @abstractmethod
    def supports_language(self, language: ProgrammingLanguage) -> bool:
        ...

    @abstractmethod
    def get_supported_languages(self) -> list[ProgrammingLanguage]:
        ...

    @abstractmethod
    def get_profile(self, language: ProgrammingLanguage) -> ProgrammingLanguageProfile:
        ...


class ProgrammingLanguageSupportRegistry(ABC):
    """Interface for programming language support registry."""

    @abstractmethod
    def register_support(self, support: ProgrammingLanguageSupport) -> None:
        ...

    @abstractmethod
    def resolve_support(self, language: ProgrammingLanguage) -> ProgrammingLanguageSupport:
        ...

    @abstractmethod
    def list_supported_languages(self) -> list[ProgrammingLanguage]:
        ...


class CodeAnalyzer(ABC):
    @abstractmethod
    def analyze(self, source_code: str, language: ProgrammingLanguage) -> dict[str, Any]:
        ...


class CodeGenerator(ABC):
    @abstractmethod
    def generate(self, specification: str, language: ProgrammingLanguage) -> str:
        ...


class CodeEditor(ABC):
    @abstractmethod
    def edit(self, file_path: str, changes: dict[str, Any]) -> None:
        ...


class CodeRefactorManager(ABC):
    @abstractmethod
    def plan_refactor(self, scope: str) -> dict[str, Any]:
        ...


class CodeFormatter(ABC):
    @abstractmethod
    def format_code(self, source_code: str, language: ProgrammingLanguage) -> str:
        ...


class CodeReviewer(ABC):
    @abstractmethod
    def review(self, source_code: str, language: ProgrammingLanguage) -> dict[str, Any]:
        ...


class CodeExplainer(ABC):
    @abstractmethod
    def explain(self, source_code: str, language: ProgrammingLanguage) -> str:
        ...


class CodeNavigator(ABC):
    @abstractmethod
    def navigate(self, file_path: str, position: dict[str, int]) -> dict[str, Any]:
        ...


class CodeComparator(ABC):
    @abstractmethod
    def compare(self, source_a: str, source_b: str, language: ProgrammingLanguage) -> dict[str, Any]:
        ...


class CodeValidator(ABC):
    @abstractmethod
    def validate(self, source_code: str, language: ProgrammingLanguage) -> dict[str, Any]:
        ...


class CodeOptimizer(ABC):
    @abstractmethod
    def optimize(self, source_code: str, language: ProgrammingLanguage) -> str:
        ...


class CodeSearchManager(ABC):
    @abstractmethod
    def search(self, query: str, language: ProgrammingLanguage | None = None) -> list[dict[str, Any]]:
        ...
