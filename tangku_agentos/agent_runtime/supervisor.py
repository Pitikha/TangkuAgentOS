"""
TangkuAgentOS Agent Runtime - Agent Supervisor and Recovery Manager

This module provides:
- AgentSupervisor: Monitors agent health and status
- AgentRecoveryManager: Handles recovery of failed agents

The supervisor and recovery manager work together to ensure agents
remain healthy and are recovered when they fail.

Author: TangkuAgentOS Team
License: MIT
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum, auto
from typing import (
    Any,
    Callable,
    Dict,
    List,
    Optional,
    Set,
    Tuple,
    Union,
    TYPE_CHECKING,
)

if TYPE_CHECKING:
    from tangku_agentos.agent_runtime.types import (
        AgentID,
        TaskID,
        AgentLifecycleState,
        HealthStatus,
        RecoveryType,
    )
    from tangku_agentos.agent_runtime.core import Agent
    from tangku_agentos.agent_runtime.manager import AgentManager, AgentRegistry
    from tangku_agentos.agent_runtime.lifecycle import AgentLifecycleManager
    from tangku_agentos.runtime_communication import EventBus

logger = logging.getLogger(__name__)


# =============================================================================
# HEALTH CHECK
# =============================================================================

@dataclass
class HealthCheck:
    """
    Definition of a health check for an agent.
    
    Attributes:
        name: Name of the health check.
        description: Description of the health check.
        check_func: Function to perform the health check.
        interval: Interval between checks in seconds.
        timeout: Timeout for the health check in seconds.
        critical: Whether this is a critical health check.
    """

    name: str
    description: str = ""
    check_func: Callable[["AgentID"], Any]
    interval: float = 60.0
    timeout: float = 10.0
    critical: bool = False


@dataclass
class HealthCheckResult:
    """
    Result of a health check.
    
    Attributes:
        agent_id: ID of the agent.
        check_name: Name of the health check.
        status: Health status.
        message: Status message.
        passed: Whether the check passed.
        timestamp: When the check was performed.
        duration: Duration of the check in seconds.
        details: Additional details.
    """

    agent_id: "AgentID"
    check_name: str
    status: "HealthStatus"
    message: str
    passed: bool
    timestamp: datetime = field(default_factory=datetime.utcnow)
    duration: float = 0.0
    details: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "agent_id": self.agent_id,
            "check_name": self.check_name,
            "status": self.status.value if hasattr(self.status, 'value') else str(self.status),
            "message": self.message,
            "passed": self.passed,
            "timestamp": self.timestamp.isoformat(),
            "duration": self.duration,
            "details": self.details,
        }


@dataclass
class AgentHealth:
    """
    Health status of an agent.
    
    Attributes:
        agent_id: ID of the agent.
        status: Overall health status.
        checks: Results of individual health checks.
        last_checked: When the agent was last checked.
        last_failed: When the agent last failed a check.
        failure_count: Number of consecutive failures.
        recovery_attempts: Number of recovery attempts.
    """

    agent_id: "AgentID"
    status: "HealthStatus" = HealthStatus.HEALTHY
    checks: Dict[str, HealthCheckResult] = field(default_factory=dict)
    last_checked: Optional[datetime] = None
    last_failed: Optional[datetime] = None
    failure_count: int = 0
    recovery_attempts: int = 0

    def is_healthy(self) -> bool:
        """Check if the agent is healthy."""
        return self.status == HealthStatus.HEALTHY

    def is_degraded(self) -> bool:
        """Check if the agent is degraded."""
        return self.status == HealthStatus.DEGRADED

    def is_unhealthy(self) -> bool:
        """Check if the agent is unhealthy."""
        return self.status in {HealthStatus.UNHEALTHY, HealthStatus.CRITICAL}

    def is_critical(self) -> bool:
        """Check if the agent is in critical condition."""
        return self.status == HealthStatus.CRITICAL

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "agent_id": self.agent_id,
            "status": self.status.value if hasattr(self.status, 'value') else str(self.status),
            "checks": {name: check.to_dict() for name, check in self.checks.items()},
            "last_checked": self.last_checked.isoformat() if self.last_checked else None,
            "last_failed": self.last_failed.isoformat() if self.last_failed else None,
            "failure_count": self.failure_count,
            "recovery_attempts": self.recovery_attempts,
        }


# =============================================================================
# AGENT SUPERVISOR
# =============================================================================

class AgentSupervisor:
    """
    Supervisor for monitoring agent health and status.
    
    This class provides:
    - Health check execution
    - Health status monitoring
    - Agent status tracking
    - Alerting for unhealthy agents
    - Integration with the lifecycle manager
    
    Thread Safety:
        This class is thread-safe for concurrent access.
    
    Example:
        >>> from tangku_agentos.agent_runtime.supervisor import AgentSupervisor
        >>> 
        >>> supervisor = AgentSupervisor()
        >>> 
        >>> # Register a health check
        >>> supervisor.register_check(
        ...     name="liveness",
        ...     check_func=check_liveness,
        ...     interval=30.0
        ... )
        >>> 
        >>> # Start monitoring
        >>> await supervisor.start()
    """

    def __init__(
        self,
        registry: Optional["AgentRegistry"] = None,
        lifecycle_manager: Optional["AgentLifecycleManager"] = None,
        event_bus: Optional["EventBus"] = None,
        check_interval: float = 60.0,
        enable_alerts: bool = True,
    ):
        """
        Initialize the supervisor.
        
        Args:
            registry: Agent registry for agent information.
            lifecycle_manager: Lifecycle manager for state tracking.
            event_bus: Event bus for publishing health events.
            check_interval: Default interval between health checks.
            enable_alerts: Whether to enable health alerts.
        """
        self._registry = registry
        self._lifecycle_manager = lifecycle_manager
        self._event_bus = event_bus
        self._check_interval = check_interval
        self._enable_alerts = enable_alerts

        # Health checks
        self._checks: Dict[str, HealthCheck] = {}
        self._agent_health: Dict["AgentID", AgentHealth] = {}

        # Monitoring
        self._monitoring_task: Optional[asyncio.Task] = None
        self._running = False

        # Alerts
        self._on_alert: List[Callable[[AgentHealth], None]] = []
        self._on_healthy: List[Callable[[AgentHealth], None]] = []
        self._on_degraded: List[Callable[[AgentHealth], None]] = []
        self._on_unhealthy: List[Callable[[AgentHealth], None]] = []
        self._on_critical: List[Callable[[AgentHealth], None]] = []

        # Metrics
        self._metrics: Dict[str, Any] = {
            "health_checks": 0,
            "health_checks_passed": 0,
            "health_checks_failed": 0,
            "agents_healthy": 0,
            "agents_degraded": 0,
            "agents_unhealthy": 0,
            "agents_critical": 0,
            "alerts_triggered": 0,
        }

        logger.info(
            f"AgentSupervisor initialized (check_interval={check_interval}, "
            f"enable_alerts={enable_alerts})"
        )

    async def start(self) -> None:
        """Start the supervisor."""
        if self._running:
            return

        self._running = True
        self._monitoring_task = asyncio.create_task(self._monitoring_loop())
        logger.info("AgentSupervisor started")

    async def stop(self) -> None:
        """Stop the supervisor."""
        if not self._running:
            return

        self._running = False
        if self._monitoring_task:
            self._monitoring_task.cancel()
            try:
                await self._monitoring_task
            except asyncio.CancelledError:
                pass

        logger.info("AgentSupervisor stopped")

    async def _monitoring_loop(self) -> None:
        """Main monitoring loop."""
        while self._running:
            try:
                # Run health checks for all agents
                if self._registry:
                    for agent_info in self._registry.list_all():
                        await self._check_agent_health(agent_info.agent_id)

                # Wait for next check
                await asyncio.sleep(self._check_interval)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(5.0)

    async def _check_agent_health(self, agent_id: "AgentID") -> None:
        """
        Check the health of an agent.
        
        Args:
            agent_id: ID of the agent to check.
        """
        # Initialize health if not exists
        if agent_id not in self._agent_health:
            self._agent_health[agent_id] = AgentHealth(agent_id=agent_id)

        health = self._agent_health[agent_id]
        old_status = health.status

        # Run all registered health checks
        for check_name, check in self._checks.items():
            try:
                start_time = datetime.utcnow()
                result = await asyncio.wait_for(
                    check.check_func(agent_id),
                    timeout=check.timeout,
                )
                duration = (datetime.utcnow() - start_time).total_seconds()

                # Determine if check passed
                passed = True
                status = HealthStatus.HEALTHY
                message = "Check passed"
                details = {}

                if isinstance(result, bool):
                    passed = result
                    if not passed:
                        status = HealthStatus.UNHEALTHY
                        message = "Check failed"
                elif isinstance(result, HealthCheckResult):
                    passed = result.passed
                    status = result.status
                    message = result.message
                    details = result.details
                elif isinstance(result, dict):
                    passed = result.get("passed", True)
                    status = HealthStatus[result.get("status", "HEALTHY")]
                    message = result.get("message", "Check passed")
                    details = result.get("details", {})

                # Store check result
                check_result = HealthCheckResult(
                    agent_id=agent_id,
                    check_name=check_name,
                    status=status,
                    message=message,
                    passed=passed,
                    duration=duration,
                    details=details,
                )
                health.checks[check_name] = check_result

                # Update metrics
                self._metrics["health_checks"] += 1
                if passed:
                    self._metrics["health_checks_passed"] += 1
                else:
                    self._metrics["health_checks_failed"] += 1

            except asyncio.TimeoutError:
                check_result = HealthCheckResult(
                    agent_id=agent_id,
                    check_name=check_name,
                    status=HealthStatus.UNHEALTHY,
                    message="Check timed out",
                    passed=False,
                    duration=check.timeout,
                )
                health.checks[check_name] = check_result
                self._metrics["health_checks"] += 1
                self._metrics["health_checks_failed"] += 1

            except Exception as e:
                check_result = HealthCheckResult(
                    agent_id=agent_id,
                    check_name=check_name,
                    status=HealthStatus.UNHEALTHY,
                    message=str(e),
                    passed=False,
                    duration=0.0,
                )
                health.checks[check_name] = check_result
                self._metrics["health_checks"] += 1
                self._metrics["health_checks_failed"] += 1

        # Determine overall health status
        health.last_checked = datetime.utcnow()
        self._update_health_status(health)

        # Check for status change
        if old_status != health.status:
            await self._handle_status_change(agent_id, health, old_status)

    def _update_health_status(self, health: AgentHealth) -> None:
        """
        Update the overall health status based on check results.
        
        Args:
            health: Health to update.
        """
        # Count failed checks
        failed_checks = sum(1 for check in health.checks.values() if not check.passed)
        total_checks = len(health.checks)

        if total_checks == 0:
            health.status = HealthStatus.HEALTHY
            return

        # Determine status based on failed checks
        if failed_checks == 0:
            health.status = HealthStatus.HEALTHY
            health.failure_count = 0
        elif failed_checks < total_checks:
            health.status = HealthStatus.DEGRADED
            health.failure_count += 1
        else:
            # Check if any critical checks failed
            critical_failed = any(
                check.name in self._get_critical_checks() and not check.passed
                for check in health.checks.values()
            )
            if critical_failed:
                health.status = HealthStatus.CRITICAL
            else:
                health.status = HealthStatus.UNHEALTHY
            health.failure_count += 1

        # Update last failed timestamp
        if health.status != HealthStatus.HEALTHY:
            health.last_failed = datetime.utcnow()

    def _get_critical_checks(self) -> Set[str]:
        """Get the names of critical health checks."""
        return {name for name, check in self._checks.items() if check.critical}

    async def _handle_status_change(
        self,
        agent_id: "AgentID",
        health: AgentHealth,
        old_status: "HealthStatus",
    ) -> None:
        """
        Handle a change in health status.
        
        Args:
            agent_id: ID of the agent.
            health: Current health of the agent.
            old_status: Previous health status.
        """
        # Update metrics
        self._metrics["agents_healthy"] = sum(
            1 for h in self._agent_health.values() if h.status == HealthStatus.HEALTHY
        )
        self._metrics["agents_degraded"] = sum(
            1 for h in self._agent_health.values() if h.status == HealthStatus.DEGRADED
        )
        self._metrics["agents_unhealthy"] = sum(
            1 for h in self._agent_health.values()
            if h.status == HealthStatus.UNHEALTHY
        )
        self._metrics["agents_critical"] = sum(
            1 for h in self._agent_health.values() if h.status == HealthStatus.CRITICAL
        )

        # Publish event
        if self._enable_alerts and self._event_bus:
            await self._publish_health_event(agent_id, health, old_status)

        # Call callbacks
        if health.status == HealthStatus.HEALTHY:
            for callback in self._on_healthy:
                try:
                    callback(health)
                except Exception as e:
                    logger.error(f"Error in healthy callback: {e}")
        elif health.status == HealthStatus.DEGRADED:
            for callback in self._on_degraded:
                try:
                    callback(health)
                except Exception as e:
                    logger.error(f"Error in degraded callback: {e}")
        elif health.status == HealthStatus.UNHEALTHY:
            for callback in self._on_unhealthy:
                try:
                    callback(health)
                except Exception as e:
                    logger.error(f"Error in unhealthy callback: {e}")
        elif health.status == HealthStatus.CRITICAL:
            for callback in self._on_critical:
                try:
                    callback(health)
                except Exception as e:
                    logger.error(f"Error in critical callback: {e}")

        # Trigger alert
        if self._enable_alerts and health.status != HealthStatus.HEALTHY:
            self._metrics["alerts_triggered"] += 1
            for callback in self._on_alert:
                try:
                    callback(health)
                except Exception as e:
                    logger.error(f"Error in alert callback: {e}")

        logger.info(
            f"Agent health status changed: {agent_id} "
            f"{old_status.name} -> {health.status.name}"
        )

    async def _publish_health_event(
        self,
        agent_id: "AgentID",
        health: AgentHealth,
        old_status: "HealthStatus",
    ) -> None:
        """
        Publish a health event.
        
        Args:
            agent_id: ID of the agent.
            health: Current health of the agent.
            old_status: Previous health status.
        """
        if not self._event_bus:
            return

        try:
            from tangku_agentos.runtime_communication import Event, MessageType

            event_type = f"agent.health_{health.status.name.lower()}"
            event = Event(
                message_type=MessageType.EVENT,
                sender_id="agent_runtime",
                event_type=event_type,
                payload={
                    "agent_id": agent_id,
                    "status": health.status.name,
                    "old_status": old_status.name,
                    "checks": {name: check.to_dict() for name, check in health.checks.items()},
                    "failure_count": health.failure_count,
                },
                timestamp=datetime.utcnow(),
            )
            await self._event_bus.publish(event)
        except Exception as e:
            logger.error(f"Failed to publish health event: {e}")

    def register_check(self, check: HealthCheck) -> None:
        """
        Register a health check.
        
        Args:
            check: Health check to register.
        """
        self._checks[check.name] = check
        logger.debug(f"Health check registered: {check.name}")

    def unregister_check(self, name: str) -> bool:
        """
        Unregister a health check.
        
        Args:
            name: Name of the health check to unregister.
            
        Returns:
            True if the check was unregistered, False if not found.
        """
        if name in self._checks:
            del self._checks[name]
            logger.debug(f"Health check unregistered: {name}")
            return True
        return False

    def get_health(self, agent_id: "AgentID") -> Optional[AgentHealth]:
        """
        Get the health of an agent.
        
        Args:
            agent_id: ID of the agent.
            
        Returns:
            Health of the agent, or None if not found.
        """
        return self._agent_health.get(agent_id)

    def get_all_health(self) -> Dict["AgentID", AgentHealth]:
        """
        Get the health of all agents.
        
        Returns:
            Dictionary of agent health.
        """
        return self._agent_health.copy()

    def list_healthy(self) -> List["AgentID"]:
        """
        List all healthy agents.
        
        Returns:
            List of agent IDs that are healthy.
        """
        return [
            agent_id for agent_id, health in self._agent_health.items()
            if health.is_healthy()
        ]

    def list_degraded(self) -> List["AgentID"]:
        """
        List all degraded agents.
        
        Returns:
            List of agent IDs that are degraded.
        """
        return [
            agent_id for agent_id, health in self._agent_health.items()
            if health.is_degraded()
        ]

    def list_unhealthy(self) -> List["AgentID"]:
        """
        List all unhealthy agents.
        
        Returns:
            List of agent IDs that are unhealthy.
        """
        return [
            agent_id for agent_id, health in self._agent_health.items()
            if health.is_unhealthy()
        ]

    def list_critical(self) -> List["AgentID"]:
        """
        List all critical agents.
        
        Returns:
            List of agent IDs that are critical.
        """
        return [
            agent_id for agent_id, health in self._agent_health.items()
            if health.is_critical()
        ]

    def on_alert(self, callback: Callable[[AgentHealth], None]) -> None:
        """
        Register a callback for health alerts.
        
        Args:
            callback: Callback function to call when an alert is triggered.
        """
        self._on_alert.append(callback)

    def on_healthy(self, callback: Callable[[AgentHealth], None]) -> None:
        """
        Register a callback for when an agent becomes healthy.
        
        Args:
            callback: Callback function to call when an agent is healthy.
        """
        self._on_healthy.append(callback)

    def on_degraded(self, callback: Callable[[AgentHealth], None]) -> None:
        """
        Register a callback for when an agent becomes degraded.
        
        Args:
            callback: Callback function to call when an agent is degraded.
        """
        self._on_degraded.append(callback)

    def on_unhealthy(self, callback: Callable[[AgentHealth], None]) -> None:
        """
        Register a callback for when an agent becomes unhealthy.
        
        Args:
            callback: Callback function to call when an agent is unhealthy.
        """
        self._on_unhealthy.append(callback)

    def on_critical(self, callback: Callable[[AgentHealth], None]) -> None:
        """
        Register a callback for when an agent becomes critical.
        
        Args:
            callback: Callback function to call when an agent is critical.
        """
        self._on_critical.append(callback)

    def set_event_bus(self, event_bus: "EventBus") -> None:
        """
        Set the event bus for publishing health events.
        
        Args:
            event_bus: Event bus instance.
        """
        self._event_bus = event_bus

    def set_registry(self, registry: "AgentRegistry") -> None:
        """
        Set the agent registry.
        
        Args:
            registry: Agent registry instance.
        """
        self._registry = registry

    def set_lifecycle_manager(self, lifecycle_manager: "AgentLifecycleManager") -> None:
        """
        Set the lifecycle manager.
        
        Args:
            lifecycle_manager: Lifecycle manager instance.
        """
        self._lifecycle_manager = lifecycle_manager

    def get_metrics(self) -> Dict[str, Any]:
        """
        Get supervisor metrics.
        
        Returns:
            Dictionary of metrics.
        """
        return {
            **self._metrics,
            "health_checks": len(self._checks),
            "agents_monitored": len(self._agent_health),
        }

    def clear(self) -> int:
        """
        Clear all health data.
        
        Returns:
            Number of agents cleared.
        """
        count = len(self._agent_health)
        self._agent_health.clear()
        self._metrics = {
            "health_checks": 0,
            "health_checks_passed": 0,
            "health_checks_failed": 0,
            "agents_healthy": 0,
            "agents_degraded": 0,
            "agents_unhealthy": 0,
            "agents_critical": 0,
            "alerts_triggered": 0,
        }
        return count

    def shutdown(self) -> None:
        """Shutdown the supervisor."""
        self._running = False
        if self._monitoring_task:
            self._monitoring_task.cancel()
        self._checks.clear()
        self._agent_health.clear()
        self._on_alert.clear()
        self._on_healthy.clear()
        self._on_degraded.clear()
        self._on_unhealthy.clear()
        self._on_critical.clear()
        self._metrics = {
            "health_checks": 0,
            "health_checks_passed": 0,
            "health_checks_failed": 0,
            "agents_healthy": 0,
            "agents_degraded": 0,
            "agents_unhealthy": 0,
            "agents_critical": 0,
            "alerts_triggered": 0,
        }
        logger.info("AgentSupervisor shutdown complete")

    def __repr__(self) -> str:
        """Return string representation."""
        return (
            f"AgentSupervisor(checks={len(self._checks)}, "
            f"agents={len(self._agent_health)}, "
            f"healthy={sum(1 for h in self._agent_health.values() if h.is_healthy())})"
        )


# =============================================================================
# AGENT RECOVERY MANAGER
# =============================================================================

@dataclass
class RecoveryPolicy:
    """
    Policy for agent recovery.
    
    Attributes:
        recovery_type: Type of recovery to attempt.
        max_attempts: Maximum number of recovery attempts.
        backoff_base: Base delay between attempts in seconds.
        backoff_multiplier: Multiplier for exponential backoff.
        max_backoff: Maximum delay between attempts in seconds.
        conditions: Conditions for when to apply this policy.
    """

    recovery_type: "RecoveryType"
    max_attempts: int = 3
    backoff_base: float = 1.0
    backoff_multiplier: float = 2.0
    max_backoff: float = 60.0
    conditions: Dict[str, Any] = field(default_factory=dict)

    def get_delay(self, attempt: int) -> float:
        """
        Get the delay for a recovery attempt.
        
        Args:
            attempt: Recovery attempt number (0-indexed).
            
        Returns:
            Delay in seconds before the next attempt.
        """
        delay = self.backoff_base * (self.backoff_multiplier ** attempt)
        return min(delay, self.max_backoff)

    def should_apply(self, health: AgentHealth) -> bool:
        """
        Check if this policy should be applied.
        
        Args:
            health: Health of the agent.
            
        Returns:
            True if the policy should be applied, False otherwise.
        """
        # Check conditions
        for key, value in self.conditions.items():
            if key == "status":
                if health.status.name != value:
                    return False
            elif key == "failure_count_min":
                if health.failure_count < value:
                    return False
            elif key == "failure_count_max":
                if health.failure_count > value:
                    return False
            elif key == "recovery_attempts_min":
                if health.recovery_attempts < value:
                    return False
            elif key == "recovery_attempts_max":
                if health.recovery_attempts > value:
                    return False
        return True


class AgentRecoveryManager:
    """
    Manager for recovering failed agents.
    
    This class provides:
    - Automatic recovery of failed agents
    - Multiple recovery strategies
    - Recovery policies
    - Recovery attempt tracking
    - Integration with the supervisor
    
    Thread Safety:
        This class is thread-safe for concurrent access.
    
    Example:
        >>> from tangku_agentos.agent_runtime.supervisor import AgentRecoveryManager
        >>> 
        >>> recovery_manager = AgentRecoveryManager()
        >>> 
        >>> # Add a recovery policy
        >>> recovery_manager.add_policy(
        ...     recovery_type=RecoveryType.RESTART,
        ...     max_attempts=3,
        ...     conditions={"status": "UNHEALTHY"}
        ... )
        >>> 
        >>> # Start recovery monitoring
        >>> await recovery_manager.start()
    """

    def __init__(
        self,
        supervisor: Optional["AgentSupervisor"] = None,
        lifecycle_manager: Optional["AgentLifecycleManager"] = None,
        agent_manager: Optional["AgentManager"] = None,
        check_interval: float = 30.0,
        enable_auto_recovery: bool = True,
    ):
        """
        Initialize the recovery manager.
        
        Args:
            supervisor: Supervisor for health monitoring.
            lifecycle_manager: Lifecycle manager for state tracking.
            agent_manager: Agent manager for agent operations.
            check_interval: Interval between recovery checks.
            enable_auto_recovery: Whether to enable automatic recovery.
        """
        self._supervisor = supervisor
        self._lifecycle_manager = lifecycle_manager
        self._agent_manager = agent_manager
        self._check_interval = check_interval
        self._enable_auto_recovery = enable_auto_recovery

        # Recovery policies
        self._policies: List[RecoveryPolicy] = []

        # Recovery tracking
        self._recovery_attempts: Dict["AgentID", int] = {}
        self._recovery_in_progress: Dict["AgentID", bool] = {}

        # Monitoring
        self._monitoring_task: Optional[asyncio.Task] = None
        self._running = False

        # Callbacks
        self._on_recovery_start: List[Callable[["AgentID", RecoveryType], None]] = []
        self._on_recovery_complete: List[Callable[["AgentID", RecoveryType, bool], None]] = []
        self._on_recovery_fail: List[Callable[["AgentID", RecoveryType, str], None]] = []

        # Metrics
        self._metrics: Dict[str, Any] = {
            "recovery_attempts": 0,
            "recoveries_successful": 0,
            "recoveries_failed": 0,
            "agents_recovered": 0,
            "recovery_timeouts": 0,
        }

        logger.info(
            f"AgentRecoveryManager initialized (check_interval={check_interval}, "
            f"enable_auto_recovery={enable_auto_recovery})"
        )

    async def start(self) -> None:
        """Start the recovery manager."""
        if self._running:
            return

        self._running = True
        self._monitoring_task = asyncio.create_task(self._monitoring_loop())
        logger.info("AgentRecoveryManager started")

    async def stop(self) -> None:
        """Stop the recovery manager."""
        if not self._running:
            return

        self._running = False
        if self._monitoring_task:
            self._monitoring_task.cancel()
            try:
                await self._monitoring_task
            except asyncio.CancelledError:
                pass

        logger.info("AgentRecoveryManager stopped")

    async def _monitoring_loop(self) -> None:
        """Main monitoring loop."""
        while self._running:
            try:
                # Check for agents that need recovery
                if self._supervisor:
                    for agent_id, health in self._supervisor.get_all_health().items():
                        if health.is_unhealthy() and not self._recovery_in_progress.get(agent_id, False):
                            await self._attempt_recovery(agent_id, health)

                # Wait for next check
                await asyncio.sleep(self._check_interval)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in recovery monitoring loop: {e}")
                await asyncio.sleep(5.0)

    async def _attempt_recovery(self, agent_id: "AgentID", health: AgentHealth) -> None:
        """
        Attempt to recover an agent.
        
        Args:
            agent_id: ID of the agent to recover.
            health: Current health of the agent.
        """
        if not self._enable_auto_recovery:
            return

        # Mark recovery as in progress
        self._recovery_in_progress[agent_id] = True

        try:
            # Find applicable recovery policy
            policy = self._get_applicable_policy(health)
            if not policy:
                logger.warning(f"No recovery policy for agent: {agent_id}")
                return

            # Check if we've exceeded max attempts
            current_attempts = self._recovery_attempts.get(agent_id, 0)
            if current_attempts >= policy.max_attempts:
                logger.warning(
                    f"Max recovery attempts reached for agent: {agent_id} "
                    f"({current_attempts}/{policy.max_attempts})"
                )
                return

            # Increment attempt count
            self._recovery_attempts[agent_id] = current_attempts + 1
            self._metrics["recovery_attempts"] += 1

            # Get delay before recovery
            delay = policy.get_delay(current_attempts)
            logger.info(
                f"Attempting recovery for agent: {agent_id} "
                f"(attempt={current_attempts + 1}, type={policy.recovery_type.name}, delay={delay}s)"
            )

            # Wait for delay
            await asyncio.sleep(delay)

            # Call recovery start callbacks
            for callback in self._on_recovery_start:
                try:
                    callback(agent_id, policy.recovery_type)
                except Exception as e:
                    logger.error(f"Error in recovery start callback: {e}")

            # Attempt recovery
            success = await self._execute_recovery(agent_id, policy.recovery_type)

            if success:
                health.recovery_attempts += 1
                self._metrics["recoveries_successful"] += 1
                self._metrics["agents_recovered"] += 1
                logger.info(f"Agent recovered: {agent_id} ({policy.recovery_type.name})")

                # Call recovery complete callbacks
                for callback in self._on_recovery_complete:
                    try:
                        callback(agent_id, policy.recovery_type, True)
                    except Exception as e:
                        logger.error(f"Error in recovery complete callback: {e}")
            else:
                self._metrics["recoveries_failed"] += 1
                logger.warning(f"Agent recovery failed: {agent_id} ({policy.recovery_type.name})")

                # Call recovery fail callbacks
                for callback in self._on_recovery_fail:
                    try:
                        callback(agent_id, policy.recovery_type, "Recovery failed")
                    except Exception as e:
                        logger.error(f"Error in recovery fail callback: {e}")

        except Exception as e:
            logger.error(f"Error during recovery for agent {agent_id}: {e}")
            self._metrics["recovery_timeouts"] += 1

            # Call recovery fail callbacks
            for callback in self._on_recovery_fail:
                try:
                    callback(agent_id, RecoveryType.RESTART, str(e))
                except Exception as e:
                    logger.error(f"Error in recovery fail callback: {e}")

        finally:
            # Mark recovery as complete
            self._recovery_in_progress[agent_id] = False

    def _get_applicable_policy(self, health: AgentHealth) -> Optional[RecoveryPolicy]:
        """
        Get the first applicable recovery policy for an agent's health.
        
        Args:
            health: Health of the agent.
            
        Returns:
            Applicable recovery policy, or None if none found.
        """
        for policy in self._policies:
            if policy.should_apply(health):
                return policy
        return None

    async def _execute_recovery(
        self,
        agent_id: "AgentID",
        recovery_type: "RecoveryType",
    ) -> bool:
        """
        Execute a recovery action.
        
        Args:
            agent_id: ID of the agent to recover.
            recovery_type: Type of recovery to perform.
            
        Returns:
            True if recovery was successful, False otherwise.
        """
        try:
            if recovery_type == RecoveryType.RESTART:
                if self._agent_manager:
                    await self._agent_manager.restart_agent(agent_id)
                    return True
                else:
                    logger.error("AgentManager not configured for restart recovery")
                    return False

            elif recovery_type == RecoveryType.RECREATE:
                if self._agent_manager:
                    # Get agent info
                    agent_info = self._agent_manager.registry.get(agent_id)
                    if agent_info and agent_info.config:
                        # Destroy old agent
                        await self._agent_manager.destroy_agent(agent_id)
                        # Create new agent
                        new_agent_id = await self._agent_manager.create_agent(
                            config=agent_info.config,
                        )
                        # Start new agent
                        await self._agent_manager.start_agent(new_agent_id)
                        return True
                    return False
                else:
                    logger.error("AgentManager not configured for recreate recovery")
                    return False

            elif recovery_type == RecoveryType.RESUME:
                if self._lifecycle_manager:
                    await self._lifecycle_manager.transition(
                        agent_id,
                        LifecycleState.IDLE,
                        reason="recovery_resume",
                    )
                    return True
                else:
                    logger.error("LifecycleManager not configured for resume recovery")
                    return False

            elif recovery_type == RecoveryType.MIGRATE:
                # Migration would require a different runtime
                logger.warning("Migration recovery not yet implemented")
                return False

            elif recovery_type == RecoveryType.ROLLBACK:
                # Rollback would require state persistence
                logger.warning("Rollback recovery not yet implemented")
                return False

            else:
                logger.warning(f"Unknown recovery type: {recovery_type}")
                return False

        except Exception as e:
            logger.error(f"Error executing recovery: {e}")
            return False

    def add_policy(self, policy: RecoveryPolicy) -> None:
        """
        Add a recovery policy.
        
        Args:
            policy: Recovery policy to add.
        """
        self._policies.append(policy)
        logger.debug(f"Recovery policy added: {policy.recovery_type.name}")

    def remove_policy(self, recovery_type: "RecoveryType") -> bool:
        """
        Remove a recovery policy.
        
        Args:
            recovery_type: Type of recovery policy to remove.
            
        Returns:
            True if the policy was removed, False if not found.
        """
        for i, policy in enumerate(self._policies):
            if policy.recovery_type == recovery_type:
                del self._policies[i]
                logger.debug(f"Recovery policy removed: {recovery_type.name}")
                return True
        return False

    def get_policy(self, recovery_type: "RecoveryType") -> Optional[RecoveryPolicy]:
        """
        Get a recovery policy by type.
        
        Args:
            recovery_type: Type of recovery policy to get.
            
        Returns:
            Recovery policy if found, None otherwise.
        """
        for policy in self._policies:
            if policy.recovery_type == recovery_type:
                return policy
        return None

    def get_recovery_attempts(self, agent_id: "AgentID") -> int:
        """
        Get the number of recovery attempts for an agent.
        
        Args:
            agent_id: ID of the agent.
            
        Returns:
            Number of recovery attempts.
        """
        return self._recovery_attempts.get(agent_id, 0)

    def reset_recovery_attempts(self, agent_id: "AgentID") -> None:
        """
        Reset the recovery attempt count for an agent.
        
        Args:
            agent_id: ID of the agent.
        """
        self._recovery_attempts[agent_id] = 0

    def on_recovery_start(
        self,
        callback: Callable[["AgentID", "RecoveryType"], None],
    ) -> None:
        """
        Register a callback for recovery start.
        
        Args:
            callback: Callback function to call when recovery starts.
        """
        self._on_recovery_start.append(callback)

    def on_recovery_complete(
        self,
        callback: Callable[["AgentID", "RecoveryType", bool], None],
    ) -> None:
        """
        Register a callback for recovery completion.
        
        Args:
            callback: Callback function to call when recovery completes.
        """
        self._on_recovery_complete.append(callback)

    def on_recovery_fail(
        self,
        callback: Callable[["AgentID", "RecoveryType", str], None],
    ) -> None:
        """
        Register a callback for recovery failure.
        
        Args:
            callback: Callback function to call when recovery fails.
        """
        self._on_recovery_fail.append(callback)

    def set_supervisor(self, supervisor: "AgentSupervisor") -> None:
        """
        Set the supervisor.
        
        Args:
            supervisor: Supervisor instance.
        """
        self._supervisor = supervisor

    def set_lifecycle_manager(self, lifecycle_manager: "AgentLifecycleManager") -> None:
        """
        Set the lifecycle manager.
        
        Args:
            lifecycle_manager: Lifecycle manager instance.
        """
        self._lifecycle_manager = lifecycle_manager

    def set_agent_manager(self, agent_manager: "AgentManager") -> None:
        """
        Set the agent manager.
        
        Args:
            agent_manager: Agent manager instance.
        """
        self._agent_manager = agent_manager

    def get_metrics(self) -> Dict[str, Any]:
        """
        Get recovery manager metrics.
        
        Returns:
            Dictionary of metrics.
        """
        return {
            **self._metrics,
            "policies": len(self._policies),
            "agents_in_recovery": sum(1 for v in self._recovery_in_progress.values() if v),
            "recovery_attempts": self._recovery_attempts,
        }

    def clear(self) -> int:
        """
        Clear all recovery data.
        
        Returns:
            Number of agents cleared.
        """
        count = len(self._recovery_attempts)
        self._recovery_attempts.clear()
        self._recovery_in_progress.clear()
        self._metrics = {
            "recovery_attempts": 0,
            "recoveries_successful": 0,
            "recoveries_failed": 0,
            "agents_recovered": 0,
            "recovery_timeouts": 0,
        }
        return count

    def shutdown(self) -> None:
        """Shutdown the recovery manager."""
        self._running = False
        if self._monitoring_task:
            self._monitoring_task.cancel()
        self._policies.clear()
        self._recovery_attempts.clear()
        self._recovery_in_progress.clear()
        self._on_recovery_start.clear()
        self._on_recovery_complete.clear()
        self._on_recovery_fail.clear()
        self._metrics = {
            "recovery_attempts": 0,
            "recoveries_successful": 0,
            "recoveries_failed": 0,
            "agents_recovered": 0,
            "recovery_timeouts": 0,
        }
        logger.info("AgentRecoveryManager shutdown complete")

    def __repr__(self) -> str:
        """Return string representation."""
        return (
            f"AgentRecoveryManager(policies={len(self._policies)}, "
            f"agents_in_recovery={sum(1 for v in self._recovery_in_progress.values() if v)})"
        )
