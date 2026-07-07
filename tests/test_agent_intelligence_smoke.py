from __future__ import annotations

from tangku_agentos.agent_intelligence import (
    AdaptationManager,
    AgentCoordinator,
    AgentManager,
    AgentMessageBus,
    AgentRegistry,
    AgentRouter,
    CollaborationPolicyManager,
    DecisionCoordinator,
    GoalMonitor,
    ProgressMonitor,
    ReflectionManager,
    SharedMemoryManager,
    SharedWorkspaceManager,
    TeamManager,
    WorkflowAgent,
)


def test_agent_intelligence_smoke() -> None:
    manager = AgentManager()
    agent = manager.register_agent("coding-agent", capabilities=["coding"], metadata={"role": "coding"})
    assert agent.agent_id == "coding-agent"

    registry = AgentRegistry()
    registry.register(agent)
    assert registry.get("coding-agent") is not None

    coordinator = AgentCoordinator()
    delegated = coordinator.delegate("coding-agent", "planning-agent", {"goal": "design"})
    assert delegated.target_agent_id == "planning-agent"

    router = AgentRouter()
    selected = router.route("planning", [{"agent_id": "planning-agent", "capabilities": ["planning"]}])
    assert selected == "planning-agent"

    message_bus = AgentMessageBus()
    sent = message_bus.send("coding-agent", "planning-agent", {"kind": "task"})
    assert sent.sender_id == "coding-agent"

    memory_manager = SharedMemoryManager()
    memory_manager.store("plan", {"status": "draft"})
    assert memory_manager.retrieve("plan")["status"] == "draft"

    team_manager = TeamManager()
    team = team_manager.create_team("team-1", members=["coding-agent", "planning-agent"])
    assert team.team_id == "team-1"

    policy_manager = CollaborationPolicyManager()
    policy_manager.set_policy("team-1", {"mode": "peer"})
    assert policy_manager.get_policy("team-1")["mode"] == "peer"

    goal_monitor = GoalMonitor()
    goal_monitor.track("goal-1", "draft")
    assert goal_monitor.get_status("goal-1") == "draft"

    progress_monitor = ProgressMonitor()
    progress_monitor.update("goal-1", 0.5)
    assert progress_monitor.get_progress("goal-1") == 0.5

    decision_coordinator = DecisionCoordinator()
    decision = decision_coordinator.decide("goal-1", {"signal": "ready"})
    assert decision["decision"] == "proceed"

    reflection_manager = ReflectionManager()
    reflection_manager.record("goal-1", "review")
    assert reflection_manager.get_history("goal-1")[-1] == "review"

    adaptation_manager = AdaptationManager()
    adaptation_manager.record_change("goal-1", "replan")
    assert adaptation_manager.get_changes("goal-1")[-1] == "replan"

    workflow_agent = WorkflowAgent()
    assert workflow_agent.agent_id == "workflow-agent"

    workspace_manager = SharedWorkspaceManager()
    workspace_manager.update("artifact-1", {"kind": "plan"})
    artifact = workspace_manager.get("artifact-1")
    assert artifact is not None and artifact.content["kind"] == "plan"
