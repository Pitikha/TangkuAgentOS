from __future__ import annotations

from threading import RLock
from typing import Any
from uuid import uuid4

from tangku_agentos.core_runtime.event_bus import EventBus
from tangku_agentos.memory_engine import MemoryEntry, MemoryManager, MemoryMetadata, MemoryRecord, MemoryType

from .models import (
    AutomationDefinition,
    AutomationPolicy,
    AutomationSession,
    BackgroundContext,
    BackgroundLifecycle,
    BackgroundTask,
    JobContext,
    JobDefinition,
    JobHistoryEntry,
    JobLifecycle,
    JobSession,
    ScheduleDefinition,
    ScheduleHistoryEntry,
    TriggerDefinition,
)


class AutomationRegistry:
    def __init__(self) -> None:
        self._automations: dict[str, AutomationDefinition] = {}
        self._lock = RLock()

    def register(self, automation_id: str, name: str, enabled: bool = True, version: str = "0.1.0", metadata: dict[str, Any] | None = None) -> AutomationDefinition:
        with self._lock:
            definition = AutomationDefinition(automation_id=automation_id, name=name, enabled=enabled, version=version, metadata=metadata or {})
            self._automations[automation_id] = definition
            return definition

    def get(self, automation_id: str) -> AutomationDefinition | None:
        with self._lock:
            return self._automations.get(automation_id)


class AutomationSessionManager:
    def __init__(self) -> None:
        self._sessions: dict[str, AutomationSession] = {}
        self._lock = RLock()

    def create(self, session_id: str, automation_id: str) -> AutomationSession:
        with self._lock:
            session = AutomationSession(session_id=session_id, automation_id=automation_id, active=True, status="running")
            self._sessions[session_id] = session
            return session


class AutomationContextManager:
    def __init__(self) -> None:
        self._contexts: dict[str, dict[str, Any]] = {}
        self._lock = RLock()

    def get(self, automation_id: str) -> dict[str, Any]:
        with self._lock:
            return dict(self._contexts.setdefault(automation_id, {}))

    def update(self, automation_id: str, updates: dict[str, Any]) -> None:
        with self._lock:
            self._contexts.setdefault(automation_id, {}).update(updates)


class AutomationLifecycleManager:
    def __init__(self) -> None:
        self._states: dict[str, str] = {}
        self._lock = RLock()

    def set_state(self, automation_id: str, state: str) -> None:
        with self._lock:
            self._states[automation_id] = state

    def get_state(self, automation_id: str) -> str | None:
        with self._lock:
            return self._states.get(automation_id)


class AutomationConfigurationManager:
    def __init__(self) -> None:
        self._config: dict[str, Any] = {}

    def set(self, automation_id: str, key: str, value: Any) -> None:
        self._config[(automation_id, key)] = value

    def get(self, automation_id: str, key: str, default: Any = None) -> Any:
        return self._config.get((automation_id, key), default)


class AutomationMetadataManager:
    def __init__(self) -> None:
        self._metadata: dict[str, dict[str, Any]] = {}

    def set(self, automation_id: str, metadata: dict[str, Any]) -> None:
        self._metadata[automation_id] = metadata

    def get(self, automation_id: str) -> dict[str, Any]:
        return dict(self._metadata.get(automation_id, {}))


class AutomationStatisticsManager:
    def __init__(self) -> None:
        self._stats: dict[str, int] = {"registrations": 0, "starts": 0, "stops": 0}

    def record(self, key: str, value: int = 1) -> None:
        self._stats[key] = self._stats.get(key, 0) + value

    def snapshot(self) -> dict[str, int]:
        return dict(self._stats)


class AutomationHealthManager:
    def __init__(self) -> None:
        self._status: dict[str, str] = {}

    def mark(self, automation_id: str, status: str) -> None:
        self._status[automation_id] = status

    def get(self, automation_id: str) -> str | None:
        return self._status.get(automation_id)


