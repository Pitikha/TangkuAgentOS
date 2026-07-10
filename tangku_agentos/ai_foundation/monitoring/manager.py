"""
AI Foundation Framework - Monitoring Manager

This module provides the MonitoringManager class for collecting and managing
metrics, logs, and monitoring data for the AI Foundation.
"""

from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from typing import Any, Dict, List, Optional, Set, TYPE_CHECKING

if TYPE_CHECKING:
    from tangku_agentos.ai_foundation.core.config import AIConfig
    from tangku_agentos.ai_foundation.core.foundation import AIFoundation

logger = logging.getLogger(__name__)


class MetricType(Enum):
    """Types of metrics."""
    COUNTER = auto()
    GAUGE = auto()
    HISTOGRAM = auto()
    SUMMARY = auto()


@dataclass
class Metric:
    """
    Represents a single metric.
    
    Attributes:
        name: Name of the metric.
        metric_type: Type of the metric.
        description: Description of the metric.
        value: Current value of the metric.
        labels: Labels for the metric.
        timestamp: When the metric was last updated.
    """

    name: str
    metric_type: MetricType = MetricType.COUNTER
    description: str = ""
    value: float = 0.0
    labels: Dict[str, str] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow)

    def increment(self, amount: float = 1.0) -> None:
        """Increment the metric value."""
        self.value += amount
        self.timestamp = datetime.utcnow()

    def set(self, value: float) -> None:
        """Set the metric value."""
        self.value = value
        self.timestamp = datetime.utcnow()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "type": self.metric_type.value,
            "description": self.description,
            "value": self.value,
            "labels": self.labels,
            "timestamp": self.timestamp.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Metric":
        """Create from dictionary."""
        metric_type = MetricType.COUNTER
        if "type" in data and data["type"]:
            try:
                metric_type = MetricType(data["type"])
            except ValueError:
                pass

        return cls(
            name=data.get("name", ""),
            metric_type=metric_type,
            description=data.get("description", ""),
            value=data.get("value", 0.0),
            labels=data.get("labels", {}),
        )


@dataclass
class MonitoringManagerMetrics:
    """Metrics for the monitoring manager itself."""
    metrics_collected: int = 0
    logs_collected: int = 0
    alerts_triggered: int = 0
    errors: int = 0
    last_error: Optional[str] = None
    last_error_time: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "metrics_collected": self.metrics_collected,
            "logs_collected": self.logs_collected,
            "alerts_triggered": self.alerts_triggered,
            "errors": self.errors,
            "last_error": self.last_error,
            "last_error_time": self.last_error_time.isoformat() if self.last_error_time else None,
        }


