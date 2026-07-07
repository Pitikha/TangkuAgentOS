from __future__ import annotations

from threading import RLock


class GoalRegistry:
    def __init__(self) -> None:
        self._goals: dict[str, dict] = {}
        self._lock = RLock()

    def register(self, goal_id: str, data: dict) -> None:
        with self._lock:
            self._goals[goal_id] = data

    def get(self, goal_id: str) -> dict | None:
        with self._lock:
            return self._goals.get(goal_id)
