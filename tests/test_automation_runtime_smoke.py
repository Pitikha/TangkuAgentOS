from __future__ import annotations

from tangku_agentos.automation_runtime import (
    AutomationManager,
    BackgroundTaskManager,
    JobManager,
    SchedulerManager,
    TriggerManager,
)


def main() -> None:
    automation_manager = AutomationManager()
    automation_manager.register_automation("auto-1", "sample automation")
    assert automation_manager.enable("auto-1") is True
    assert automation_manager.disable("auto-1") is True

    job_manager = JobManager()
    job = job_manager.create_job("job-1", "sample job")
    assert job.job_id == "job-1"
    assert job_manager.enqueue(job.job_id) is True

    scheduler = SchedulerManager()
    scheduler.register_schedule("sched-1", "interval", {"every": 5})
    assert scheduler.get_schedule("sched-1") is not None

    trigger_manager = TriggerManager()
    trigger_manager.register_trigger("file", {"source": "workspace"})
    assert trigger_manager.dispatch("file", {"path": "/tmp/example"}) is True

    background_manager = BackgroundTaskManager()
    task = background_manager.create_task("bg-1", "long-running")
    assert task.task_id == "bg-1"
    background_manager.pause(task.task_id)
    background_manager.resume(task.task_id)
    background_manager.cancel(task.task_id)
    print("automation runtime checks passed")


if __name__ == "__main__":
    main()
