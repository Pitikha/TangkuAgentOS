from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class SoftwareEngineeringIntelligenceManager(ABC):
    @abstractmethod
    def evaluate_project(self, repository_id: str, context: dict[str, Any]) -> dict[str, Any]:
        ...


class RefactoringPlanner(ABC):
    @abstractmethod
    def plan_refactor(self, repository_id: str) -> dict[str, Any]:
        ...


class BugInvestigationManager(ABC):
    @abstractmethod
    def investigate_bug(self, repository_id: str, bug_id: str) -> dict[str, Any]:
        ...


class TechnicalDebtAnalyzer(ABC):
    @abstractmethod
    def analyze_debt(self, repository_id: str) -> dict[str, Any]:
        ...


class DependencyRiskAnalyzer(ABC):
    @abstractmethod
    def assess_risk(self, repository_id: str) -> dict[str, Any]:
        ...


class SecurityReviewManager(ABC):
    @abstractmethod
    def review_security(self, repository_id: str) -> dict[str, Any]:
        ...


class PerformanceReviewManager(ABC):
    @abstractmethod
    def review_performance(self, repository_id: str) -> dict[str, Any]:
        ...


class ArchitectureRecommendationManager(ABC):
    @abstractmethod
    def recommend_architecture(self, repository_id: str) -> dict[str, Any]:
        ...
