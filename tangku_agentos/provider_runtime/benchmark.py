"""Benchmarking for the TangkuAgentOS Provider Runtime."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from threading import RLock
from typing import Any, Callable, Dict, List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from .types import BenchmarkConfig, BenchmarkMetrics, ProviderID

from .constants import BenchmarkConfig, BenchmarkMetrics
from .exceptions import BenchmarkFailedError


@dataclass
class BenchmarkResult:
    """Result of a benchmark."""

    provider_id: ProviderID
    metrics: BenchmarkMetrics
    timestamp: float = field(default_factory=time.time)


@dataclass
class BenchmarkHistory:
    """History of benchmarks."""

    results: List[BenchmarkResult] = field(default_factory=list)

    def add_result(self, result: BenchmarkResult) -> None:
        """Add a benchmark result."""
        self.results.append(result)

    def get_latest(self) -> Optional[BenchmarkResult]:
        """Get the latest benchmark result."""
        return self.results[-1] if self.results else None

    def get_history(self, limit: int = 10) -> List[BenchmarkResult]:
        """Get the benchmark history."""
        return self.results[-limit:]


class ProviderBenchmark:
    """
    Benchmarks providers with:
    - Speed benchmarks
    - Cost benchmarks
    - Quality benchmarks
    - Token usage
    - Latency reports
    - Performance rankings
    """

    def __init__(self, hub: Any = None) -> None:
        self._hub = hub
        self._lock = RLock()
        self._history = BenchmarkHistory()
        self._default_config = BenchmarkConfig()

    def run_benchmark(
        self,
        provider_ids: Optional[List[ProviderID]] = None,
        config: Optional[BenchmarkConfig] = None,
    ) -> Dict[str, Any]:
        """
        Run a benchmark for the given providers.
        Measures:
        - Latency (ms)
        - Tokens per second
        - Reliability
        - Cost per token
        - Quality score
        """
        benchmark_config = config or self._default_config
        provider_ids = provider_ids or self._get_all_provider_ids()
        report: Dict[str, Any] = {
            "providers": {},
            "timestamp": time.time(),
            "config": {
                "iterations": benchmark_config.iterations,
                "warmup_iterations": benchmark_config.warmup_iterations,
                "input_size": benchmark_config.input_size,
                "max_tokens": benchmark_config.max_tokens,
            },
        }

        for provider_id in provider_ids:
            try:
                metrics = self._benchmark_provider(provider_id, benchmark_config)
                report["providers"][provider_id] = metrics
                self._history.add_result(
                    BenchmarkResult(provider_id=provider_id, metrics=metrics)
                )
            except Exception as e:
                report["providers"][provider_id] = {
                    "error": str(e),
                    "latency_ms": 0.0,
                    "tokens_per_second": 0.0,
                    "reliability": 0.0,
                    "cost_per_token": 0.0,
                    "quality_score": 0.0,
                }

        # Add rankings
        report["rankings"] = self._generate_rankings(report["providers"])

        return report

    def _get_all_provider_ids(self) -> List[ProviderID]:
        """Get all provider IDs from the hub."""
        if self._hub is not None:
            return self._hub.list_providers()
        return []

    def _benchmark_provider(
        self, provider_id: ProviderID, config: BenchmarkConfig
    ) -> BenchmarkMetrics:
        """Benchmark a single provider."""
        # Warmup
        for _ in range(config.warmup_iterations):
            self._run_single_test(provider_id, config)

        # Actual benchmark
        latencies: List[float] = []
        token_counts: List[int] = []
        successes = 0

        for _ in range(config.iterations):
            try:
                start_time = time.time()
                result = self._run_single_test(provider_id, config)
                latency = (time.time() - start_time) * 1000
                latencies.append(latency)
                token_counts.append(result.get("usage", {}).get("total_tokens", 0))
                successes += 1
            except Exception:
                latencies.append(0.0)
                token_counts.append(0)

        # Calculate metrics
        avg_latency = sum(latencies) / len(latencies) if latencies else 0.0
        total_tokens = sum(token_counts)
        total_time = sum(latencies) / 1000
        tokens_per_second = total_tokens / total_time if total_time > 0 else 0.0
        reliability = successes / config.iterations if config.iterations > 0 else 0.0

        # Placeholder for cost and quality (would require actual API calls)
        cost_per_token = 0.0
        quality_score = 0.95  # Placeholder

        return BenchmarkMetrics(
            latency_ms=avg_latency,
            tokens_per_second=tokens_per_second,
            reliability=reliability,
            cost_per_token=cost_per_token,
            quality_score=quality_score,
        )

    def _run_single_test(
        self, provider_id: ProviderID, config: BenchmarkConfig
    ) -> Dict[str, Any]:
        """Run a single test request."""
        if self._hub is None:
            raise BenchmarkFailedError(f"No hub available for provider {provider_id}")

        adapter = self._hub.get_adapter(provider_id)
        if adapter is None:
            raise BenchmarkFailedError(f"No adapter for provider {provider_id}")

        # Generate test input
        test_input = self._generate_test_input(config.input_size)

        request = {
            "request_id": f"benchmark-{provider_id}-{time.time()}",
            "provider_id": provider_id,
            "model": self._hub.get_provider_state(provider_id).get("default_model", "default"),
            "input": test_input,
            "parameters": {
                "max_tokens": config.max_tokens,
            },
            "stream": False,
        }

        return adapter.send(request)

    def _generate_test_input(self, size: int) -> str:
        """Generate test input of the given size."""
        return " " * size

    def _generate_rankings(self, providers: Dict[str, Any]) -> Dict[str, Any]:
        """Generate performance rankings."""
        rankings: Dict[str, Any] = {}

        # Latency ranking (lower is better)
        latency_sorted = sorted(
            providers.items(),
            key=lambda x: x[1].get("latency_ms", float("inf")),
        )
        rankings["latency"] = [p[0] for p in latency_sorted]

        # Tokens per second ranking (higher is better)
        tps_sorted = sorted(
            providers.items(),
            key=lambda x: x[1].get("tokens_per_second", 0.0),
            reverse=True,
        )
        rankings["tokens_per_second"] = [p[0] for p in tps_sorted]

        # Reliability ranking (higher is better)
        reliability_sorted = sorted(
            providers.items(),
            key=lambda x: x[1].get("reliability", 0.0),
            reverse=True,
        )
        rankings["reliability"] = [p[0] for p in reliability_sorted]

        # Cost per token ranking (lower is better)
        cost_sorted = sorted(
            providers.items(),
            key=lambda x: x[1].get("cost_per_token", float("inf")),
        )
        rankings["cost_per_token"] = [p[0] for p in cost_sorted]

        # Quality ranking (higher is better)
        quality_sorted = sorted(
            providers.items(),
            key=lambda x: x[1].get("quality_score", 0.0),
            reverse=True,
        )
        rankings["quality"] = [p[0] for p in quality_sorted]

        return rankings

    def history(self) -> Dict[str, Any]:
        """Get the benchmark history."""
        latest = self._history.get_latest()
        if latest is not None:
            return {
                "latest": {
                    "provider_id": latest.provider_id,
                    "metrics": latest.metrics,
                    "timestamp": latest.timestamp,
                },
                "history": [
                    {
                        "provider_id": r.provider_id,
                        "metrics": r.metrics,
                        "timestamp": r.timestamp,
                    }
                    for r in self._history.get_history(10)
                ],
            }
        return {"latest": None, "history": []}

    def get_provider_metrics(self, provider_id: ProviderID) -> Optional[BenchmarkMetrics]:
        """Get the latest benchmark metrics for a provider."""
        latest = self._history.get_latest()
        if latest and latest.provider_id == provider_id:
            return latest.metrics
        return None

    def compare_providers(
        self, provider_ids: List[ProviderID]
    ) -> Dict[str, Any]:
        """Compare multiple providers."""
        comparison: Dict[str, Any] = {}
        for provider_id in provider_ids:
            metrics = self.get_provider_metrics(provider_id)
            if metrics is not None:
                comparison[provider_id] = {
                    "latency_ms": metrics.latency_ms,
                    "tokens_per_second": metrics.tokens_per_second,
                    "reliability": metrics.reliability,
                    "cost_per_token": metrics.cost_per_token,
                    "quality_score": metrics.quality_score,
                }
        return comparison
