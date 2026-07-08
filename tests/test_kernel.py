#!/usr/bin/env python3
"""
Tests for the TangkuAgentOS Kernel.
"""

import pytest
from unittest.mock import MagicMock, patch

from tangku_agentos.kernel_runtime.kernel import KernelManager


@pytest.fixture
def kernel():
    """Create a fresh KernelManager instance for each test."""
    return KernelManager()


class TestKernelInitialization:
    """Test kernel initialization and setup."""

    def test_kernel_creation(self, kernel):
        """Test that a kernel can be created."""
        assert kernel is not None
        assert hasattr(kernel, "initialize")
        assert hasattr(kernel, "startup")
        assert hasattr(kernel, "shutdown")

    def test_kernel_id_is_unique(self):
        """Test that each kernel has a unique ID."""
        kernel1 = KernelManager()
        kernel2 = KernelManager()
        assert kernel1._kernel_id != kernel2._kernel_id

    def test_kernel_initialization(self, kernel):
        """Test kernel initialization."""
        state = kernel.initialize()
        assert "kernel_id" in state
        assert "runtimes" in state


class TestKernelLifecycle:
    """Test kernel lifecycle management."""

    def test_kernel_startup(self, kernel):
        """Test kernel startup."""
        kernel.initialize()
        state = kernel.startup()
        assert "state" in state
        assert "runtimes" in state

    def test_kernel_shutdown(self, kernel):
        """Test kernel shutdown."""
        kernel.initialize()
        kernel.startup()
        state = kernel.shutdown()
        assert "state" in state

    def test_kernel_restart(self, kernel):
        """Test kernel restart."""
        kernel.initialize()
        kernel.startup()
        state = kernel.restart()
        assert "state" in state


class TestKernelRuntimeManagement:
    """Test runtime management in the kernel."""

    def test_register_runtime(self, kernel):
        """Test registering a runtime."""
        mock_runtime = MagicMock()
        mock_runtime.runtime_id = "test_runtime"
        mock_runtime.name = "Test Runtime"

        runtime = kernel.register_runtime(mock_runtime)
        assert runtime is not None
        assert runtime.runtime_id == "test_runtime"

    def test_unregister_runtime(self, kernel):
        """Test unregistering a runtime."""
        mock_runtime = MagicMock()
        mock_runtime.runtime_id = "test_runtime"
        mock_runtime.name = "Test Runtime"

        kernel.register_runtime(mock_runtime)
        kernel.unregister_runtime("test_runtime")

        # Runtime should no longer be registered
        assert kernel.get_runtime("test_runtime") is None

    def test_get_runtime(self, kernel):
        """Test getting a registered runtime."""
        mock_runtime = MagicMock()
        mock_runtime.runtime_id = "test_runtime"
        mock_runtime.name = "Test Runtime"

        kernel.register_runtime(mock_runtime)
        runtime = kernel.get_runtime("test_runtime")
        assert runtime is not None
        assert runtime.runtime_id == "test_runtime"

    def test_list_runtimes(self, kernel):
        """Test listing all registered runtimes."""
        mock_runtime1 = MagicMock()
        mock_runtime1.runtime_id = "runtime1"
        mock_runtime2 = MagicMock()
        mock_runtime2.runtime_id = "runtime2"

        kernel.register_runtime(mock_runtime1)
        kernel.register_runtime(mock_runtime2)

        runtimes = kernel.list_runtimes()
        assert "runtime1" in runtimes
        assert "runtime2" in runtimes


class TestKernelStatus:
    """Test kernel status and health checks."""

    def test_kernel_status(self, kernel):
        """Test getting kernel status."""
        kernel.initialize()
        status = kernel.status()
        assert "kernel_id" in status
        assert "state" in status
        assert "runtimes" in status

    def test_kernel_health(self, kernel):
        """Test getting kernel health."""
        health = kernel.health()
        assert "status" in health
        assert "summary" in health

    def test_kernel_statistics(self, kernel):
        """Test getting kernel statistics."""
        stats = kernel.statistics()
        assert "kernel_id" in stats
        assert "runtime_count" in stats


class TestKernelDependencies:
    """Test kernel dependency management."""

    def test_dependencies(self, kernel):
        """Test getting dependencies."""
        deps = kernel.dependencies()
        assert isinstance(deps, dict)

    def test_dependencies_graph(self, kernel):
        """Test getting dependency graph."""
        graph = kernel.dependencies_graph()
        assert isinstance(graph, dict)


class TestKernelEventManagement:
    """Test kernel event routing."""

    def test_route_event(self, kernel):
        """Test routing an event through the kernel."""
        result = kernel.route_event("test_event", {"key": "value"})
        assert result is not None


class TestKernelServiceManagement:
    """Test kernel service management."""

    def test_register_service(self, kernel):
        """Test registering a service."""
        mock_service = MagicMock()
        kernel.register_service("test_service", mock_service)
        assert kernel.get_service("test_service") is mock_service

    def test_get_service(self, kernel):
        """Test getting a registered service."""
        mock_service = MagicMock()
        kernel.register_service("test_service", mock_service)
        service = kernel.get_service("test_service")
        assert service is mock_service

    def test_resolve_service(self, kernel):
        """Test resolving a service."""
        mock_service = MagicMock()
        kernel.register_service("test_service", mock_service)
        service = kernel.resolve_service("test_service")
        assert service is mock_service