class MonitoringManager:
    """
    Manager for monitoring AI Foundation operations.
    
    This class collects and manages metrics, logs, and alerts for the
    AI Foundation. It provides comprehensive observability into AI
    operations, performance, and usage.
    
    Thread Safety:
        This class is thread-safe for concurrent access.
    
    Example:
        >>> from tangku_agentos.ai_foundation import MonitoringManager
        >>> 
        >>> # Create manager
        >>> manager = MonitoringManager()
        >>> 
        >>> # Record a metric
        >>> await manager.record_metric("requests", 1, MetricType.COUNTER)
        >>> 
        >>> # Get metrics
        >>> metrics = await manager.get_metrics()
        >>> 
        >>> # Trigger an alert
        >>> await manager.trigger_alert("high_latency", "Latency exceeded threshold")
    """

    def __init__(self, config: "AIConfig", foundation: "AIFoundation"):
        """
        Initialize the monitoring manager.
        
        Args:
            config: AI Foundation configuration.
            foundation: AI Foundation instance.
        """
        self._config = config
        self._foundation = foundation
        self._metrics: Dict[str, Metric] = {}
        self._logs: List[Dict[str, Any]] = []
        self._alerts: List[Dict[str, Any]] = []
        self._metrics_lock = asyncio.Lock()
        self._logs_lock = asyncio.Lock()
        self._alerts_lock = asyncio.Lock()
        self._manager_metrics = MonitoringManagerMetrics()
        self._initialized = False
        self._started = False
        self._cleanup_task: Optional[asyncio.Task] = None
        
        logger.info("MonitoringManager initialized")

    @property
    def config(self) -> "AIConfig":
        """Get the configuration."""
        return self._config

    @property
    def foundation(self) -> "AIFoundation":
        """Get the AI Foundation instance."""
        return self._foundation

    @property
    def metrics(self) -> Dict[str, Metric]:
        """Get all metrics."""
        return self._metrics.copy()

    @property
    def manager_metrics(self) -> MonitoringManagerMetrics:
        """Get the monitoring manager metrics."""
        return self._manager_metrics

    @property
    def is_initialized(self) -> bool:
        """Check if the manager is initialized."""
        return self._initialized

    @property
    def is_started(self) -> bool:
        """Check if the manager is started."""
        return self._started

    async def initialize(self) -> None:
        """
        Initialize the monitoring manager.
        """
        if self._initialized:
            logger.warning("MonitoringManager already initialized")
            return
        
        logger.info("Initializing MonitoringManager...")
        
        # Initialize default metrics
        await self._initialize_default_metrics()
        
        self._initialized = True
        logger.info("MonitoringManager initialized successfully")

    async def start(self) -> None:
        """
        Start the monitoring manager.
        
        This method starts the cleanup task for old logs and metrics.
        """
        if self._started:
            logger.warning("MonitoringManager already started")
            return
        
        if not self._initialized:
            await self.initialize()
        
        logger.info("Starting MonitoringManager...")
        
        # Start cleanup task
        self._cleanup_task = asyncio.create_task(self._cleanup_old_data())
        
        self._started = True
        logger.info("MonitoringManager started successfully")

    async def stop(self) -> None:
        """
        Stop the monitoring manager.
        """
        if not self._started:
            logger.warning("MonitoringManager not started")
            return
        
        logger.info("Stopping MonitoringManager...")
        
        # Cancel cleanup task
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
        
        self._started = False
        logger.info("MonitoringManager stopped successfully")

    async def _initialize_default_metrics(self) -> None:
        """Initialize default metrics."""
        # Request metrics
        await self.record_metric(
            "ai_requests_total",
            0,
            MetricType.COUNTER,
            "Total number of AI requests"
        )
        
        await self.record_metric(
            "ai_requests_successful",
            0,
            MetricType.COUNTER,
            "Number of successful AI requests"
        )
        
        await self.record_metric(
            "ai_requests_failed",
            0,
            MetricType.COUNTER,
            "Number of failed AI requests"
        )
        
        # Token metrics
        await self.record_metric(
            "tokens_input_total",
            0,
            MetricType.COUNTER,
            "Total number of input tokens processed"
        )
        
        await self.record_metric(
            "tokens_output_total",
            0,
            MetricType.COUNTER,
            "Total number of output tokens generated"
        )
        
        # Latency metrics
        await self.record_metric(
            "ai_latency_seconds",
            0,
            MetricType.HISTOGRAM,
            "Latency of AI requests in seconds"
        )
        
        # Cost metrics
        await self.record_metric(
            "ai_cost_total",
            0,
            MetricType.GAUGE,
            "Total cost of AI operations"
        )
        
        # Model metrics
        await self.record_metric(
            "models_used_total",
            0,
            MetricType.COUNTER,
            "Total number of model usages"
        )

    async def _cleanup_old_data(self) -> None:
        """Clean up old logs and metrics periodically."""
        import time
        
        cleanup_interval = 300.0  # 5 minutes
        retention_period = 86400.0  # 24 hours
        
        while True:
            try:
                await asyncio.sleep(cleanup_interval)
                await self._cleanup_old(retention_period)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error during monitoring cleanup: {e}")

    async def _cleanup_old(self, retention_seconds: float) -> None:
        """Clean up old logs and alerts."""
        cutoff = datetime.utcnow() - datetime.timedelta(seconds=retention_seconds)
        
        async with self._logs_lock:
            self._logs = [
                log for log in self._logs
                if datetime.fromisoformat(log.get("timestamp", "")) > cutoff
            ]
        
        async with self._alerts_lock:
            self._alerts = [
                alert for alert in self._alerts
                if datetime.fromisoformat(alert.get("timestamp", "")) > cutoff
            ]

    async def record_metric(
        self,
        name: str,
        value: float,
        metric_type: MetricType = MetricType.COUNTER,
        description: str = "",
        labels: Optional[Dict[str, str]] = None,
    ) -> None:
        """
        Record a metric.
        
        Args:
            name: Name of the metric.
            value: Value of the metric.
            metric_type: Type of the metric.
            description: Description of the metric.
            labels: Optional labels for the metric.
        """
        async with self._metrics_lock:
            if name not in self._metrics:
                self._metrics[name] = Metric(
                    name=name,
                    metric_type=metric_type,
                    description=description,
                    value=0.0,
                    labels=labels or {},
                )
            
            metric = self._metrics[name]
            
            if metric_type == MetricType.COUNTER:
                metric.increment(value)
            else:
                metric.set(value)
            
            self._manager_metrics.metrics_collected += 1

    async def increment_metric(
        self,
        name: str,
        amount: float = 1.0,
    ) -> None:
        """
        Increment a metric.
        
        Args:
            name: Name of the metric.
            amount: Amount to increment by.
        """
        async with self._metrics_lock:
            if name in self._metrics:
                self._metrics[name].increment(amount)
                self._manager_metrics.metrics_collected += 1

    async def set_metric(
        self,
        name: str,
        value: float,
    ) -> None:
        """
        Set a metric value.
        
        Args:
            name: Name of the metric.
            value: Value to set.
        """
        async with self._metrics_lock:
            if name in self._metrics:
                self._metrics[name].set(value)
                self._manager_metrics.metrics_collected += 1

    async def get_metric(self, name: str) -> Optional[Metric]:
        """
        Get a metric by name.
        
        Args:
            name: Name of the metric.
        
        Returns:
            Metric or None if not found.
        """
        async with self._metrics_lock:
            return self._metrics.get(name)

    async def get_metrics(
        self,
        metric_type: Optional[MetricType] = None,
    ) -> Dict[str, Metric]:
        """
        Get all metrics, optionally filtered by type.
        
        Args:
            metric_type: Optional metric type to filter by.
        
        Returns:
            Dictionary of metric name to Metric.
        """
        async with self._metrics_lock:
            if metric_type:
                return {
                    name: metric
                    for name, metric in self._metrics.items()
                    if metric.metric_type == metric_type
                }
            return self._metrics.copy()

    async def delete_metric(self, name: str) -> bool:
        """
        Delete a metric.
        
        Args:
            name: Name of the metric to delete.
        
        Returns:
            True if metric was deleted, False if not found.
        """
        async with self._metrics_lock:
            if name not in self._metrics:
                return False
            
            del self._metrics[name]
            return True

    async def clear_metrics(self) -> None:
        """Clear all metrics."""
        async with self._metrics_lock:
            self._metrics.clear()

    async def log(
        self,
        level: str,
        message: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Log a message.
        
        Args:
            level: Log level (debug, info, warning, error, critical).
            message: Log message.
            context: Optional additional context.
        """
        async with self._logs_lock:
            log_entry = {
                "timestamp": datetime.utcnow().isoformat(),
                "level": level,
                "message": message,
                "context": context or {},
            }
            
            self._logs.append(log_entry)
            self._manager_metrics.logs_collected += 1
            
            # Log to Python logging
            if level == "debug":
                logger.debug(message, extra=context)
            elif level == "info":
                logger.info(message, extra=context)
            elif level == "warning":
                logger.warning(message, extra=context)
            elif level == "error":
                logger.error(message, extra=context)
            elif level == "critical":
                logger.critical(message, extra=context)
            else:
                logger.info(message, extra=context)

    async def get_logs(
        self,
        level: Optional[str] = None,
        limit: Optional[int] = None,
        since: Optional[datetime] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get logs, optionally filtered.
        
        Args:
            level: Optional log level to filter by.
            limit: Optional maximum number of logs to return.
            since: Optional start timestamp to filter by.
        
        Returns:
            List of log entries.
        """
        async with self._logs_lock:
            logs = self._logs.copy()
            
            # Filter by level
            if level:
                logs = [log for log in logs if log.get("level") == level]
            
            # Filter by time
            if since:
                logs = [
                    log for log in logs
                    if datetime.fromisoformat(log.get("timestamp", "")) >= since
                ]
            
            # Limit results
            if limit:
                logs = logs[-limit:]
            
            return logs

    async def trigger_alert(
        self,
        alert_id: str,
        message: str,
        severity: str = "warning",
        context: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Trigger an alert.
        
        Args:
            alert_id: Unique identifier for the alert.
            message: Alert message.
            severity: Alert severity (info, warning, critical).
            context: Optional additional context.
        """
        async with self._alerts_lock:
            alert = {
                "alert_id": alert_id,
                "timestamp": datetime.utcnow().isoformat(),
                "message": message,
                "severity": severity,
                "context": context or {},
                "resolved": False,
            }
            
            self._alerts.append(alert)
            self._manager_metrics.alerts_triggered += 1
            
            # Log the alert
            await self.log(severity, f"ALERT: {message}", {"alert_id": alert_id, **context})

    async def resolve_alert(self, alert_id: str) -> bool:
        """
        Resolve an alert.
        
        Args:
            alert_id: ID of the alert to resolve.
        
        Returns:
            True if alert was resolved, False if not found.
        """
        async with self._alerts_lock:
            for alert in self._alerts:
                if alert.get("alert_id") == alert_id:
                    alert["resolved"] = True
                    alert["resolved_at"] = datetime.utcnow().isoformat()
                    return True
            return False

    async def get_alerts(
        self,
        severity: Optional[str] = None,
        resolved: Optional[bool] = None,
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get alerts, optionally filtered.
        
        Args:
            severity: Optional severity to filter by.
            resolved: Optional resolved status to filter by.
            limit: Optional maximum number of alerts to return.
        
        Returns:
            List of alert entries.
        """
        async with self._alerts_lock:
            alerts = self._alerts.copy()
            
            # Filter by severity
            if severity:
                alerts = [alert for alert in alerts if alert.get("severity") == severity]
            
            # Filter by resolved status
            if resolved is not None:
                alerts = [alert for alert in alerts if alert.get("resolved") == resolved]
            
            # Limit results
            if limit:
                alerts = alerts[-limit:]
            
            return alerts

    async def get_stats(self) -> Dict[str, Any]:
        """
        Get statistics for the monitoring manager.
        
        Returns:
            Dictionary with statistics.
        """
        async with self._metrics_lock:
            stats = {
                "metrics": {name: metric.value for name, metric in self._metrics.items()},
                "logs_count": len(self._logs),
                "alerts_count": len(self._alerts),
                "manager_metrics": self._manager_metrics.to_dict(),
            }
        
        return stats

    async def get_info(self) -> Dict[str, Any]:
        """
        Get information about the monitoring manager.
        
        Returns:
            Dictionary with monitoring manager information.
        """
        return {
            "status": "active" if self._initialized and self._started else "inactive",
            "metrics_count": len(self._metrics),
            "logs_count": len(self._logs),
            "alerts_count": len(self._alerts),
            "manager_metrics": self._manager_metrics.to_dict(),
            "config": {
                "log_requests": self._config.monitoring.log_requests,
                "log_responses": self._config.monitoring.log_responses,
                "log_errors": self._config.monitoring.log_errors,
                "metrics_backends": self._config.monitoring.metrics_backends,
                "alerting_enabled": self._config.monitoring.alerting_enabled,
            }
        }

    async def reset(self) -> None:
        """
        Reset the monitoring manager.
        
        This method clears all metrics, logs, and alerts.
        """
        logger.info("Resetting MonitoringManager...")
        
        async with self._metrics_lock:
            self._metrics.clear()
        
        async with self._logs_lock:
            self._logs.clear()
        
        async with self._alerts_lock:
            self._alerts.clear()
        
        self._manager_metrics = MonitoringManagerMetrics()
        self._initialized = False
        self._started = False
        
        logger.info("MonitoringManager reset successfully")

    def __repr__(self) -> str:
        """Return string representation."""
        return (
            f"MonitoringManager("
            f"initialized={self._initialized}, "
            f"started={self._started}, "
            f"metrics={len(self._metrics)})"
        )
