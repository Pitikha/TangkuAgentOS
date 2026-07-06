import unittest

from tangku_agentos.planning_runtime import (
    PlanningManager,
    PlanningRegistry,
    PlanningSessionManager,
    PlanningContextManager,
    PlanningLifecycleManager,
    PlanningConfigurationManager,
    PlanningMetadataManager,
    PlanningStatisticsManager,
    PlanningHealthManager,
)
from tangku_agentos.reasoning_runtime import (
    ReasoningManager,
    ReasoningRegistry,
    ReasoningPipeline,
    ReasoningHistory,
    ReasoningStatistics,
)
from tangku_agentos.decision_runtime import (
    DecisionManager,
    DecisionRegistry,
    DecisionEvaluator,
    DecisionHistory,
    DecisionMetadata,
)
from tangku_agentos.goal_runtime import GoalManager, GoalRegistry, GoalLifecycle
from tangku_agentos.task_runtime import TaskManager, TaskRegistry, TaskQueue


class PlanningRuntimeSmokeTest(unittest.TestCase):
    def test_runtime_services_are_instantiable_and_operational(self) -> None:
        planning_manager = PlanningManager()
        planning_registry = PlanningRegistry()
        planning_session_manager = PlanningSessionManager()
        planning_context_manager = PlanningContextManager()
        planning_lifecycle_manager = PlanningLifecycleManager()
        planning_configuration_manager = PlanningConfigurationManager()
        planning_metadata_manager = PlanningMetadataManager()
        planning_statistics_manager = PlanningStatisticsManager()
        planning_health_manager = PlanningHealthManager()

        reasoning_manager = ReasoningManager()
        reasoning_registry = ReasoningRegistry()
        reasoning_pipeline = ReasoningPipeline()
        reasoning_history = ReasoningHistory()
        reasoning_statistics = ReasoningStatistics()

        decision_manager = DecisionManager()
        decision_registry = DecisionRegistry()
        decision_evaluator = DecisionEvaluator()
        decision_history = DecisionHistory()
        decision_metadata = DecisionMetadata()

        goal_manager = GoalManager()
        goal_registry = GoalRegistry()
        goal_lifecycle = GoalLifecycle()

        task_manager = TaskManager()
        task_registry = TaskRegistry()
        task_queue = TaskQueue()

        self.assertIsNotNone(planning_manager)
        self.assertIsNotNone(reasoning_manager)
        self.assertIsNotNone(decision_manager)
        self.assertIsNotNone(goal_manager)
        self.assertIsNotNone(task_manager)

        plan_id = planning_manager.create_plan("Investigate issue")
        self.assertTrue(plan_id)
        session = planning_session_manager.create_session(plan_id)
        self.assertTrue(session.session_id)

        reasoning_context = reasoning_manager.create_context("reasoning-1", "analysis")
        self.assertEqual(reasoning_context.context_id, "reasoning-1")

        decision = decision_manager.create_decision("choose-tool", {"priority": "high"})
        self.assertTrue(decision.decision_id)

        goal_id = goal_manager.create_goal("ship feature")
        self.assertTrue(goal_id)

        task_id = task_manager.create_task("implement runtime")
        self.assertTrue(task_id)


if __name__ == "__main__":
    unittest.main()
