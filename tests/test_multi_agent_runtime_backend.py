from __future__ import annotations

from tangku_agentos.agent_framework import CodingAgent, PlanningAgent
from tangku_agentos.agent_intelligence import AgentManager, AgentMessageBus, AgentScheduler
from tangku_agentos.coordination.runtime import MultiAgentManager


def test_multi_agent_runtime_supports_collaboration_and_execution() -> None:
    runtime = MultiAgentManager()
    coding_agent = CodingAgent()
    planning_agent = PlanningAgent()

    runtime.register_agent(coding_agent, group_id="team")
    runtime.register_agent(planning_agent, group_id="team")

    session = runtime.create_session("session-1", participants=[coding_agent.descriptor.agent_id, planning_agent.descriptor.agent_id])
    assert session.session_id == "session-1"

    message = runtime.send_message(coding_agent.descriptor.agent_id, planning_agent.descriptor.agent_id, {"kind": "handoff"})
    assert message.recipient_id == planning_agent.descriptor.agent_id

    delegation = runtime.delegate_task(coding_agent.descriptor.agent_id, planning_agent.descriptor.agent_id, {"goal": "design"})
    assert delegation.delegation_type == "task"

    shared_context = runtime.share_context("shared-team", {"status": "ready"})
    assert shared_context["shared"] is True

    shared_memory = runtime.share_memory("plan", {"status": "draft"})
    assert shared_memory["status"] == "draft"

    plan_id = runtime.create_plan("Ship a prototype", agent_id=coding_agent.descriptor.agent_id)
    assert plan_id

    reasoning_session = runtime.create_reasoning_session("reasoning-1", agent_id=coding_agent.descriptor.agent_id)
    assert reasoning_session.session_id

    scheduled = runtime.schedule_task("task-1", priority=10, dependencies=[], retries=1, timeout=15)
    assert scheduled["task_id"] == "task-1"

    result = runtime.execute_parallel([coding_agent.descriptor.agent_id, planning_agent.descriptor.agent_id], {"mode": "parallel"})
    assert result["status"] == "completed"

    runtime.pause_agent(coding_agent.descriptor.agent_id)
    runtime.resume_agent(coding_agent.descriptor.agent_id)
    runtime.stop_agent(coding_agent.descriptor.agent_id)
    runtime.restart_agent(coding_agent.descriptor.agent_id)

    assert runtime.get_agent_state(coding_agent.descriptor.agent_id) == "running"


def test_runtime_metrics_and_recovery_surface_coordination_state() -> None:
    runtime = MultiAgentManager()
    coding_agent = CodingAgent()

    runtime.register_agent(coding_agent)
    runtime.send_message(coding_agent.descriptor.agent_id, coding_agent.descriptor.agent_id, {"kind": "ping"})
    runtime.schedule_task("task-2", priority=3)

    metrics = runtime.get_runtime_metrics()
    assert metrics["agent_count"] == 1
    assert metrics["messages"]["messages"] >= 1
    assert metrics["scheduler"]["pending"]

    recovered = runtime.recover()
    assert recovered["status"] == "recovered"
