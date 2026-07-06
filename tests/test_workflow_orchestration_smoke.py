from tangku_agentos.workflow_engine import (
    WorkflowEventManagerImpl,
    WorkflowManager,
    WorkflowRegistry,
    WorkflowStateManager,
    WorkflowContextManager,
    WorkflowQueue,
    WorkflowExecutorImpl,
    WorkflowHistoryManagerImpl,
    WorkflowLifecycleManagerImpl,
    Workflow,
    WorkflowNode,
    WorkflowEdge,
    WorkflowMetadata,
    WorkflowState,
    WorkflowContext,
)


def test_workflow_orchestration_smoke() -> None:
    registry = WorkflowRegistry()
    state_manager = WorkflowStateManager()
    history_manager = WorkflowHistoryManagerImpl()
    event_manager = WorkflowEventManagerImpl()
    context_provider = WorkflowContextManager()
    queue = WorkflowQueue()
    executor = WorkflowExecutorImpl()
    manager = WorkflowManager(registry, state_manager, history_manager, event_manager, context_provider, queue, executor)

    workflow = Workflow(
        workflow_id="demo-workflow",
        name="Demo Workflow",
        description="demo",
        metadata=WorkflowMetadata(version="1.0"),
        nodes=[WorkflowNode(node_id="start", name="start"), WorkflowNode(node_id="end", name="end")],
        edges=[WorkflowEdge(source_node_id="start", target_node_id="end")],
    )
    manager.create_workflow(workflow)
    instance = manager.start_workflow("demo-workflow")

    assert instance.workflow.workflow_id == "demo-workflow"
    assert instance.state == WorkflowState.COMPLETED
    assert queue.dequeue() is not None
    assert event_manager.list_events("workflow.started")

    print("workflow orchestration checks passed")