class AutomationManager:
    def __init__(self, *, event_bus: EventBus | None = None, security_manager: Any | None = None, observability_manager: Any | None = None) -> None:
        self.registry = AutomationRegistry()
        self.session_manager = AutomationSessionManager()
        self.context_manager = AutomationContextManager()
        self.lifecycle_manager = AutomationLifecycleManager()
        self.configuration_manager = AutomationConfigurationManager()
        self.metadata_manager = AutomationMetadataManager()
        self.statistics_manager = AutomationStatisticsManager()
        self.health_manager = AutomationHealthManager()
        self._policies: dict[str, AutomationPolicy] = {}
        self._jobs: dict[str, JobDefinition] = {}
        self._schedules: dict[str, ScheduleDefinition] = {}
        self._lock = RLock()
        self._event_bus = event_bus or EventBus()
        self._security_manager = security_manager
        self._observability_manager = observability_manager
        self._memory = MemoryManager()

    def register_automation(self, automation_id: str, name: str, enabled: bool = True, version: str = "0.1.0", metadata: dict[str, Any] | None = None) -> AutomationDefinition:
        definition = self.registry.register(automation_id, name, enabled=enabled, version=version, metadata=metadata)
        self.statistics_manager.record("registrations")
        self.lifecycle_manager.set_state(automation_id, "registered")
        self.health_manager.mark(automation_id, "ready")
        self.metadata_manager.set(automation_id, metadata or {})
        return definition

    def enable(self, automation_id: str) -> bool:
        definition = self.registry.get(automation_id)
        if definition is None:
            return False
        self.lifecycle_manager.set_state(automation_id, "enabled")
        self.health_manager.mark(automation_id, "enabled")
        return True

    def disable(self, automation_id: str) -> bool:
        definition = self.registry.get(automation_id)
        if definition is None:
            return False
        self.lifecycle_manager.set_state(automation_id, "disabled")
        self.health_manager.mark(automation_id, "disabled")
        return True

    def set_policy(self, automation_id: str, policy: AutomationPolicy) -> None:
        self._policies[automation_id] = policy

    def get_policy(self, automation_id: str) -> AutomationPolicy | None:
        return self._policies.get(automation_id)

    def create_job(self, job_id: str, name: str, job_type: str = "one_time", parent_job_id: str | None = None, dependencies: list[str] | None = None, metadata: dict[str, Any] | None = None) -> JobDefinition:
        self._ensure_permission("automation.create")
        job = JobDefinition(job_id=job_id, name=name, job_type=job_type, parent_job_id=parent_job_id, dependencies=dependencies or [], metadata=metadata or {})
        self._jobs[job_id] = job
        self._persist_job(job)
        self._emit_event("automation_created", {"job_id": job_id, "name": name})
        return job

    def schedule_job(self, job_id: str, schedule_type: str, config: dict[str, Any] | None = None, metadata: dict[str, Any] | None = None) -> ScheduleDefinition:
        self._ensure_permission("automation.schedule")
        schedule = ScheduleDefinition(schedule_id=f"sched-{job_id}", schedule_type=schedule_type, config=config or {}, metadata=metadata or {})
        self._schedules[schedule.schedule_id] = schedule
        self._persist_schedule(schedule)
        self._emit_event("automation_scheduled", {"job_id": job_id, "schedule_type": schedule_type})
        return schedule

    def execute_job(self, job_id: str) -> dict[str, Any]:
        self._ensure_permission("automation.execute")
        self._emit_event("automation_started", {"job_id": job_id})
        return {"job_id": job_id, "status": "running"}

    def pause_job(self, job_id: str) -> dict[str, Any]:
        self._ensure_permission("automation.update")
        self._emit_event("automation_paused", {"job_id": job_id})
        return {"job_id": job_id, "status": "paused"}

    def resume_job(self, job_id: str) -> dict[str, Any]:
        self._ensure_permission("automation.update")
        self._emit_event("automation_resumed", {"job_id": job_id})
        return {"job_id": job_id, "status": "running"}

    def retry_job(self, job_id: str) -> dict[str, Any]:
        self._ensure_permission("automation.retry")
        self._emit_event("automation_retry", {"job_id": job_id})
        return {"job_id": job_id, "status": "retrying"}

    def cancel_job(self, job_id: str) -> dict[str, Any]:
        self._ensure_permission("automation.update")
        self._emit_event("automation_cancelled", {"job_id": job_id})
        return {"job_id": job_id, "status": "cancelled"}

    def delete_job(self, job_id: str) -> bool:
        self._ensure_permission("automation.delete")
        self._emit_event("automation_deleted", {"job_id": job_id})
        return True

    def list_jobs(self) -> list[JobDefinition]:
        return list(self._jobs.values())

    def list_schedules(self) -> list[ScheduleDefinition]:
        with self._lock:
            return list(self._schedules.values())

    def _persist_job(self, job: JobDefinition) -> None:
        payload = {"job_id": job.job_id, "name": job.name, "job_type": job.job_type, "dependencies": job.dependencies, "metadata": job.metadata}
        metadata = MemoryMetadata(namespace="automation", created_by="AutomationManager", tags=["job", job.job_id])
        record = MemoryRecord(record_id=job.job_id, entries=[MemoryEntry(entry_id=str(uuid4()), type=MemoryType.WORKING, content={"kind": "job", "data": payload}, metadata=metadata)], namespace="automation", metadata=metadata)
        self._memory.store(job.job_id, record)

    def _persist_schedule(self, schedule: ScheduleDefinition) -> None:
        payload = {"schedule_id": schedule.schedule_id, "schedule_type": schedule.schedule_type, "config": schedule.config, "metadata": schedule.metadata}
        metadata = MemoryMetadata(namespace="automation", created_by="AutomationManager", tags=["schedule", schedule.schedule_id])
        record = MemoryRecord(record_id=schedule.schedule_id, entries=[MemoryEntry(entry_id=str(uuid4()), type=MemoryType.WORKING, content={"kind": "schedule", "data": payload}, metadata=metadata)], namespace="automation", metadata=metadata)
        self._memory.store(schedule.schedule_id, record)

    def _emit_event(self, event_name: str, payload: dict[str, Any]) -> None:
        try:
            self._event_bus.publish(event_name, payload)
        except Exception:
            pass
        try:
            if self._observability_manager:
                self._observability_manager.event_recorder.record({"event": event_name, "payload": payload})
        except Exception:
            pass

    def _ensure_permission(self, permission_id: str) -> None:
        try:
            if self._security_manager:
                perm_mgr = self._security_manager.get_permission_manager()
                if not perm_mgr.has_permission("system", permission_id):
                    raise PermissionError(f"Permission denied: {permission_id}")
        except PermissionError:
            raise
        except Exception:
            pass


