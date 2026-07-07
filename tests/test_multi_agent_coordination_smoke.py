from __future__ import annotations

from tangku_agentos.agent_framework import CodingAgent, PlanningAgent
from tangku_agentos.coordination.models import CoordinationPolicy
from tangku_agentos.coordination.runtime import MultiAgentManager


def main() -> None:
    manager = MultiAgentManager()

    coding_agent = CodingAgent()
    planning_agent = PlanningAgent()

    manager.register_agent(coding_agent, group_id="team")
    manager.register_agent(planning_agent, group_id="team")

    assert len(manager.discover_agents(group_id="team")) == 2
    manager.start_runtime()

    bus_message = manager.message_bus.direct_message(
        sender_id=coding_agent.descriptor.agent_id,
        recipient_id=planning_agent.descriptor.agent_id,
        payload={"operation": "plan"},
    )
    assert bus_message.recipient_id == planning_agent.descriptor.agent_id

    delegation = manager.delegation_manager.delegate_task(
        source_agent_id=coding_agent.descriptor.agent_id,
        target_agent_id=planning_agent.descriptor.agent_id,
        payload={"goal": "decompose"},
    )
    assert delegation.delegation_type == "task"

    session = manager.collaboration_manager.create_session(
        session_id="session-1",
        participants=[coding_agent.descriptor.agent_id, planning_agent.descriptor.agent_id],
    )
    assert session.session_id == "session-1"

    manager.policy_manager.set_policy("session-1", CoordinationPolicy.LEADER_FOLLOWER)
    assert manager.policy_manager.resolve_policy("session-1") == CoordinationPolicy.LEADER_FOLLOWER

    manager.conflict_manager.record_conflict(
        subject="shared-workspace",
        participants=[coding_agent.descriptor.agent_id, planning_agent.descriptor.agent_id],
        metadata={"reason": "resource"},
    )
    assert len(manager.conflict_manager.history()) == 1

    distribution = manager.distribution_manager.distribute(
        task_id="task-1",
        agents=[coding_agent, planning_agent],
        capabilities=["goal_decomposition"],
        priority=10,
    )
    assert len(distribution) == 2

    print("multi-agent checks passed")


if __name__ == "__main__":
    main()
