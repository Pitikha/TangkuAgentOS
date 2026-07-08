#!/usr/bin/env python3
"""
Integration tests for TangkuAgentOS.

These tests verify that the core components (Kernel, Provider Runtime, Memory Engine, Workflow Engine)
work together correctly.
"""

import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from tangku_agentos.kernel_runtime.kernel import KernelManager


@pytest.fixture
def kernel():
    """Create a fresh KernelManager instance for each test."""
    return KernelManager()


class TestKernelIntegration:
    """Test integration between kernel and other components."""

    def test_kernel_initialization_and_startup(self, kernel):
        """Test that the kernel can initialize and start."""
        kernel.initialize()
        status = kernel.startup()
        assert "kernel_id" in status
        assert "state" in status

    def test_kernel_shutdown(self, kernel):
        """Test that the kernel can shut down."""
        kernel.initialize()
        kernel.startup()
        status = kernel.shutdown()
        assert "state" in status

    def test_kernel_restart(self, kernel):
        """Test that the kernel can restart."""
        kernel.initialize()
        kernel.startup()
        kernel.shutdown()
        status = kernel.startup()  # Restart
        assert "state" in status


class TestRuntimeRegistration:
    """Test runtime registration and management."""

    def test_register_and_get_runtime(self, kernel):
        """Test registering and retrieving a runtime."""
        mock_runtime = MagicMock()
        mock_runtime.runtime_id = "test_runtime"
        mock_runtime.name = "Test Runtime"

        runtime = kernel.register_runtime(mock_runtime)
        assert runtime is not None
        assert runtime.runtime_id == "test_runtime"

        retrieved = kernel.get_runtime("test_runtime")
        assert retrieved is not None
        assert retrieved.runtime_id == "test_runtime"

    def test_unregister_runtime(self, kernel):
        """Test unregistering a runtime."""
        mock_runtime = MagicMock()
        mock_runtime.runtime_id = "test_runtime"
        mock_runtime.name = "Test Runtime"

        kernel.register_runtime(mock_runtime)
        kernel.unregister_runtime("test_runtime")

        assert kernel.get_runtime("test_runtime") is None

    def test_list_runtimes(self, kernel):
        """Test listing all runtimes."""
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

    def test_register_and_get_service(self, kernel):
        """Test registering and retrieving a service."""
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


class TestKernelDumpState:
    """Test kernel state dumping."""

    def test_dump_state(self, kernel):
        """Test dumping kernel state."""
        state = kernel.dump_state()
        assert "kernel_id" in state
        assert "state" in state
        assert "runtimes" in state
        assert "dependencies" in state
        assert "health" in state
        assert "config" in state
