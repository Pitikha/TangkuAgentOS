from __future__ import annotations

from .agents import CodingAgent, PlanningAgent, ResearchAgent, SupervisorAgent
from .execution import TaskExecutionEngine


def run_end_to_end_demo(request: str) -> dict[str, Any]:
    from typing import Any

    engine = TaskExecutionEngine()
    plan = engine.create_plan(
        goal=request,
        steps=[
            {"step_id": "plan", "title": "Plan response", "depends_on": []},
            {"step_id": "research", "title": "Gather context", "depends_on": ["plan"]},
            {"step_id": "execute", "title": "Produce response", "depends_on": ["research"]},
        ],
    )

    def runner(step):
        return True, f"handled:{step.step_id}"

    engine.execute_plan(plan, runner=runner)
    supervisor = SupervisorAgent()
    coding_agent = CodingAgent()
    planning_agent = PlanningAgent()
    research_agent = ResearchAgent()

    return {
        "status": "completed",
        "summary": f"Completed {request} using {supervisor.profile.role} orchestration",
        "agents": [coding_agent.profile.role, planning_agent.profile.role, research_agent.profile.role],
        "plan": [step.step_id for step in plan.steps],
    }
