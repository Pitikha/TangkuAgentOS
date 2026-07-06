from __future__ import annotations

from dataclasses import dataclass


@dataclass
class IntelligenceStatistics:
    total_goals: int = 0
    total_plans: int = 0
    total_tasks: int = 0
    successful_executions: int = 0
    failed_executions: int = 0
