from tangku_agentos.agent_framework import (
    CodingAgent,
    PlanningAgent,
    ResearchAgent,
    SupervisorAgent,
    TaskExecutionEngine,
    run_end_to_end_demo,
)
from tangku_agentos.memory_engine import MemoryIntelligence
from tangku_agentos.plugin_runtime import PluginRegistry
from tangku_agentos.sdk import TangkuDeveloperSDK


def test_phase3_execution_engine_supports_retry_resume_and_parallelism():
    engine = TaskExecutionEngine()
    attempts = {}

    def runner(step):
        attempts[step.step_id] = attempts.get(step.step_id, 0) + 1
        if step.step_id == "inspect" and attempts[step.step_id] == 1:
            return False, "temporary failure"
        return True, f"done:{step.step_id}"

    plan = engine.create_plan(
        goal="Inspect repository",
        steps=[
            {"step_id": "inspect", "title": "Inspect workspace", "depends_on": []},
            {"step_id": "summarize", "title": "Summarize findings", "depends_on": ["inspect"]},
        ],
    )

    result = engine.execute_plan(plan, runner=runner, allow_parallel=True)

    assert result["status"] == "completed"
    assert attempts["inspect"] == 2
    assert plan.steps[0].retry_count == 1
    assert plan.steps[1].status == "completed"

    paused = engine.pause_plan(plan)
    assert paused["status"] == "paused"

    resumed = engine.resume_plan(plan)
    assert resumed["status"] == "completed"


def test_phase3_agents_memory_plugins_and_sdk_work_together():
    coding_agent = CodingAgent()
    planning_agent = PlanningAgent()
    research_agent = ResearchAgent()
    supervisor_agent = SupervisorAgent()

    assert coding_agent.profile.role == "coding"
    assert planning_agent.profile.role == "planning"
    assert research_agent.profile.role == "research"
    assert supervisor_agent.profile.role == "supervisor"

    memory = MemoryIntelligence()
    memory.store("conversation", "user", "Prefers concise summaries", namespace="conversation")
    memory.store("project", "workspace", "Test project uses pytest", namespace="project")
    semantic = memory.retrieve("pytest", namespace="project")
    assert semantic
    assert semantic[0]["content"].startswith("Test project")

    plugin_registry = PluginRegistry()
    plugin_registry.discover([{"name": "demo-plugin", "version": "1.0.0", "dependencies": []}])
    plugin_registry.install("demo-plugin")
    installed = plugin_registry.resolve("demo-plugin")
    assert installed is not None
    assert installed["state"] == "installed"

    sdk = TangkuDeveloperSDK()
    agent = sdk.create_agent("demo-agent")
    tool = sdk.create_tool("search")
    plugin = sdk.create_plugin("demo-plugin")
    assert agent.name == "demo-agent"
    assert tool.name == "search"
    assert plugin.name == "demo-plugin"

    demo = run_end_to_end_demo("Summarize the repository")
    assert demo["status"] == "completed"
    assert demo["summary"].startswith("Completed")
