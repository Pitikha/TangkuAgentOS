from __future__ import annotations


class WorkspaceEngineError(Exception):
    """Base workspace engine exception."""


class WorkspaceRegistryError(WorkspaceEngineError):
    """Raised when workspace registry operations fail."""


class WorkspaceManagerError(WorkspaceEngineError):
    """Raised when workspace manager operations fail."""


class WorkspaceScannerError(WorkspaceEngineError):
    """Raised when workspace scanning fails."""


class WorkspaceIndexerError(WorkspaceEngineError):
    """Raised when workspace indexing fails."""
