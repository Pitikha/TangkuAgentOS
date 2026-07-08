"""
Retry Strategy and Logic for Task Execution

Implements exponential backoff, jitter, and retry policies.
"""

from typing import Optional, Callable, Any
from dataclasses import dataclass
from datetime import timedelta
import random
import logging

logger = logging.getLogger(__name__)


@dataclass
class RetryPolicy:
    """Configuration for task retry behavior."""
    max_retries: int = 3
    initial_delay: timedelta = None
    max_delay: timedelta = None
    exponential_base: float = 2.0
    use_jitter: bool = True
    jitter_factor: float = 0.1  # 10% jitter

    def __post_init__(self):
        if self.initial_delay is None:
            self.initial_delay = timedelta(seconds=5)
        if self.max_delay is None:
            self.max_delay = timedelta(minutes=5)


class RetryStrategy:
    """
    Implements retry strategies for failed tasks.
    """

    def __init__(self, policy: Optional[RetryPolicy] = None):
        self.policy = policy or RetryPolicy()

    def get_retry_delay(
        self,
        retry_count: int,
    ) -> timedelta:
        """
        Calculate delay before next retry using exponential backoff.

        Args:
            retry_count: Number of retries attempted so far (0-indexed)

        Returns:
            Timedelta for delay before retry
        """
        base_seconds = self.policy.initial_delay.total_seconds()
        delay_seconds = base_seconds * (
            self.policy.exponential_base ** retry_count
        )

        # Cap at max delay
        max_seconds = self.policy.max_delay.total_seconds()
        delay_seconds = min(delay_seconds, max_seconds)

        # Add jitter
        if self.policy.use_jitter:
            jitter = delay_seconds * self.policy.jitter_factor
            delay_seconds += random.uniform(-jitter, jitter)
            delay_seconds = max(delay_seconds, 0)  # Ensure non-negative

        return timedelta(seconds=delay_seconds)

    def should_retry(self, retry_count: int) -> bool:
        """Check if task should be retried."""
        return retry_count < self.policy.max_retries

    def calculate_backoff_schedule(
        self, max_retries: int
    ) -> list[timedelta]:
        """Generate backoff schedule for all retries."""
        schedule = []
        for i in range(max_retries):
            schedule.append(self.get_retry_delay(i))
        return schedule


class CircuitBreaker:
    """
    Circuit breaker pattern for preventing cascading failures.

    States:
    - CLOSED: Normal operation
    - OPEN: Rejecting requests
    - HALF_OPEN: Testing if service recovered
    """

    def __init__(
        self,
        failure_threshold: int = 5,
        success_threshold: int = 2,
        timeout: timedelta = None,
    ):
        self.failure_threshold = failure_threshold
        self.success_threshold = success_threshold
        self.timeout = timeout or timedelta(seconds=60)

        self.state = "CLOSED"
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time: Optional[float] = None

    def record_success(self) -> None:
        """Record successful call."""
        self.failure_count = 0

        if self.state == "HALF_OPEN":
            self.success_count += 1
            if self.success_count >= self.success_threshold:
                self.state = "CLOSED"
                self.success_count = 0
                logger.info("Circuit breaker CLOSED")

    def record_failure(self) -> None:
        """Record failed call."""
        self.failure_count += 1
        self.last_failure_time = datetime.utcnow().timestamp()

        if self.failure_count >= self.failure_threshold:
            if self.state != "OPEN":
                self.state = "OPEN"
                logger.warning("Circuit breaker OPEN")

    def call_allowed(self) -> bool:
        """Check if call is allowed by circuit breaker."""
        if self.state == "CLOSED":
            return True

        if self.state == "OPEN":
            # Check if timeout has elapsed
            if self.last_failure_time:
                elapsed = (
                    datetime.utcnow().timestamp() - self.last_failure_time
                )
                if elapsed > self.timeout.total_seconds():
                    self.state = "HALF_OPEN"
                    self.success_count = 0
                    logger.info("Circuit breaker HALF_OPEN")
                    return True
            return False

        # HALF_OPEN
        return True

    def get_state(self) -> str:
        """Get current circuit breaker state."""
        return self.state


class FallbackStrategy:
    """
    Fallback strategy for handling failures.
    """

    def __init__(self):
        self.fallbacks: dict[str, Callable] = {}

    def register_fallback(
        self,
        operation_id: str,
        fallback_func: Callable[..., Any],
    ) -> None:
        """Register fallback for an operation."""
        self.fallbacks[operation_id] = fallback_func
        logger.info(f"Fallback registered for {operation_id}")

    def has_fallback(self, operation_id: str) -> bool:
        """Check if fallback exists."""
        return operation_id in self.fallbacks

    def execute_fallback(
        self,
        operation_id: str,
        *args,
        **kwargs,
    ) -> Any:
        """Execute fallback for operation."""
        fallback = self.fallbacks.get(operation_id)
        if fallback:
            try:
                result = fallback(*args, **kwargs)
                logger.info(f"Fallback executed for {operation_id}")
                return result
            except Exception as e:
                logger.error(f"Fallback failed for {operation_id}: {e}")
                raise

        raise ValueError(f"No fallback registered for {operation_id}")


# Import datetime for CircuitBreaker
from datetime import datetime
