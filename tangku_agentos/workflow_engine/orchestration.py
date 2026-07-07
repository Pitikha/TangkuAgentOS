from __future__ import annotations

from threading import RLock
from typing import Any


class WorkflowStudioManager:
    def __init__(self) -> None:
        self._templates: dict[str, dict[str, Any]] = {}
        self._lock = RLock()

    def register_template(self, template_id: str, payload: dict[str, Any]) -> None:
        with self._lock:
            self._templates[template_id] = payload

    def get_template(self, template_id: str) -> dict[str, Any] | None:
        with self._lock:
            return self._templates.get(template_id)


class PipelineManager:
    def __init__(self) -> None:
        self._pipelines: dict[str, dict[str, Any]] = {}
        self._lock = RLock()

    def register_pipeline(self, pipeline_id: str, payload: dict[str, Any]) -> None:
        with self._lock:
            self._pipelines[pipeline_id] = payload

    def get_pipeline(self, pipeline_id: str) -> dict[str, Any] | None:
        with self._lock:
            return self._pipelines.get(pipeline_id)


class ExecutionGraphManager:
    def __init__(self) -> None:
        self._graph: dict[str, list[tuple[str, str]]] = {"nodes": [], "edges": []}
        self._lock = RLock()

    def add_node(self, node_id: str) -> None:
        with self._lock:
            self._graph["nodes"].append(node_id)

    def add_edge(self, source: str, target: str) -> None:
        with self._lock:
            self._graph["edges"].append((source, target))

    def snapshot(self) -> dict[str, list[tuple[str, str]] | list[str]]:
        with self._lock:
            return {"nodes": list(self._graph["nodes"]), "edges": list(self._graph["edges"])}


class OrchestrationManager:
    def __init__(self) -> None:
        self._sessions: dict[str, dict[str, Any]] = {}
        self._lock = RLock()

    def create_session(self, session_id: str, payload: dict[str, Any]) -> None:
        with self._lock:
            self._sessions[session_id] = payload

    def get_session(self, session_id: str) -> dict[str, Any] | None:
        with self._lock:
            return self._sessions.get(session_id)


class WorkflowStateManagerExtended:
    def __init__(self) -> None:
        self._states: dict[str, dict[str, Any]] = {}
        self._lock = RLock()

    def set_state(self, workflow_id: str, state: str) -> None:
        with self._lock:
            self._states[workflow_id] = {"state": state}

    def get_state(self, workflow_id: str) -> dict[str, Any] | None:
        with self._lock:
            return self._states.get(workflow_id)


class WorkflowEventManager:
    def __init__(self) -> None:
        self._events: dict[str, list[dict[str, Any]]] = {}
        self._lock = RLock()

    def record(self, event_name: str, payload: dict[str, Any]) -> None:
        with self._lock:
            self._events.setdefault(event_name, []).append(payload)

    def list_events(self, event_name: str) -> list[dict[str, Any]]:
        with self._lock:
            return list(self._events.get(event_name, []))


class TemplateManager:
    def __init__(self) -> None:
        self._templates: dict[str, dict[str, Any]] = {}
        self._lock = RLock()

    def register(self, template_id: str, payload: dict[str, Any]) -> None:
        with self._lock:
            self._templates[template_id] = payload

    def get(self, template_id: str) -> dict[str, Any] | None:
        with self._lock:
            return self._templates.get(template_id)