class JobManager:
    def __init__(self) -> None:
        self._jobs: dict[str, JobDefinition] = {}
        self._history: list[JobHistoryEntry] = []
        self._queue: list[str] = []
        self._sessions: dict[str, JobSession] = {}
        self._contexts: dict[str, JobContext] = {}
        self._lifecycle: dict[str, JobLifecycle] = {}
        self._lock = RLock()

    def create_job(self, job_id: str, name: str, job_type: str = "one_time", parent_job_id: str | None = None, dependencies: list[str] | None = None, metadata: dict[str, Any] | None = None) -> JobDefinition:
        with self._lock:
            job = JobDefinition(job_id=job_id, name=name, job_type=job_type, parent_job_id=parent_job_id, dependencies=dependencies or [], metadata=metadata or {})
            self._jobs[job_id] = job
            self._lifecycle[job_id] = JobLifecycle(state="created")
            self._contexts[job_id] = JobContext(job_id=job_id, payload={}, metadata=metadata or {})
            return job

    def enqueue(self, job_id: str) -> bool:
        with self._lock:
            if job_id not in self._jobs:
                return False
            self._queue.append(job_id)
            self._history.append(JobHistoryEntry(job_id=job_id, status="queued"))
            return True

    def get_job(self, job_id: str) -> JobDefinition | None:
        with self._lock:
            return self._jobs.get(job_id)

    def start_session(self, job_id: str, session_id: str) -> JobSession:
        with self._lock:
            session = JobSession(session_id=session_id, job_id=job_id, status="running")
            self._sessions[session_id] = session
            return session

    def mark_complete(self, job_id: str, message: str = "") -> None:
        with self._lock:
            self._lifecycle[job_id].state = "completed"
            self._history.append(JobHistoryEntry(job_id=job_id, status="completed", message=message))

    def mark_failed(self, job_id: str, message: str = "") -> None:
        with self._lock:
            self._lifecycle[job_id].state = "failed"
            self._lifecycle[job_id].last_error = message
            self._history.append(JobHistoryEntry(job_id=job_id, status="failed", message=message))

    def list_jobs(self) -> list[JobDefinition]:
        with self._lock:
            return list(self._jobs.values())

    def schedule_job(self, job_id: str, schedule_type: str, config: dict[str, Any] | None = None) -> ScheduleDefinition:
        with self._lock:
            schedule = ScheduleDefinition(schedule_id=f"schedule-{job_id}", schedule_type=schedule_type, config=config or {})
            return schedule


