"""
Message Infrastructure Monitoring and Metrics
"""

from typing import Dict, Any, List
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import defaultdict
import logging

logger = logging.getLogger(__name__)


@dataclass
class MessageMetric:
    """Metrics for message types."""
    message_type: str = ""
    sent_count: int = 0
    delivered_count: int = 0
    failed_count: int = 0
    expired_count: int = 0
    avg_latency_ms: float = 0.0
    total_latency_ms: float = 0.0
    last_updated: datetime = field(default_factory=datetime.utcnow)


@dataclass
class HandlerMetric:
    """Metrics for message handlers."""
    handler_id: str = ""
    message_type: str = ""
    messages_processed: int = 0
    messages_failed: int = 0
    avg_processing_time_ms: float = 0.0
    total_processing_time_ms: float = 0.0
    last_processed: Optional[datetime] = None


@dataclass
class RoutingMetric:
    """Metrics for message routes."""
    route_id: str = ""
    route_name: str = ""
    messages_routed: int = 0
    avg_routing_time_ms: float = 0.0
    total_routing_time_ms: float = 0.0


class MessageInfrastructureMonitor:
    """
    Comprehensive monitoring for message infrastructure.
    """

    def __init__(self):
        self.message_metrics: Dict[str, MessageMetric] = defaultdict(
            lambda: MessageMetric()
        )
        self.handler_metrics: Dict[str, HandlerMetric] = {}
        self.route_metrics: Dict[str, RoutingMetric] = {}
        self.queue_depth_history: List[Dict[str, Any]] = []
        self.max_history = 1000

    def record_message_sent(
        self, message_type: str, timestamp: datetime = None
    ) -> None:
        """Record sent message."""
        if timestamp is None:
            timestamp = datetime.utcnow()

        metric = self.message_metrics[message_type]
        metric.message_type = message_type
        metric.sent_count += 1
        metric.last_updated = timestamp

    def record_message_delivered(
        self, message_type: str, latency_ms: float, timestamp: datetime = None
    ) -> None:
        """Record delivered message."""
        if timestamp is None:
            timestamp = datetime.utcnow()

        metric = self.message_metrics[message_type]
        metric.message_type = message_type
        metric.delivered_count += 1
        metric.total_latency_ms += latency_ms
        metric.avg_latency_ms = (
            metric.total_latency_ms / metric.delivered_count
        )
        metric.last_updated = timestamp

    def record_message_failed(
        self, message_type: str, timestamp: datetime = None
    ) -> None:
        """Record failed message."""
        if timestamp is None:
            timestamp = datetime.utcnow()

        metric = self.message_metrics[message_type]
        metric.message_type = message_type
        metric.failed_count += 1
        metric.last_updated = timestamp

    def record_message_expired(
        self, message_type: str, timestamp: datetime = None
    ) -> None:
        """Record expired message."""
        if timestamp is None:
            timestamp = datetime.utcnow()

        metric = self.message_metrics[message_type]
        metric.message_type = message_type
        metric.expired_count += 1
        metric.last_updated = timestamp

    def record_handler_processed(
        self,
        handler_id: str,
        message_type: str,
        processing_time_ms: float,
    ) -> None:
        """Record message handler processing."""
        metric = self.handler_metrics.get(
            handler_id,
            HandlerMetric(handler_id=handler_id, message_type=message_type),
        )
        metric.messages_processed += 1
        metric.total_processing_time_ms += processing_time_ms
        metric.avg_processing_time_ms = (
            metric.total_processing_time_ms / metric.messages_processed
        )
        metric.last_processed = datetime.utcnow()
        self.handler_metrics[handler_id] = metric

    def record_handler_error(self, handler_id: str) -> None:
        """Record handler error."""
        metric = self.handler_metrics.get(handler_id)
        if metric:
            metric.messages_failed += 1

    def record_route_traversal(
        self, route_id: str, route_name: str, routing_time_ms: float
    ) -> None:
        """Record route traversal."""
        metric = self.route_metrics.get(
            route_id,
            RoutingMetric(route_id=route_id, route_name=route_name),
        )
        metric.messages_routed += 1
        metric.total_routing_time_ms += routing_time_ms
        metric.avg_routing_time_ms = (
            metric.total_routing_time_ms / metric.messages_routed
        )
        self.route_metrics[route_id] = metric

    def record_queue_depth(self, queue_name: str, depth: int) -> None:
        """Record queue depth over time."""
        record = {
            "timestamp": datetime.utcnow().isoformat(),
            "queue": queue_name,
            "depth": depth,
        }
        self.queue_depth_history.append(record)

        if len(self.queue_depth_history) > self.max_history:
            self.queue_depth_history.pop(0)

    def get_message_metrics(self) -> Dict[str, MessageMetric]:
        """Get all message metrics."""
        return dict(self.message_metrics)

    def get_message_type_summary(self, message_type: str) -> Dict[str, Any]:
        """Get summary for specific message type."""
        metric = self.message_metrics.get(message_type)
        if not metric:
            return {}

        total = metric.sent_count
        success_rate = (
            (metric.delivered_count / total * 100) if total > 0 else 0
        )

        return {
            "message_type": message_type,
            "sent": metric.sent_count,
            "delivered": metric.delivered_count,
            "failed": metric.failed_count,
            "expired": metric.expired_count,
            "success_rate": success_rate,
            "avg_latency_ms": metric.avg_latency_ms,
            "last_updated": metric.last_updated.isoformat(),
        }

    def get_handler_metrics(self) -> Dict[str, HandlerMetric]:
        """Get all handler metrics."""
        return dict(self.handler_metrics)

    def get_route_metrics(self) -> Dict[str, RoutingMetric]:
        """Get all route metrics."""
        return dict(self.route_metrics)

    def get_overall_stats(self) -> Dict[str, Any]:
        """Get overall infrastructure statistics."""
        messages = list(self.message_metrics.values())
        total_sent = sum(m.sent_count for m in messages)
        total_delivered = sum(m.delivered_count for m in messages)
        total_failed = sum(m.failed_count for m in messages)
        total_expired = sum(m.expired_count for m in messages)

        overall_success_rate = (
            (total_delivered / total_sent * 100) if total_sent > 0 else 0
        )

        avg_latency = (
            sum(m.avg_latency_ms for m in messages) / len(messages)
            if messages
            else 0
        )

        return {
            "total_message_types": len(messages),
            "total_sent": total_sent,
            "total_delivered": total_delivered,
            "total_failed": total_failed,
            "total_expired": total_expired,
            "overall_success_rate": overall_success_rate,
            "average_latency_ms": avg_latency,
            "active_handlers": len(self.handler_metrics),
            "active_routes": len(self.route_metrics),
            "timestamp": datetime.utcnow().isoformat(),
        }

    def get_recent_queue_depth(self, queue_name: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Get recent queue depth measurements."""
        return [
            r for r in self.queue_depth_history[-limit:]
            if r["queue"] == queue_name
        ]

    def clear_metrics(self) -> None:
        """Clear all metrics."""
        self.message_metrics.clear()
        self.handler_metrics.clear()
        self.route_metrics.clear()
        self.queue_depth_history.clear()
        logger.info("Message infrastructure metrics cleared")
