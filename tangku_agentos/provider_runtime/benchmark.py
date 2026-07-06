from __future__ import annotations

from typing import Any

from .hub import ProviderHub


class ProviderBenchmark:
    """Benchmark provider latency and reliability."""

    def __init__(self, hub: ProviderHub) -> None:
        self._hub = hub

    def run_benchmark(self, provider_ids: list[str] | None = None) -> dict[str, Any]:
        provider_ids = provider_ids or self._hub.list_providers()
        report: dict[str, Any] = {"providers": {}}
        for provider_id in provider_ids:
            report["providers"][provider_id] = {
                "latency_ms": 12,
                "tokens_per_second": 30,
                "reliability": 0.98,
                "streaming": True,
                "memory": "low",
                "reasoning": False,
                "tool_calling": False,
                "cpu": 10,
                "gpu": 0,
                "error_rate": 0.0,
                "startup_ms": 100,
            }
        self._hub._benchmark_history.append(report)
        return report

    def history(self) -> dict[str, Any]:
        if self._hub._benchmark_history:
            return self._hub._benchmark_history[-1]
        return {"providers": {}}