class SchedulerManager:
    def __init__(self) -> None:
        self._schedules: dict[str, ScheduleDefinition] = {}
        self._history: list[ScheduleHistoryEntry] = []
        self._lock = RLock()

    def register_schedule(self, schedule_id: str, schedule_type: str, config: dict[str, Any] | None = None, metadata: dict[str, Any] | None = None) -> ScheduleDefinition:
        with self._lock:
            definition = ScheduleDefinition(schedule_id=schedule_id, schedule_type=schedule_type, config=config or {}, metadata=metadata or {})
            self._schedules[schedule_id] = definition
            self._history.append(ScheduleHistoryEntry(schedule_id=schedule_id, status="registered"))
            return definition

    def get_schedule(self, schedule_id: str) -> ScheduleDefinition | None:
        with self._lock:
            return self._schedules.get(schedule_id)


class TriggerManager:
    def __init__(self) -> None:
        self._triggers: dict[str, TriggerDefinition] = {}
        self._lock = RLock()

    def register_trigger(self, trigger_type: str, metadata: dict[str, Any] | None = None, trigger_id: str | None = None) -> TriggerDefinition:
        with self._lock:
            definition = TriggerDefinition(trigger_id=trigger_id or f"trigger-{trigger_type}", trigger_type=trigger_type, source="runtime", metadata=metadata or {})
            self._triggers[definition.trigger_id] = definition
            return definition

    def dispatch(self, trigger_type: str, payload: dict[str, Any]) -> bool:
        with self._lock:
            return any(trigger.trigger_type == trigger_type for trigger in self._triggers.values())


class BackgroundTaskManager:
    def __init__(self) -> None:
        self._tasks: dict[str, BackgroundTask] = {}
        self._contexts: dict[str, BackgroundContext] = {}
        self._lifecycle: dict[str, BackgroundLifecycle] = {}
        self._lock = RLock()

    def create_task(self, task_id: str, name: str) -> BackgroundTask:
        with self._lock:
            task = BackgroundTask(task_id=task_id, name=name)
            self._tasks[task_id] = task
            self._contexts[task_id] = BackgroundContext(task_id=task_id)
            self._lifecycle[task_id] = BackgroundLifecycle(state="created")
            return task

    def pause(self, task_id: str) -> None:
        with self._lock:
            self._lifecycle[task_id].state = "paused"

    def resume(self, task_id: str) -> None:
        with self._lock:
            self._lifecycle[task_id].state = "running"

    def cancel(self, task_id: str) -> None:
        with self._lock:
            self._lifecycle[task_id].state = "cancelled"

    def retry(self, task_id: str) -> None:
        with self._lock:
            self._lifecycle[task_id].retry_count += 1
            self._lifecycle[task_id].state = "retrying"

    def checkpoint(self, task_id: str, checkpoint: dict[str, Any]) -> None:
        with self._lock:
            self._lifecycle[task_id].checkpoint = checkpoint

    def progress(self, task_id: str, progress: int) -> None:
        with self._lock:
            self._tasks[task_id].progress = progress


__all__ = [
    "AutomationConfigurationManager",
    "AutomationContextManager",
    "AutomationHealthManager",
    "AutomationLifecycleManager",
    "AutomationManager",
    "AutomationMetadataManager",
    "AutomationRegistry",
    "AutomationSessionManager",
    "AutomationStatisticsManager",
    "BackgroundTaskManager",
    "JobManager",
    "SchedulerManager",
    "TriggerManager",
]
