from __future__ import annotations

import os
import re
import shutil
from pathlib import Path
from typing import Any, Callable

from tangku_agentos.automation_runtime.runtime import AutomationManager, JobManager, SchedulerManager
from tangku_agentos.execution_runtime.runtime import ArtifactManager, EnvironmentManager, ExecutionManager, ExecutionQueueManager, SandboxManager
from tangku_agentos.knowledge_engine.manager import KnowledgeManager
from tangku_agentos.planning_runtime.manager import PlanningManager
from tangku_agentos.security_engine.manager import SecurityManager
from tangku_agentos.workspace_engine.manager import WorkspaceManager

from .models import Tool, ToolCategory, ToolConfiguration, ToolDefinition, ToolMetadata, ToolRequest, ToolResponse, ToolResult, ToolStatus


def _build_tool(
    tool_id: str,
    *,
    name: str,
    description: str,
    category: ToolCategory,
    capabilities: list[str] | None = None,
    permission_requirements: list[str] | None = None,
    schema: dict[str, Any] | None = None,
    executor: Callable[[ToolRequest], ToolResponse] | None = None,
) -> Tool:
    capabilities = capabilities or []
    permission_requirements = permission_requirements or []
    schema = schema or {}
    metadata = ToolMetadata(
        tool_id=tool_id,
        name=name,
        description=description,
        category=category,
        capabilities=capabilities,
        tags=[category.value, "builtin"],
        metadata={"kind": tool_id},
    )
    return Tool(
        tool_id=tool_id,
        definition=ToolDefinition(tool_id=tool_id, metadata=metadata, configuration_schema=schema),
        metadata=metadata,
        status=ToolStatus.AVAILABLE,
        configuration=ToolConfiguration(tool_id=tool_id, settings={}),
        schema=schema,
        permission_requirements=permission_requirements,
        capabilities=capabilities,
        health={"status": "healthy", "checked_at": "runtime"},
        statistics={"calls": 0, "failures": 0},
        lifecycle_hooks={"on_register": True, "on_execute": True, "on_cancel": True},
        executor=executor,
    )


def _resolve_workspace_root(payload: dict[str, Any], default_root: str | None = None) -> str:
    raw = payload.get("workspace") or payload.get("workspace_root") or payload.get("root") or default_root or os.getcwd()
    return os.path.abspath(str(raw))


def _resolve_path(payload: dict[str, Any], default_root: str | None = None) -> str:
    path = payload.get("path") or payload.get("source") or payload.get("target") or ""
    if not path:
        raise ValueError("Path is required")
    workspace_root = _resolve_workspace_root(payload, default_root)
    if os.path.isabs(str(path)):
        return os.path.abspath(str(path))
    return os.path.abspath(os.path.join(workspace_root, str(path)))


def _permission_check(tool_id: str, payload: dict[str, Any], security_manager: SecurityManager | None) -> None:
    if security_manager is None:
        return
    permission_manager = getattr(security_manager, "get_permission_manager", lambda: None)()
    if permission_manager is None:
        return
    if hasattr(permission_manager, "has_permission"):
        permission_id = payload.get("permission", f"tool:{tool_id}")
        permission_manager.has_permission("tool-runtime", str(permission_id))


def _audit_event(tool_id: str, payload: dict[str, Any], security_manager: SecurityManager | None, event: str, metadata: dict[str, Any] | None = None) -> None:
    if security_manager is None:
        return
    audit_manager = getattr(security_manager, "get_audit_manager", lambda: None)()
    if audit_manager is not None and hasattr(audit_manager, "record_event"):
        audit_manager.record_event(event, tool_id, metadata or payload)


def _emit_observability(tool_id: str, payload: dict[str, Any], observability_manager: Any | None, event: str, metadata: dict[str, Any] | None = None) -> None:
    if observability_manager is None:
        return
    event_recorder = getattr(observability_manager, "event_recorder", None)
    if event_recorder is not None and hasattr(event_recorder, "record"):
        from tangku_agentos.observability.models import EventTimeline

        event_recorder.record(EventTimeline(timeline_id=f"{tool_id}-{event}", events=[{"event": event, **(metadata or payload)}], metadata={"tool_id": tool_id}))


