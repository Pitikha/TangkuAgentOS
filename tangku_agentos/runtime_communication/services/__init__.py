"""
Runtime Communication Framework - Runtime Services

This package contains service implementations for runtime management in
TangkuAgentOS. These services provide:
- Runtime discovery and lookup
- Runtime registration and metadata management
- Health monitoring and status tracking
- Context propagation
- Session management

Available services:
- RuntimeDiscoveryService: Service discovery for runtimes
- RuntimeRegistry: Runtime registration and lookup
- RuntimeHealthService: Health monitoring for runtimes
- RuntimeStatusManager: Status tracking for runtimes
- RuntimeMetadataRegistry: Metadata management for runtimes
- RuntimeContextManager: Context propagation for runtime communication
- RuntimeSessionManager: Session management for runtime communication

Example usage:
    from tangku_agentos.runtime_communication.services import (
        RuntimeDiscoveryService,
        RuntimeRegistry,
        RuntimeHealthService,
        RuntimeStatusManager,
        RuntimeMetadataRegistry,
        RuntimeContextManager,
        RuntimeSessionManager,
    )
"""

from tangku_agentos.runtime_communication.services.discovery import RuntimeDiscoveryService
from tangku_agentos.runtime_communication.services.registry import RuntimeRegistry
from tangku_agentos.runtime_communication.services.health import RuntimeHealthService
from tangku_agentos.runtime_communication.services.status import RuntimeStatusManager
from tangku_agentos.runtime_communication.services.metadata import RuntimeMetadataRegistry
from tangku_agentos.runtime_communication.services.context import RuntimeContextManager
from tangku_agentos.runtime_communication.services.session import RuntimeSessionManager

__all__ = [
    "RuntimeDiscoveryService",
    "RuntimeRegistry",
    "RuntimeHealthService",
    "RuntimeStatusManager",
    "RuntimeMetadataRegistry",
    "RuntimeContextManager",
    "RuntimeSessionManager",
]
