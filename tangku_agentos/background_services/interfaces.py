from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from .models import Job, JobStatus, RetryPolicy


class BackgroundWorkerManager(ABC):
    @abstractmethod
    def register_worker(self, worker_id: str, metadata: dict[str, Any]) -> None:
        ...

    @abstractmethod
    def get_worker_status(self, worker_id: str) -> dict[str, Any]:
        ...


class JobManager(ABC):
    @abstractmethod
    def submit_job(self, job: Job) -> None:
        ...

    @abstractmethod
    def get_job(self, job_id: str) -> Job:
        ...


class QueueManager(ABC):
    @abstractmethod
    def enqueue(self, job_id: str) -> None:
        ...

    @abstractmethod
    def dequeue(self) -> str | None:
        ...


class ResourceScheduler(ABC):
    @abstractmethod
    def allocate_resources(self, job_id: str) -> dict[str, Any]:
        ...

    @abstractmethod
    def release_resources(self, job_id: str) -> None:
        ...


class HealthMonitor(ABC):
    @abstractmethod
    def check_health(self) -> dict[str, Any]:
        ...


class HeartbeatManager(ABC):
    @abstractmethod
    def send_heartbeat(self, worker_id: str) -> None:
        ...

    @abstractmethod
    def monitor_heartbeat(self, worker_id: str) -> bool:
        ...


class CheckpointManager(ABC):
    @abstractmethod
    def checkpoint(self, job_id: str, state: dict[str, Any]) -> None:
        ...

    @abstractmethod
    def restore(self, job_id: str) -> dict[str, Any] | None:
        ...


class RetryPolicy(ABC):
    @abstractmethod
    def should_retry(self, job: Job, attempt: int) -> bool:
        ...

    @abstractmethod
    def retry_delay(self, attempt: int) -> int:
        ...