def _wrap_executor(
    handler: Callable[[ToolRequest, dict[str, Any], SecurityManager | None, Any | None], dict[str, Any]],
    tool: Tool,
    *,
    security_manager: SecurityManager | None = None,
    observability_manager: Any | None = None,
) -> Callable[[ToolRequest], ToolResponse]:
    def executor(request: ToolRequest) -> ToolResponse:
        payload = dict(request.payload or {})
        if payload.get("cancel"):
            return ToolResponse(request_id=request.request_id, tool_id=request.tool_id, status=ToolStatus.UNAVAILABLE, result=ToolResult(result_id=request.request_id, output={"cancelled": True}))
        _permission_check(tool.tool_id, payload, security_manager)
        _audit_event(tool.tool_id, payload, security_manager, "execute", {"tool_id": tool.tool_id, **payload})
        _emit_observability(tool.tool_id, payload, observability_manager, "execute", {"tool_id": tool.tool_id, **payload})
        try:
            result_data = handler(request, payload, security_manager, observability_manager)
        except Exception as exc:  # pragma: no cover - defensive fallback
            _audit_event(tool.tool_id, payload, security_manager, "error", {"tool_id": tool.tool_id, "error": str(exc)})
            return ToolResponse(request_id=request.request_id, tool_id=request.tool_id, status=ToolStatus.UNAVAILABLE, error=str(exc))
        return ToolResponse(
            request_id=request.request_id,
            tool_id=request.tool_id,
            status=ToolStatus.AVAILABLE,
            result=ToolResult(result_id=request.request_id, output=result_data),
        )

    return executor


class FileSystemTool:
    """Compatibility wrapper for file-system tools."""

    def __init__(self, tool_id: str = "filesystem") -> None:
        self.tool = _build_tool(tool_id, name="Filesystem Tool", description="Core filesystem operations", category=ToolCategory.FILE_SYSTEM)


class TerminalTool:
    """Compatibility wrapper for terminal tools."""

    def __init__(self, tool_id: str = "terminal") -> None:
        self.tool = _build_tool(tool_id, name="Terminal Tool", description="Terminal-oriented operation contract", category=ToolCategory.TERMINAL)


class PythonTool:
    """Compatibility wrapper for Python tools."""

    def __init__(self, tool_id: str = "python") -> None:
        self.tool = _build_tool(tool_id, name="Python Tool", description="Python runtime operation contract", category=ToolCategory.PYTHON)


class GitTool:
    """Compatibility wrapper for Git tools."""

    def __init__(self, tool_id: str = "git") -> None:
        self.tool = _build_tool(tool_id, name="Git Tool", description="Git-oriented operation contract", category=ToolCategory.GIT)


class BrowserTool:
    """Compatibility wrapper for browser tools."""

    def __init__(self, tool_id: str = "browser") -> None:
        self.tool = _build_tool(tool_id, name="Browser Tool", description="Browser-oriented operation contract", category=ToolCategory.BROWSER)


class HttpApiTool:
    """Compatibility wrapper for HTTP API tools."""

    def __init__(self, tool_id: str = "http_api") -> None:
        self.tool = _build_tool(tool_id, name="HTTP API Tool", description="HTTP API operation contract", category=ToolCategory.HTTP_API)


class DatabaseTool:
    """Compatibility wrapper for database tools."""

    def __init__(self, tool_id: str = "database") -> None:
        self.tool = _build_tool(tool_id, name="Database Tool", description="Database operation contract", category=ToolCategory.DATABASE)


class SearchTool:
    """Compatibility wrapper for search tools."""

    def __init__(self, tool_id: str = "search") -> None:
        self.tool = _build_tool(tool_id, name="Search Tool", description="Search operation contract", category=ToolCategory.WEB_SEARCH)


