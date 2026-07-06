from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict


class JobStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass(frozen=True)
class Job:
    job_id: str
    worker_id: str
    payload: Dict[str, Any] = field(default_factory=dict)
    status: JobStatus = JobStatus.PENDING
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class RetryPolicy:
    max_attempts: int = 3
    delay_seconds: int = 60
    backoff_factor: float = 2.0
    metadata: Dict[str, Any] = field(default_factory=dict)
