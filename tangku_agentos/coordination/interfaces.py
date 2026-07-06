from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from 


class ProviderSelector(ABC):
    """Interface for provider selection."""

    @abstractmethod
    def select(self, request: ModelRequest) -> str:
        ...


class MultiModelCoordinator(ABC):
    """Interface for multi-model execution coordination."""

    @abstractmethod
    def coordinate(self, requests: list[ModelRequest]) -> list[ModelResponse]:
        ...


class ResultAggregator(ABC):
    """Interface for aggregating results from multiple models."""

    @abstractmethod
    def aggregate(self, results: list[ModelResponse]) -> ModelResponse:
        ...


class ProviderVerifier(ABC):
    """Interface for verification across providers."""

    @abstractmethod
    def verify(self, responses: list[ModelResponse]) -> bool:
        ...


class CostOptimizer(ABC):
    """Interface for cost optimization."""

    @abstractmethod
    def optimize(self, requests: list[ModelRequest]) -> list[ModelRequest]:
        ...


class LatencyOptimizer(ABC):
    """Interface for latency optimization."""

    @abstractmethod
    def optimize(self, requests: list[ModelRequest]) -> list[ModelRequest]:
        ...


class ReliabilityOptimizer(ABC):
    """Interface for reliability optimization."""

    @abstractmethod
    def optimize(self, responses: list[ModelResponse]) -> list[ModelResponse]:
        ...