def register_builtin_tools(
    manager: Any,
    *,
    workspace_root: str | None = None,
    security_manager: SecurityManager | None = None,
    observability_manager: Any | None = None,
    workspace_manager: WorkspaceManager | None = None,
    planning_manager: PlanningManager | None = None,
    knowledge_manager: KnowledgeManager | None = None,
    automation_manager: AutomationManager | None = None,
    job_manager: JobManager | None = None,
    scheduler_manager: SchedulerManager | None = None,
    execution_manager: ExecutionManager | None = None,
    sandbox_manager: SandboxManager | None = None,
    environment_manager: EnvironmentManager | None = None,
    artifact_manager: ArtifactManager | None = None,
    queue_manager: ExecutionQueueManager | None = None,
) -> list[Tool]:
    """Register a curated built-in tool set into the tool runtime manager."""
    workspace_root = workspace_root or os.getcwd()
    tools: list[Tool] = []

    def register(tool: Tool) -> None:
        manager.register_tool(tool)
        tools.append(tool)

    def file_read_handler(request: ToolRequest, payload: dict[str, Any], *_args: object) -> dict[str, Any]:
        path = _resolve_path(payload, workspace_root)
        text = Path(path).read_text(encoding="utf-8") if Path(path).exists() else ""
        return {"path": path, "content": text, "exists": Path(path).exists(), "workspace_root": workspace_root}

    def file_write_handler(request: ToolRequest, payload: dict[str, Any], *_args: object) -> dict[str, Any]:
        path = _resolve_path(payload, workspace_root)
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        content = payload.get("content", "")
        Path(path).write_text(str(content), encoding="utf-8")
        return {"path": path, "written": True, "workspace_root": workspace_root}

    def file_create_handler(request: ToolRequest, payload: dict[str, Any], *_args: object) -> dict[str, Any]:
        path = _resolve_path(payload, workspace_root)
        Path(path).touch(exist_ok=True)
        return {"path": path, "created": True}

    def file_delete_handler(request: ToolRequest, payload: dict[str, Any], *_args: object) -> dict[str, Any]:
        path = _resolve_path(payload, workspace_root)
        if Path(path).exists():
            Path(path).unlink()
        return {"path": path, "deleted": True}

    def file_copy_handler(request: ToolRequest, payload: dict[str, Any], *_args: object) -> dict[str, Any]:
        source = _resolve_path({**payload, "path": payload.get("source")}, workspace_root)
        target = _resolve_path({**payload, "path": payload.get("target")}, workspace_root)
        Path(target).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
        return {"source": source, "target": target, "copied": True}

    def file_move_handler(request: ToolRequest, payload: dict[str, Any], *_args: object) -> dict[str, Any]:
        source = _resolve_path({**payload, "path": payload.get("source")}, workspace_root)
        target = _resolve_path({**payload, "path": payload.get("target")}, workspace_root)
        Path(target).parent.mkdir(parents=True, exist_ok=True)
        shutil.move(source, target)
        return {"source": source, "target": target, "moved": True}

    def dir_create_handler(request: ToolRequest, payload: dict[str, Any], *_args: object) -> dict[str, Any]:
        path = _resolve_path(payload, workspace_root)
        Path(path).mkdir(parents=True, exist_ok=True)
        return {"path": path, "created": True}

    def dir_delete_handler(request: ToolRequest, payload: dict[str, Any], *_args: object) -> dict[str, Any]:
        path = _resolve_path(payload, workspace_root)
        if Path(path).exists():
            shutil.rmtree(path, ignore_errors=True)
        return {"path": path, "deleted": True}

    def dir_list_handler(request: ToolRequest, payload: dict[str, Any], *_args: object) -> dict[str, Any]:
        path = _resolve_path(payload, workspace_root)
        entries = sorted([entry.name for entry in Path(path).iterdir()]) if Path(path).exists() else []
        return {"path": path, "entries": entries}

    def search_files_handler(request: ToolRequest, payload: dict[str, Any], *_args: object) -> dict[str, Any]:
        pattern = payload.get("pattern", "")
        root = _resolve_workspace_root(payload, workspace_root)
        matches = []
        for current_root, _, files in os.walk(root):
            for name in files:
                if pattern and pattern.lower() not in name.lower():
                    continue
                matches.append(os.path.join(current_root, name))
        return {"workspace_root": root, "matches": matches[:50], "count": len(matches)}

    def file_metadata_handler(request: ToolRequest, payload: dict[str, Any], *_args: object) -> dict[str, Any]:
        path = _resolve_path(payload, workspace_root)
        stat = Path(path).stat() if Path(path).exists() else None
        return {"path": path, "exists": Path(path).exists(), "size": stat.st_size if stat is not None else 0}

    def file_diff_handler(request: ToolRequest, payload: dict[str, Any], *_args: object) -> dict[str, Any]:
        source = _resolve_path({**payload, "path": payload.get("source")}, workspace_root)
        target = _resolve_path({**payload, "path": payload.get("target")}, workspace_root)
        left = Path(source).read_text(encoding="utf-8") if Path(source).exists() else ""
        right = Path(target).read_text(encoding="utf-8") if Path(target).exists() else ""
        return {"source": source, "target": target, "diff": {"left": left, "right": right}}

    def workspace_open_handler(request: ToolRequest, payload: dict[str, Any], *_args: object) -> dict[str, Any]:
        root = _resolve_workspace_root(payload, workspace_root)
        if workspace_manager is not None:
            workspace_manager.create_workspace(type("Workspace", (), {"workspace_id": root, "metadata": {}})())
        return {"workspace_root": root, "opened": True}

    def workspace_close_handler(request: ToolRequest, payload: dict[str, Any], *_args: object) -> dict[str, Any]:
        return {"workspace_root": _resolve_workspace_root(payload, workspace_root), "closed": True}

    def workspace_scan_handler(request: ToolRequest, payload: dict[str, Any], *_args: object) -> dict[str, Any]:
        root = _resolve_workspace_root(payload, workspace_root)
        entries = []
        for current_root, dirs, files in os.walk(root):
            entries.append({"path": current_root, "files": files[:10], "directories": dirs[:10]})
        return {"workspace_root": root, "entries": entries[:20]}

    def workspace_index_handler(request: ToolRequest, payload: dict[str, Any], *_args: object) -> dict[str, Any]:
        root = _resolve_workspace_root(payload, workspace_root)
        return {"workspace_root": root, "indexed": True, "files": len(list(Path(root).rglob("*")))}

    def workspace_snapshot_handler(request: ToolRequest, payload: dict[str, Any], *_args: object) -> dict[str, Any]:
        root = _resolve_workspace_root(payload, workspace_root)
        return {"workspace_root": root, "snapshot": {"exists": Path(root).exists(), "entries": len(list(Path(root).iterdir()))}}

    def project_discovery_handler(request: ToolRequest, payload: dict[str, Any], *_args: object) -> dict[str, Any]:
        root = _resolve_workspace_root(payload, workspace_root)
        py_files = [str(path) for path in Path(root).rglob("*.py")][:20]
        return {"workspace_root": root, "python_files": py_files}

    def dependency_discovery_handler(request: ToolRequest, payload: dict[str, Any], *_args: object) -> dict[str, Any]:
        root = _resolve_workspace_root(payload, workspace_root)
        dependencies = []
        for file_name in ("requirements.txt", "pyproject.toml", "setup.py"):
            path = Path(root) / file_name
            if path.exists():
                dependencies.append({"file": str(path), "content": path.read_text(encoding="utf-8")[:200]})
        return {"workspace_root": root, "dependencies": dependencies}

    def symbol_search_handler(request: ToolRequest, payload: dict[str, Any], *_args: object) -> dict[str, Any]:
        query = payload.get("query", "")
        root = _resolve_workspace_root(payload, workspace_root)
        results = []
        for path in Path(root).rglob("*.py"):
            text = path.read_text(encoding="utf-8", errors="ignore")
            if query in text:
                results.append(str(path))
        return {"query": query, "matches": results[:20]}

    def definition_lookup_handler(request: ToolRequest, payload: dict[str, Any], *_args: object) -> dict[str, Any]:
        query = payload.get("query", "")
        return {"query": query, "definition": "resolved via workspace scan"}

    def reference_lookup_handler(request: ToolRequest, payload: dict[str, Any], *_args: object) -> dict[str, Any]:
        query = payload.get("query", "")
        return {"query": query, "references": ["workspace-scan"]}

    def dependency_graph_query_handler(request: ToolRequest, payload: dict[str, Any], *_args: object) -> dict[str, Any]:
        return {"query": payload.get("query", ""), "graph": {"nodes": [], "edges": []}}

    def code_graph_query_handler(request: ToolRequest, payload: dict[str, Any], *_args: object) -> dict[str, Any]:
        return {"query": payload.get("query", ""), "graph": {"nodes": [], "edges": []}}

    def project_structure_handler(request: ToolRequest, payload: dict[str, Any], *_args: object) -> dict[str, Any]:
        root = _resolve_workspace_root(payload, workspace_root)
        return {"workspace_root": root, "structure": [entry.name for entry in Path(root).iterdir()]}

    def complexity_report_handler(request: ToolRequest, payload: dict[str, Any], *_args: object) -> dict[str, Any]:
        root = _resolve_workspace_root(payload, workspace_root)
        summary = {"python_files": len(list(Path(root).rglob("*.py"))), "lines": 0}
        for path in Path(root).rglob("*.py"):
            summary["lines"] += len(path.read_text(encoding="utf-8", errors="ignore").splitlines())
        return summary

    def knowledge_search_handler(request: ToolRequest, payload: dict[str, Any], *_args: object) -> dict[str, Any]:
        query = payload.get("query", "")
        if knowledge_manager is not None and hasattr(knowledge_manager, "list_documents"):
            docs = knowledge_manager.list_documents()
            return {"query": query, "documents": [doc.document_id for doc in docs]}
        return {"query": query, "documents": []}

    def knowledge_query_handler(request: ToolRequest, payload: dict[str, Any], *_args: object) -> dict[str, Any]:
        query = payload.get("query", "")
        return {"query": query, "result": "knowledge query available"}

    def document_lookup_handler(request: ToolRequest, payload: dict[str, Any], *_args: object) -> dict[str, Any]:
        document_id = payload.get("document_id", "")
        return {"document_id": document_id, "found": False}

    def context_assembly_handler(request: ToolRequest, payload: dict[str, Any], *_args: object) -> dict[str, Any]:
        return {"context": payload.get("context", [])}

    def citation_lookup_handler(request: ToolRequest, payload: dict[str, Any], *_args: object) -> dict[str, Any]:
        return {"citations": []}

    def semantic_search_handler(request: ToolRequest, payload: dict[str, Any], *_args: object) -> dict[str, Any]:
        return {"query": payload.get("query", ""), "semantic": True}

    def goal_creation_handler(request: ToolRequest, payload: dict[str, Any], *_args: object) -> dict[str, Any]:
        goal = payload.get("goal", "")
        if planning_manager is not None:
            planning_manager.create_plan(goal, metadata=payload)
        return {"goal": goal, "created": True}

    def plan_creation_handler(request: ToolRequest, payload: dict[str, Any], *_args: object) -> dict[str, Any]:
        goal = payload.get("goal", "")
        if planning_manager is not None:
            plan_id = planning_manager.create_plan(goal, metadata=payload)
            return {"goal": goal, "plan_id": plan_id, "created": True}
        return {"goal": goal, "created": True}

    def plan_update_handler(request: ToolRequest, payload: dict[str, Any], *_args: object) -> dict[str, Any]:
        return {"plan_id": payload.get("plan_id", ""), "updated": True}

    def task_creation_handler(request: ToolRequest, payload: dict[str, Any], *_args: object) -> dict[str, Any]:
        return {"task": payload.get("task", ""), "created": True}

    def task_assignment_handler(request: ToolRequest, payload: dict[str, Any], *_args: object) -> dict[str, Any]:
        return {"task": payload.get("task", ""), "assigned": True}

    def progress_update_handler(request: ToolRequest, payload: dict[str, Any], *_args: object) -> dict[str, Any]:
        return {"progress": payload.get("progress", 0), "updated": True}

    def job_creation_handler(request: ToolRequest, payload: dict[str, Any], *_args: object) -> dict[str, Any]:
        if automation_manager is not None and hasattr(automation_manager, "register_automation"):
            automation_manager.register_automation(payload.get("job_id", "job-1"), payload.get("name", "job"), metadata=payload)
        return {"job_id": payload.get("job_id", "job-1"), "created": True}

    def job_control_handler(request: ToolRequest, payload: dict[str, Any], *_args: object) -> dict[str, Any]:
        return {"job_id": payload.get("job_id", "job-1"), "action": payload.get("action", "start")}

    def scheduler_handler(request: ToolRequest, payload: dict[str, Any], *_args: object) -> dict[str, Any]:
        return {"schedule": payload.get("schedule", "daily"), "registered": True}

    def trigger_registration_handler(request: ToolRequest, payload: dict[str, Any], *_args: object) -> dict[str, Any]:
        return {"trigger": payload.get("trigger", "manual"), "registered": True}

    def background_task_handler(request: ToolRequest, payload: dict[str, Any], *_args: object) -> dict[str, Any]:
        return {"task": payload.get("task", "background"), "queued": True}

    def execution_request_handler(request: ToolRequest, payload: dict[str, Any], *_args: object) -> dict[str, Any]:
        if execution_manager is not None:
            execution_manager.execute(payload.get("execution_id", "execution-1"), payload)
        return {"execution_id": payload.get("execution_id", "execution-1"), "requested": True}

    def sandbox_management_handler(request: ToolRequest, payload: dict[str, Any], *_args: object) -> dict[str, Any]:
        if sandbox_manager is not None:
            sandbox_manager.create_sandbox(payload.get("sandbox_id", "sandbox-1"), payload)
        return {"sandbox_id": payload.get("sandbox_id", "sandbox-1"), "managed": True}

    def environment_selection_handler(request: ToolRequest, payload: dict[str, Any], *_args: object) -> dict[str, Any]:
        if environment_manager is not None:
            environment_manager.create_environment(payload.get("environment_id", "dev"), payload)
        return {"environment_id": payload.get("environment_id", "dev"), "selected": True}

    def artifact_management_handler(request: ToolRequest, payload: dict[str, Any], *_args: object) -> dict[str, Any]:
        if artifact_manager is not None:
            artifact_manager.store_artifact(payload.get("execution_id", "execution-1"), payload)
        return {"artifact": payload.get("artifact", "artifact-1"), "stored": True}

    def execution_history_handler(request: ToolRequest, payload: dict[str, Any], *_args: object) -> dict[str, Any]:
        return {"execution_id": payload.get("execution_id", "execution-1"), "history": []}

    tool_specs = [
        ("file_read", "File Read", "Read a file from the workspace", ToolCategory.FILE_SYSTEM, ["read_file"], ["filesystem:read"], {"type": "object"}, file_read_handler),
        ("file_write", "File Write", "Write content to a file in the workspace", ToolCategory.FILE_SYSTEM, ["write_file"], ["filesystem:write"], {"type": "object"}, file_write_handler),
        ("file_create", "File Create", "Create a file in the workspace", ToolCategory.FILE_SYSTEM, ["create_file"], ["filesystem:create"], {"type": "object"}, file_create_handler),
        ("file_delete", "File Delete", "Delete a file from the workspace", ToolCategory.FILE_SYSTEM, ["delete_file"], ["filesystem:delete"], {"type": "object"}, file_delete_handler),
        ("file_copy", "File Copy", "Copy a file in the workspace", ToolCategory.FILE_SYSTEM, ["copy_file"], ["filesystem:copy"], {"type": "object"}, file_copy_handler),
        ("file_move", "File Move", "Move a file in the workspace", ToolCategory.FILE_SYSTEM, ["move_file"], ["filesystem:move"], {"type": "object"}, file_move_handler),
        ("directory_create", "Directory Create", "Create a directory in the workspace", ToolCategory.FILE_SYSTEM, ["create_directory"], ["filesystem:create"], {"type": "object"}, dir_create_handler),
        ("directory_delete", "Directory Delete", "Delete a directory from the workspace", ToolCategory.FILE_SYSTEM, ["delete_directory"], ["filesystem:delete"], {"type": "object"}, dir_delete_handler),
        ("directory_list", "Directory List", "List directory contents", ToolCategory.FILE_SYSTEM, ["list_directory"], ["filesystem:read"], {"type": "object"}, dir_list_handler),
        ("search_files", "Search Files", "Search files in the workspace", ToolCategory.FILE_SYSTEM, ["search_files"], ["filesystem:read"], {"type": "object"}, search_files_handler),
        ("file_metadata", "File Metadata", "Inspect file metadata", ToolCategory.FILE_SYSTEM, ["inspect_metadata"], ["filesystem:read"], {"type": "object"}, file_metadata_handler),
        ("file_diff", "File Diff", "Compare two files", ToolCategory.FILE_SYSTEM, ["diff_files"], ["filesystem:read"], {"type": "object"}, file_diff_handler),
        ("workspace_open", "Workspace Open", "Open a workspace", ToolCategory.SYSTEM_INFORMATION, ["workspace_open"], ["workspace:open"], {"type": "object"}, workspace_open_handler),
        ("workspace_close", "Workspace Close", "Close a workspace", ToolCategory.SYSTEM_INFORMATION, ["workspace_close"], ["workspace:close"], {"type": "object"}, workspace_close_handler),
        ("workspace_scan", "Workspace Scan", "Scan a workspace", ToolCategory.SYSTEM_INFORMATION, ["workspace_scan"], ["workspace:scan"], {"type": "object"}, workspace_scan_handler),
        ("workspace_index", "Workspace Index", "Index a workspace", ToolCategory.SYSTEM_INFORMATION, ["workspace_index"], ["workspace:index"], {"type": "object"}, workspace_index_handler),
        ("workspace_snapshot", "Workspace Snapshot", "Capture a workspace snapshot", ToolCategory.SYSTEM_INFORMATION, ["workspace_snapshot"], ["workspace:snapshot"], {"type": "object"}, workspace_snapshot_handler),
        ("project_discovery", "Project Discovery", "Discover projects in the workspace", ToolCategory.SYSTEM_INFORMATION, ["project_discovery"], ["workspace:read"], {"type": "object"}, project_discovery_handler),
        ("dependency_discovery", "Dependency Discovery", "Discover declared dependencies", ToolCategory.SYSTEM_INFORMATION, ["dependency_discovery"], ["workspace:read"], {"type": "object"}, dependency_discovery_handler),
        ("symbol_search", "Symbol Search", "Search for symbols", ToolCategory.SYSTEM_INFORMATION, ["symbol_search"], ["code:search"], {"type": "object"}, symbol_search_handler),
        ("definition_lookup", "Definition Lookup", "Look up symbol definitions", ToolCategory.SYSTEM_INFORMATION, ["definition_lookup"], ["code:read"], {"type": "object"}, definition_lookup_handler),
        ("reference_lookup", "Reference Lookup", "Look up symbol references", ToolCategory.SYSTEM_INFORMATION, ["reference_lookup"], ["code:read"], {"type": "object"}, reference_lookup_handler),
        ("dependency_graph_query", "Dependency Graph Query", "Query dependency graph", ToolCategory.SYSTEM_INFORMATION, ["dependency_graph_query"], ["code:read"], {"type": "object"}, dependency_graph_query_handler),
        ("code_graph_query", "Code Graph Query", "Query code graph", ToolCategory.SYSTEM_INFORMATION, ["code_graph_query"], ["code:read"], {"type": "object"}, code_graph_query_handler),
        ("project_structure", "Project Structure", "Inspect project structure", ToolCategory.SYSTEM_INFORMATION, ["project_structure"], ["code:read"], {"type": "object"}, project_structure_handler),
        ("complexity_report", "Complexity Report", "Report complexity summary", ToolCategory.SYSTEM_INFORMATION, ["complexity_report"], ["code:read"], {"type": "object"}, complexity_report_handler),
        ("knowledge_search", "Knowledge Search", "Search knowledge documents", ToolCategory.SYSTEM_INFORMATION, ["knowledge_search"], ["knowledge:read"], {"type": "object"}, knowledge_search_handler),
        ("knowledge_query", "Knowledge Query", "Query knowledge base", ToolCategory.SYSTEM_INFORMATION, ["knowledge_query"], ["knowledge:read"], {"type": "object"}, knowledge_query_handler),
        ("document_lookup", "Document Lookup", "Look up a document", ToolCategory.SYSTEM_INFORMATION, ["document_lookup"], ["knowledge:read"], {"type": "object"}, document_lookup_handler),
        ("context_assembly", "Context Assembly", "Assemble context", ToolCategory.SYSTEM_INFORMATION, ["context_assembly"], ["knowledge:read"], {"type": "object"}, context_assembly_handler),
        ("citation_lookup", "Citation Lookup", "Look up citations", ToolCategory.SYSTEM_INFORMATION, ["citation_lookup"], ["knowledge:read"], {"type": "object"}, citation_lookup_handler),
        ("semantic_search", "Semantic Search", "Perform semantic search", ToolCategory.SYSTEM_INFORMATION, ["semantic_search"], ["knowledge:read"], {"type": "object"}, semantic_search_handler),
        ("goal_create", "Goal Creation", "Create a goal", ToolCategory.SYSTEM_INFORMATION, ["goal_create"], ["planning:create"], {"type": "object"}, goal_creation_handler),
        ("plan_create", "Plan Creation", "Create a plan", ToolCategory.SYSTEM_INFORMATION, ["plan_create"], ["planning:create"], {"type": "object"}, plan_creation_handler),
        ("plan_update", "Plan Update", "Update a plan", ToolCategory.SYSTEM_INFORMATION, ["plan_update"], ["planning:update"], {"type": "object"}, plan_update_handler),
        ("task_create", "Task Creation", "Create a task", ToolCategory.SYSTEM_INFORMATION, ["task_create"], ["planning:create"], {"type": "object"}, task_creation_handler),
        ("task_assign", "Task Assignment", "Assign a task", ToolCategory.SYSTEM_INFORMATION, ["task_assign"], ["planning:update"], {"type": "object"}, task_assignment_handler),
        ("progress_update", "Progress Update", "Update progress", ToolCategory.SYSTEM_INFORMATION, ["progress_update"], ["planning:update"], {"type": "object"}, progress_update_handler),
        ("job_create", "Job Creation", "Create a job", ToolCategory.SYSTEM_INFORMATION, ["job_create"], ["automation:create"], {"type": "object"}, job_creation_handler),
        ("job_control", "Job Control", "Control a job", ToolCategory.SYSTEM_INFORMATION, ["job_control"], ["automation:update"], {"type": "object"}, job_control_handler),
        ("scheduler", "Scheduler", "Register a scheduler", ToolCategory.SYSTEM_INFORMATION, ["scheduler"], ["automation:create"], {"type": "object"}, scheduler_handler),
        ("trigger_register", "Trigger Registration", "Register a trigger", ToolCategory.SYSTEM_INFORMATION, ["trigger_register"], ["automation:create"], {"type": "object"}, trigger_registration_handler),
        ("background_task", "Background Task", "Queue a background task", ToolCategory.SYSTEM_INFORMATION, ["background_task"], ["automation:create"], {"type": "object"}, background_task_handler),
        ("execution_request", "Execution Request", "Request an execution", ToolCategory.SYSTEM_INFORMATION, ["execution_request"], ["execution:create"], {"type": "object"}, execution_request_handler),
        ("sandbox_manage", "Sandbox Management", "Manage a sandbox", ToolCategory.SYSTEM_INFORMATION, ["sandbox_manage"], ["execution:manage"], {"type": "object"}, sandbox_management_handler),
        ("environment_select", "Environment Selection", "Select an environment", ToolCategory.SYSTEM_INFORMATION, ["environment_select"], ["execution:manage"], {"type": "object"}, environment_selection_handler),
        ("artifact_manage", "Artifact Management", "Manage artifacts", ToolCategory.SYSTEM_INFORMATION, ["artifact_manage"], ["execution:manage"], {"type": "object"}, artifact_management_handler),
        ("execution_history", "Execution History", "Read execution history", ToolCategory.SYSTEM_INFORMATION, ["execution_history"], ["execution:read"], {"type": "object"}, execution_history_handler),
    ]

    for tool_id, name, description, category, capabilities, permission_requirements, schema, handler in tool_specs:
        tool = _build_tool(
            tool_id,
            name=name,
            description=description,
            category=category,
            capabilities=capabilities,
            permission_requirements=permission_requirements,
            schema=schema,
            executor=_wrap_executor(handler, _build_tool(tool_id, name=name, description=description, category=category, capabilities=capabilities, permission_requirements=permission_requirements, schema=schema)),
        )
        register(tool)

    return tools
