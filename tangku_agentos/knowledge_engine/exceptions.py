from __future__ import annotations


class KnowledgeEngineError(Exception):
    """Base knowledge engine exception."""


class KnowledgeRegistryError(KnowledgeEngineError):
    """Raised when knowledge registry operations fail."""


class KnowledgeManagerError(KnowledgeEngineError):
    """Raised when knowledge manager operations fail."""


class KnowledgeProviderError(KnowledgeEngineError):
    """Raised when knowledge provider operations fail."""


class KnowledgeSourceError(KnowledgeEngineError):
    """Raised when knowledge source operations fail."""
