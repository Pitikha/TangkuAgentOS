from __future__ import annotations


class WorkflowEngineError(Exception):
    """Base workflow engine exception."""


class WorkflowRegistryError(WorkflowEngineError):
    """Raised for workflow registry failures."""


class WorkflowManagerError(WorkflowEngineError):
    """Raised for workflow manager failures."""
