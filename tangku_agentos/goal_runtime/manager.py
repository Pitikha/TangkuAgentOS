from __future__ import annotations

from threading import RLock
from uuid import uuid4


class GoalManager:
    def __init__(self) -> None:
        self._goals: dict[str, dict] = {}
        self._lock = RLock()

    def create_goal(self, name: str, metadata: dict | None = None) -> str:
        goal_id = str(uuid4())
        with self._lock:
            self._goals[goal_id] = {"name": name, "metadata": dict(metadata or {})}
        return goal_id

    def get_goal(self, goal_id: str) -> dict | None:
        with self._lock:
            return self._goals.get(goal_id)
