"""
Tool Metrics for TangkuAgentOS AI Foundation Framework.

Tracks and analyzes metrics for tool executions.
"""
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
import logging
from datetime import datetime
from .tool_executor import ExecutionResult

logger = logging.getLogger(__name__)


@dataclass
class Metric:
    """Represents a single metric for tool executions."""
    name: str
    value: float
    timestamp: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ToolMetricsResult:
    """Result of a metrics collection operation."""
    tool_name: str
    execution_result: ExecutionResult
    metrics: List[Metric]
    metadata: Dict[str, Any] = field(default_factory=dict)


class ToolMetrics:
    """Tracks and analyzes metrics for tool executions in TangkuAgentOS.

    This class provides methods for collecting and analyzing metrics
    related to tool executions, including latency, success rate, and usage.
    """

    def __init__(self):
        """Initialize the ToolMetrics."""
        self._metrics: Dict[str, List[Metric]] = {}
        self._tool_usage: Dict[str, int] = {}
        logger.info("ToolMetrics initialized.")

    async def collect(
        self,
        tool_name: str,
        execution_result: ExecutionResult,
    ) -> ToolMetricsResult:
        """Collect metrics for a tool execution.

        Args:
            tool_name: The name of the tool.
            execution_result: The ExecutionResult from the tool execution.

        Returns:
            ToolMetricsResult containing the collected metrics.
        """
        metrics = []

        # Latency metric
        latency_metric = Metric(
            name="latency",
            value=execution_result.latency,
            metadata={"tool": tool_name, "success": execution_result.success},
        )
        metrics.append(latency_metric)

        # Success metric
        success_metric = Metric(
            name="success",
            value=1.0 if execution_result.success else 0.0,
            metadata={"tool": tool_name},
        )
        metrics.append(success_metric)

        # Usage metric
        self._tool_usage[tool_name] = self._tool_usage.get(tool_name, 0) + 1
        usage_metric = Metric(
            name="usage",
            value=self._tool_usage[tool_name],
            metadata={"tool": tool_name},
        )
        metrics.append(usage_metric)

        # Record metrics
        for metric in metrics:
            self._record_metric(metric)

        logger.info(f"Collected {len(metrics)} metrics for tool: {tool_name}")
        return ToolMetricsResult(
            tool_name=tool_name,
            execution_result=execution_result,
            metrics=metrics,
            metadata={"timestamp": datetime.utcnow().isoformat()},
        )

    def _record_metric(self, metric: Metric) -> None:
        """Record a single metric.

        Args:
            metric: The metric to record.
        """
        if metric.name not in self._metrics:
            self._metrics[metric.name] = []
        self._metrics[metric.name].append(metric)

    def get_metrics(self, name: str) -> List[Metric]:
        """Retrieve metrics by name.

        Args:
            name: The name of the metric.

        Returns:
            List of metrics with the specified name.
        """
        return self._metrics.get(name, [])

    def get_all_metrics(self) -> Dict[str, List[Metric]]:
        """Retrieve all metrics.

        Returns:
            Dictionary mapping metric names to their values.
        """
        return self._metrics

    def get_tool_stats(self, tool_name: str) -> Dict[str, Any]:
        """Get statistics for a specific tool.

        Args:
            tool_name: The name of the tool.

        Returns:
            Dictionary containing statistics for the tool.
        """
        usage = self._tool_usage.get(tool_name, 0)
        success_metrics = [
            m for m in self._metrics.get("success", [])
            if m.metadata.get("tool") == tool_name
        ]
        success_rate = (
            sum(m.value for m in success_metrics) / len(success_metrics)
            if success_metrics else 0.0
        )
        latency_metrics = [
            m for m in self._metrics.get("latency", [])
            if m.metadata.get("tool") == tool_name
        ]
        avg_latency = (
            sum(m.value for m in latency_metrics) / len(latency_metrics)
            if latency_metrics else 0.0
        )
        return {
            "usage": usage,
            "success_rate": success_rate,
            "avg_latency": avg_latency,
        }

    def get_all_tool_stats(self) -> Dict[str, Dict[str, Any]]:
        """Get statistics for all tools.

        Returns:
            Dictionary mapping tool names to their statistics.
        """
        return {tool: self.get_tool_stats(tool) for tool in self._tool_usage}

    def clear(self) -> None:
        """Clear all metrics and usage data."""
        self._metrics.clear()
        self._tool_usage.clear()
        logger.info("Cleared all tool metrics.")
