"""
Reasoning Metrics for TangkuAgentOS AI Foundation Framework.

Tracks and analyzes metrics for reasoning operations.
"""
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
import logging
from datetime import datetime
from .reasoning_engine import ReasoningResult, ReasoningTask

logger = logging.getLogger(__name__)


@dataclass
class Metric:
    name: str
    value: float
    timestamp: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class MetricsResult:
    reasoning_result: ReasoningResult
    metrics: List[Metric]
    metadata: Dict[str, Any] = field(default_factory=dict)


class ReasoningMetrics:
    def __init__(self):
        self._metrics: Dict[str, List[Metric]] = {}
        logger.info("ReasoningMetrics initialized.")

    async def collect(self, reasoning_result: ReasoningResult) -> MetricsResult:
        metrics = []
        latency_metric = Metric(
            name="latency",
            value=0.5,
            metadata={"task": reasoning_result.task.value},
        )
        metrics.append(latency_metric)
        confidence_metric = Metric(
            name="confidence",
            value=reasoning_result.confidence,
            metadata={"task": reasoning_result.task.value},
        )
        metrics.append(confidence_metric)
        quality_metric = Metric(
            name="quality",
            value=0.8,
            metadata={"task": reasoning_result.task.value},
        )
        metrics.append(quality_metric)
        for metric in metrics:
            self._record_metric(metric)
        logger.info(f"Collected {len(metrics)} metrics for reasoning task: {reasoning_result.task.value}")
        return MetricsResult(
            reasoning_result=reasoning_result,
            metrics=metrics,
            metadata={"timestamp": datetime.utcnow().isoformat()},
        )

    def _record_metric(self, metric: Metric) -> None:
        if metric.name not in self._metrics:
            self._metrics[metric.name] = []
        self._metrics[metric.name].append(metric)

    def get_metrics(self, name: str) -> List[Metric]:
        return self._metrics.get(name, [])

    def get_all_metrics(self) -> Dict[str, List[Metric]]:
        return self._metrics

    def get_average(self, name: str) -> Optional[float]:
        metrics = self._metrics.get(name, [])
        if not metrics:
            return None
        return sum(m.value for m in metrics) / len(metrics)

    def clear(self) -> None:
        self._metrics.clear()
        logger.info("Cleared all reasoning metrics.")
