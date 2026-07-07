from __future__ import annotations

from uuid import uuid4

from .interfaces import ModelScheduler
from .models import ModelRequest


class ModelScheduler(ModelScheduler):
    """Concrete model scheduler."""

    def __init__(self) -> None:
        self._schedules: dict[str, tuple[ModelRequest, str]] = {}

    def schedule(self, request: ModelRequest, cron_expression: str) -> str:
        schedule_id = str(uuid4())
        self._schedules[schedule_id] = (request, cron_expression)
        return schedule_id

    def cancel(self, schedule_id: str) -> None:
        self._schedules.pop(schedule_id, None)
