from __future__ import annotations


class GoalLifecycle:
    def __init__(self) -> None:
        self._states: dict[str, str] = {}

    def set_state(self, goal_id: str, state: str) -> None:
        self._states[goal_id] = state

    def get_state(self, goal_id: str) -> str | None:
        return self._states.get(goal_id)
