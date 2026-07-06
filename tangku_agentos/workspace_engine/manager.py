from __future__ import annotations

import os
import shutil
import time
from pathlib import Path
from threading import RLock
from typing import Any, Dict, List

from tangku_agentos.configuration.manager import ConfigurationManager
from tangku_agentos.configuration.models import Configuration
from tangku_agentos.core_runtime.event_bus import EventBus
from tangku_agentos.observability.events import EventRecorder
from tangku_agentos.observability.models import EventTimeline
from tangku_agentos.repository_intelligence.manager import GitManager
from tangku_agentos.security_engine.manager import SecurityManager
from tangku_agentos.security_engine.models import Permission

from .exceptions import WorkspaceManagerError
from .interfaces import WorkspaceManagerInterface
from .models import Workspace, WorkspaceConfiguration, WorkspaceMetadata, WorkspaceStatistics
from .registry import WorkspaceRegistry


class WorkspaceManager(WorkspaceManagerInterface):
    """Filesystem-backed workspace manager for real workspace operations."""

    def __init__(self, registry: WorkspaceRegistry | None = None, security_manager: SecurityManager | None = None, configuration_manager: ConfigurationManager | None = None, observability_manager: Any | None = None, event_bus: EventBus | None = None) -> None:
        self._registry = registry or WorkspaceRegistry()
        self._security_manager = security_manager
        self._configuration_manager = configuration_manager or ConfigurationManager()
        self._observability_manager = observability_manager
        self._event_bus = event_bus or EventBus()
        self._workspaces: Dict[str, Workspace] = {}
        self._sessions: Dict[str, Dict[str, Any]] = {}
        self._active_workspace_ids: list[str] = []
        self._changes: Dict[str, List[Dict[str, Any]]] = {}
        self._lock = RLock()
        self._git_manager = GitManager()
        self._event_recorder = getattr(observability_manager, "event_recorder", None) if observability_manager is not None else None
        self._statistics: Dict[str, WorkspaceStatistics] = {}
        self._configurations: Dict[str, WorkspaceConfiguration] = {}
        self._health: Dict[str, dict[str, Any]] = {}
        self._operation_times: Dict[str, list[float]] = {}

    def _audit(self, workspace_id: str, operation: str, metadata: dict[str, Any] | None = None) -> None:
        if self._security_manager is None:
            return
        audit_manager = getattr(self._security_manager, "get_audit_manager", None)
        if callable(audit_manager):
            audit_manager().record_event(operation, workspace_id, metadata=metadata or {})

    def _emit_event(self, event_type: str, workspace_id: str, payload: dict[str, Any] | None = None) -> None:
        self._event_bus.publish(event_type, payload or {}, metadata={"workspace_id": workspace_id})
        if self._event_recorder is not None and hasattr(self._event_recorder, "record"):
            self._event_recorder.record(EventTimeline(timeline_id=workspace_id, events=[{"event": event_type, "workspace_id": workspace_id}], metadata=payload or {}))

    def _get_configuration(self, workspace_id: str) -> WorkspaceConfiguration:
        config = self._configurations.get(workspace_id)
        if config is None:
            config = WorkspaceConfiguration(
                watch_enabled=True,
                language_detection=True,
                framework_detection=True,
                metadata={"encoding": "utf-8", "newline": "\n", "ignored_directories": [".git", "__pycache__"], "ignored_files": [".DS_Store"], "workspace_limits": {"max_files": 10000}},
            )
            self._configurations[workspace_id] = config
        return config

    def _load_configuration(self, workspace_id: str) -> WorkspaceConfiguration:
        config_obj = self._configuration_manager.get(workspace_id) if self._configuration_manager is not None else None
        if config_obj is not None and getattr(config_obj, "settings", None):
            settings = config_obj.settings
            return WorkspaceConfiguration(
                watch_enabled=settings.get("watch_enabled", True),
                language_detection=settings.get("language_detection", True),
                framework_detection=settings.get("framework_detection", True),
                metadata={
                    "encoding": settings.get("encoding", "utf-8"),
                    "newline": settings.get("newline", "\n"),
                    "ignored_directories": settings.get("ignored_directories", [".git", "__pycache__"]),
                    "ignored_files": settings.get("ignored_files", [".DS_Store"]),
                    "workspace_limits": settings.get("workspace_limits", {"max_files": 10000}),
                },
            )
        return self._get_configuration(workspace_id)

    def _ensure_security(self, workspace_id: str, operation: str) -> None:
        if self._security_manager is None:
            return
        permission_manager = getattr(self._security_manager, "get_permission_manager", None)
        if callable(permission_manager):
            permission_manager().grant(workspace_id, Permission(permission_id=f"{workspace_id}:{operation}", name=operation, resource=workspace_id, actions=[operation]))
        self._audit(workspace_id, operation, metadata={"workspace_id": workspace_id})

    def _record_operation(self, workspace_id: str, operation: str, duration: float, error: str | None = None) -> None:
        stats = self._statistics.get(workspace_id, WorkspaceStatistics())
        stats.metadata["operations"] = stats.metadata.get("operations", 0) + 1
        if operation.startswith("read"):
            stats.metadata["read_count"] = stats.metadata.get("read_count", 0) + 1
        elif operation.startswith("write") or operation.startswith("append"):
            stats.metadata["write_count"] = stats.metadata.get("write_count", 0) + 1
        if error:
            stats.metadata["errors"] = stats.metadata.get("errors", 0) + 1
        stats.metadata["avg_operation_duration"] = self._average_duration(workspace_id, duration)
        self._statistics[workspace_id] = stats
        self._operation_times[workspace_id] = self._operation_times.get(workspace_id, []) + [duration]

    def _average_duration(self, workspace_id: str, duration: float) -> float:
        durations = self._operation_times.get(workspace_id, [])
        durations = durations + [duration]
        return round(sum(durations) / len(durations), 6)

    def _workspace_root(self, workspace: Workspace) -> Path:
        return Path(workspace.root_path).resolve()

    def _repo_metadata(self, workspace: Workspace) -> dict[str, Any]:
        git_manager = self._git_manager
        repository_path = str(self._workspace_root(workspace))
        try:
            status = git_manager.status(repository_path, repository_id=workspace.workspace_id)
            return {
                "is_git_repo": True,
                "root": repository_path,
                "branch": status.branch,
                "dirty": status.is_dirty,
            }
        except Exception:
            return {"is_git_repo": False, "root": repository_path, "branch": None, "dirty": False}

    def initialize(self) -> None:
        self._emit_event("workspace.initialized", "system")

    def start(self) -> None:
        self._emit_event("workspace.started", "system")

    def pause(self) -> None:
        self._emit_event("workspace.paused", "system")

    def resume(self) -> None:
        self._emit_event("workspace.resumed", "system")

    def stop(self) -> None:
        self._emit_event("workspace.stopped", "system")

    def shutdown(self) -> None:
        self._emit_event("workspace.shutdown", "system")

    def cleanup(self) -> None:
        self._emit_event("workspace.cleaned", "system")

    def create_workspace(self, workspace: Workspace) -> Workspace:
        with self._lock:
            self._ensure_security(workspace.workspace_id, "create_workspace")
            workspace_path = self._workspace_root(workspace)
            workspace_path.mkdir(parents=True, exist_ok=True)
            self._registry.register(workspace)
            self._workspaces[workspace.workspace_id] = workspace
            self._sessions[workspace.workspace_id] = {"workspace_id": workspace.workspace_id, "active": True, "created_at": time.time()}
            self._active_workspace_ids.append(workspace.workspace_id)
            self._configurations[workspace.workspace_id] = self._load_configuration(workspace.workspace_id)
            self._statistics[workspace.workspace_id] = WorkspaceStatistics(file_count=0, project_count=0, module_count=0, metadata={"operations": 0, "read_count": 0, "write_count": 0, "errors": 0, "avg_operation_duration": 0.0})
            self._health[workspace.workspace_id] = {"status": "healthy", "filesystem_accessible": True, "integrity": "ok", "repository_available": self._repo_metadata(workspace).get("is_git_repo", False)}
            self._emit_event("workspace.created", workspace.workspace_id, {"path": str(workspace_path)})
            return workspace

    def open_workspace(self, workspace_id: str) -> Workspace:
        with self._lock:
            workspace = self.get_workspace(workspace_id)
            self._ensure_security(workspace_id, "open_workspace")
            self._sessions[workspace_id] = {"workspace_id": workspace_id, "active": True, "opened_at": time.time()}
            self._active_workspace_ids = list(dict.fromkeys([*self._active_workspace_ids, workspace_id]))
            self._emit_event("workspace.opened", workspace_id, {"path": workspace.root_path})
            return workspace

    def close_workspace(self, workspace_id: str) -> Workspace:
        with self._lock:
            workspace = self.get_workspace(workspace_id)
            self._ensure_security(workspace_id, "close_workspace")
            self._sessions[workspace_id] = {"workspace_id": workspace_id, "active": False, "closed_at": time.time()}
            self._emit_event("workspace.closed", workspace_id, {"path": workspace.root_path})
            return workspace

    def delete_workspace(self, workspace_id: str) -> None:
        with self._lock:
            workspace = self.get_workspace(workspace_id)
            self._ensure_security(workspace_id, "delete_workspace")
            shutil.rmtree(workspace.root_path, ignore_errors=True)
            if hasattr(self._registry, "unregister"):
                self._registry.unregister(workspace_id)
            self._workspaces.pop(workspace_id, None)
            self._sessions.pop(workspace_id, None)
            self._active_workspace_ids = [item for item in self._active_workspace_ids if item != workspace_id]
            self._emit_event("workspace.deleted", workspace_id, {"path": workspace.root_path})

    def clone_workspace(self, workspace: Workspace, source_path: str) -> Workspace:
        with self._lock:
            self._ensure_security(workspace.workspace_id, "clone_workspace")
            shutil.copytree(source_path, workspace.root_path, dirs_exist_ok=True)
            self.create_workspace(workspace)
            self._emit_event("workspace.cloned", workspace.workspace_id, {"source_path": source_path})
            return workspace

    def copy_workspace(self, workspace_id: str, destination_path: str) -> Workspace:
        with self._lock:
            workspace = self.get_workspace(workspace_id)
            self._ensure_security(workspace_id, "copy_workspace")
            shutil.copytree(workspace.root_path, destination_path, dirs_exist_ok=True)
            self._emit_event("workspace.copied", workspace_id, {"destination_path": destination_path})
            return workspace

    def get_workspace(self, workspace_id: str) -> Workspace | None:
        try:
            return self._registry.get(workspace_id)
        except Exception:
            return None

    def list_workspaces(self) -> list[Workspace]:
        return self._registry.list()

    def create_file(self, workspace_id: str, relative_path: str, content: str = "", binary: bool = False, encoding: str | None = None) -> Path:
        workspace = self.get_workspace(workspace_id)
        self._ensure_security(workspace_id, "create_file")
        start = time.time()
        try:
            path = self._workspace_root(workspace) / relative_path
            path.parent.mkdir(parents=True, exist_ok=True)
            if binary:
                path.write_bytes(content.encode(encoding or "utf-8") if isinstance(content, str) else content)
            else:
                path.write_text(content, encoding=encoding or self._configurations.get(workspace_id, self._get_configuration(workspace_id)).metadata.get("encoding", "utf-8"))
            self._emit_event("file.created", workspace_id, {"path": str(path)})
            self._record_operation(workspace_id, "write_file", time.time() - start)
            return path
        except Exception as error:
            self._record_operation(workspace_id, "write_file", time.time() - start, error=str(error))
            raise

    def delete_file(self, workspace_id: str, relative_path: str) -> None:
        workspace = self.get_workspace(workspace_id)
        self._ensure_security(workspace_id, "delete_file")
        start = time.time()
        try:
            path = self._workspace_root(workspace) / relative_path
            if path.exists():
                path.unlink()
            self._emit_event("file.deleted", workspace_id, {"path": str(path)})
            self._record_operation(workspace_id, "delete_file", time.time() - start)
        except Exception as error:
            self._record_operation(workspace_id, "delete_file", time.time() - start, error=str(error))
            raise

    def rename_file(self, workspace_id: str, old_relative_path: str, new_relative_path: str) -> Path:
        workspace = self.get_workspace(workspace_id)
        self._ensure_security(workspace_id, "rename_file")
        start = time.time()
        try:
            old_path = self._workspace_root(workspace) / old_relative_path
            new_path = self._workspace_root(workspace) / new_relative_path
            old_path.rename(new_path)
            self._emit_event("file.renamed", workspace_id, {"from": str(old_path), "to": str(new_path)})
            self._record_operation(workspace_id, "rename_file", time.time() - start)
            return new_path
        except Exception as error:
            self._record_operation(workspace_id, "rename_file", time.time() - start, error=str(error))
            raise

    def move_file(self, workspace_id: str, old_relative_path: str, new_relative_path: str) -> Path:
        return self.rename_file(workspace_id, old_relative_path, new_relative_path)

    def copy_file(self, workspace_id: str, old_relative_path: str, new_relative_path: str) -> Path:
        workspace = self.get_workspace(workspace_id)
        self._ensure_security(workspace_id, "copy_file")
        start = time.time()
        try:
            old_path = self._workspace_root(workspace) / old_relative_path
            new_path = self._workspace_root(workspace) / new_relative_path
            new_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(old_path, new_path)
            self._emit_event("file.copied", workspace_id, {"from": str(old_path), "to": str(new_path)})
            self._record_operation(workspace_id, "copy_file", time.time() - start)
            return new_path
        except Exception as error:
            self._record_operation(workspace_id, "copy_file", time.time() - start, error=str(error))
            raise

    def read_file(self, workspace_id: str, relative_path: str, binary: bool = False, encoding: str | None = None) -> str | bytes:
        workspace = self.get_workspace(workspace_id)
        self._ensure_security(workspace_id, "read_file")
        start = time.time()
        try:
            path = self._workspace_root(workspace) / relative_path
            if binary:
                payload = path.read_bytes()
            else:
                payload = path.read_text(encoding=encoding or self._configurations.get(workspace_id, self._get_configuration(workspace_id)).metadata.get("encoding", "utf-8"))
            self._record_operation(workspace_id, "read_file", time.time() - start)
            return payload
        except Exception as error:
            self._record_operation(workspace_id, "read_file", time.time() - start, error=str(error))
            raise

    def write_file(self, workspace_id: str, relative_path: str, content: str | bytes, binary: bool = False, encoding: str | None = None) -> Path:
        return self.create_file(workspace_id, relative_path, content if isinstance(content, str) else content.decode("utf-8"), binary=binary, encoding=encoding)

    def append_file(self, workspace_id: str, relative_path: str, content: str, encoding: str | None = None) -> Path:
        workspace = self.get_workspace(workspace_id)
        self._ensure_security(workspace_id, "append_file")
        start = time.time()
        try:
            path = self._workspace_root(workspace) / relative_path
            path.parent.mkdir(parents=True, exist_ok=True)
            with path.open("a", encoding=encoding or self._configurations.get(workspace_id, self._get_configuration(workspace_id)).metadata.get("encoding", "utf-8"), newline=self._configurations.get(workspace_id, self._get_configuration(workspace_id)).metadata.get("newline", "\n")) as handle:
                handle.write(content)
            self._emit_event("file.modified", workspace_id, {"path": str(path)})
            self._record_operation(workspace_id, "append_file", time.time() - start)
            return path
        except Exception as error:
            self._record_operation(workspace_id, "append_file", time.time() - start, error=str(error))
            raise

    def replace_contents(self, workspace_id: str, relative_path: str, content: str, encoding: str | None = None) -> Path:
        return self.create_file(workspace_id, relative_path, content, binary=False, encoding=encoding)

    def create_directory(self, workspace_id: str, relative_path: str) -> Path:
        workspace = self.get_workspace(workspace_id)
        self._ensure_security(workspace_id, "create_directory")
        start = time.time()
        try:
            path = self._workspace_root(workspace) / relative_path
            path.mkdir(parents=True, exist_ok=True)
            self._emit_event("directory.created", workspace_id, {"path": str(path)})
            self._record_operation(workspace_id, "create_directory", time.time() - start)
            return path
        except Exception as error:
            self._record_operation(workspace_id, "create_directory", time.time() - start, error=str(error))
            raise

    def delete_directory(self, workspace_id: str, relative_path: str, recursive: bool = True) -> None:
        workspace = self.get_workspace(workspace_id)
        self._ensure_security(workspace_id, "delete_directory")
        start = time.time()
        try:
            path = self._workspace_root(workspace) / relative_path
            if recursive:
                shutil.rmtree(path, ignore_errors=True)
            else:
                path.rmdir()
            self._emit_event("directory.deleted", workspace_id, {"path": str(path)})
            self._record_operation(workspace_id, "delete_directory", time.time() - start)
        except Exception as error:
            self._record_operation(workspace_id, "delete_directory", time.time() - start, error=str(error))
            raise

    def recursive_traversal(self, workspace_id: str, relative_path: str = ".") -> list[Path]:
        workspace = self.get_workspace(workspace_id)
        root = self._workspace_root(workspace) / relative_path
        return [path for path in sorted(root.rglob("*")) if path.exists()]

    def search(self, workspace_id: str, pattern: str, recursive: bool = True, extensions: list[str] | None = None) -> list[Path]:
        workspace = self.get_workspace(workspace_id)
        root = self._workspace_root(workspace)
        if recursive:
            paths = list(root.rglob(pattern))
        else:
            paths = list(root.glob(pattern))
        if extensions:
            paths = [path for path in paths if path.suffix.lower() in {ext.lower() for ext in extensions}]
        return [path for path in sorted(paths) if path.exists()]

    def get_statistics(self, workspace_id: str) -> WorkspaceStatistics:
        return self._statistics.get(workspace_id, WorkspaceStatistics())

    def get_health(self, workspace_id: str) -> dict[str, Any]:
        workspace = self.get_workspace(workspace_id)
        path = self._workspace_root(workspace)
        return {
            "status": "healthy" if path.exists() else "degraded",
            "filesystem_accessible": path.exists(),
            "integrity": "ok" if path.exists() else "missing",
            "repository_available": self._repo_metadata(workspace).get("is_git_repo", False),
        }

    def get_session(self, workspace_id: str) -> dict[str, Any] | None:
        return self._sessions.get(workspace_id)

    def list_sessions(self) -> list[dict[str, Any]]:
        return list(self._sessions.values())

    def get_active_workspace_ids(self) -> list[str]:
        return list(self._active_workspace_ids)

    def set_configuration(self, workspace_id: str, configuration: WorkspaceConfiguration) -> None:
        self._configurations[workspace_id] = configuration
        self._configuration_manager.register(Configuration(config_id=workspace_id, settings={
            "watch_enabled": configuration.watch_enabled,
            "language_detection": configuration.language_detection,
            "framework_detection": configuration.framework_detection,
            **configuration.metadata,
        }))

    def get_configuration(self, workspace_id: str) -> WorkspaceConfiguration:
        return self._load_configuration(workspace_id)
