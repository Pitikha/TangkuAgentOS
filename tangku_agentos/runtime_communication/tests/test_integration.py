"""
Runtime Communication Framework - Integration Tests

This module contains integration tests for the Runtime Communication Framework.
These tests verify that all components work together correctly.

Test categories:
- Runtime integration tests
- Communication flow tests
- Event handling tests
- Error recovery tests
- Performance tests

Example usage:
    python -m pytest tangku_agentos/runtime_communication/tests/test_integration.py -v
"""

import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from tangku_agentos.runtime_communication.integration import (
    BaseRuntime,
    RuntimeConfig,
    create_runtime_capabilities,
    create_runtime_config,
    SystemEvents,
    SystemCommands,
    SystemQueries,
    RuntimeIntegrationRegistry,
    RuntimeIntegrationStatus,
)
from tangku_agentos.runtime_communication import (
    MessageBus,
    EventBus,
    CommandBus,
    QueryBus,
    RuntimeRegistry,
    RuntimeHealthService,
    RuntimeStatusManager,
    Message,
    MessageType,
    Command,
    Query,
    Event,
)


class TestRuntimeIntegration:
    """Test runtime integration with the framework."""

    @pytest.fixture
    def runtime_config(self):
        """Create a runtime configuration for testing."""
        return create_runtime_config(
            runtime_id="test_runtime",
            name="Test Runtime",
            version="1.0.0",
            description="Test runtime for integration tests",
            capabilities={"test", "integration"},
        )

    @pytest.fixture
    def runtime_capabilities(self):
        """Create runtime capabilities for testing."""
        return create_runtime_capabilities(
            can_handle_commands=True,
            can_handle_queries=True,
            can_publish_events=True,
            can_subscribe_events=True,
        )

    @pytest.fixture
    def test_runtime(self, runtime_config):
        """Create a test runtime."""
        
        class TestRuntime(BaseRuntime):
            def __init__(self, config):
                super().__init__(config, create_runtime_capabilities())
                self.command_received = None
                self.query_received = None
                self.event_received = None

            async def _initialize(self) -> None:
                pass

            async def _start(self) -> None:
                pass

            async def _stop(self) -> None:
                pass

            async def handle_command(self, command: Command) -> Any:
                self.command_received = command
                return {"success": True, "command": command.command_type}

            async def handle_query(self, query: Query) -> Any:
                self.query_received = query
                return {"success": True, "query": query.query_type}

            async def handle_event(self, event: Event) -> None:
                self.event_received = event

        return TestRuntime(runtime_config)

    @pytest.mark.asyncio
    async def test_runtime_initialization(self, test_runtime):
        """Test runtime initialization."""
        await test_runtime.initialize()
        assert test_runtime.state == test_runtime.state.INITIALIZED

    @pytest.mark.asyncio
    async def test_runtime_start(self, test_runtime):
        """Test runtime start."""
        await test_runtime.initialize()
        await test_runtime.start()
        assert test_runtime.state == test_runtime.state.RUNNING

    @pytest.mark.asyncio
    async def test_runtime_stop(self, test_runtime):
        """Test runtime stop."""
        await test_runtime.initialize()
        await test_runtime.start()
        await test_runtime.stop()
        assert test_runtime.state == test_runtime.state.STOPPED

    @pytest.mark.asyncio
    async def test_command_handling(self, test_runtime):
        """Test command handling."""
        await test_runtime.initialize()
        
        command = Command(
            message_type=MessageType.COMMAND,
            sender_id="sender",
            recipient_id=test_runtime.runtime_id,
            command_type="test_command",
            payload={"param": "value"},
        )
        
        result = await test_runtime.handle_command(command)
        assert result["success"] is True
        assert result["command"] == "test_command"
        assert test_runtime.command_received == command

    @pytest.mark.asyncio
    async def test_query_handling(self, test_runtime):
        """Test query handling."""
        await test_runtime.initialize()
        
        query = Query(
            message_type=MessageType.QUERY,
            sender_id="sender",
            recipient_id=test_runtime.runtime_id,
            query_type="test_query",
            payload={"param": "value"},
        )
        
        result = await test_runtime.handle_query(query)
        assert result["success"] is True
        assert result["query"] == "test_query"
        assert test_runtime.query_received == query

    @pytest.mark.asyncio
    async def test_event_handling(self, test_runtime):
        """Test event handling."""
        await test_runtime.initialize()
        
        event = Event(
            message_type=MessageType.EVENT,
            sender_id="sender",
            event_type="test_event",
            payload={"param": "value"},
        )
        
        await test_runtime.handle_event(event)
        assert test_runtime.event_received == event


class TestSystemEvents:
    """Test standard system events."""

    def test_system_events_creation(self):
        """Test creating system events."""
        # Test runtime events
        event = SystemEvents.runtime_started(
            runtime_id="test",
            name="Test Runtime",
            type="test",
            version="1.0.0",
        )
        assert event.event_type == "runtime.started"
        assert event.metadata["runtime_id"] == "test"
        assert event.metadata["name"] == "Test Runtime"

    def test_all_event_types(self):
        """Test that all event types can be created."""
        # This is a smoke test to ensure all event types are accessible
        event_types = [
            "runtime.registered",
            "runtime.unregistered",
            "runtime.started",
            "runtime.stopped",
            "runtime.failed",
            "kernel.started",
            "kernel.shutdown",
            "memory.updated",
            "knowledge.indexed",
            "workflow.started",
            "provider.connected",
            "model.loaded",
            "terminal.command.executed",
            "repository.indexed",
            "security.alert",
            "planning.started",
            "automation.started",
            "workspace.changed",
            "core.initialized",
            "reasoning.started",
            "coordination.task_created",
            "context.created",
            "decision.made",
            "agent.created",
            "system.startup",
        ]
        
        for event_type in event_types:
            # Just verify we can access the event type
            assert hasattr(SystemEvents, event_type.replace(".", "_"))


class TestSystemCommands:
    """Test standard system commands."""

    def test_system_commands_creation(self):
        """Test creating system commands."""
        # Test runtime commands
        command = SystemCommands.StartRuntime(
            target_runtime_id="test",
            sender_id="sender",
        )
        assert command.command_type == "runtime.start"
        assert command.target_runtime_id == "test"
        assert command.sender_id == "sender"

    def test_command_to_command_message(self):
        """Test converting command to Command message."""
        system_command = SystemCommands.StopRuntime(
            target_runtime_id="test",
            sender_id="sender",
            reason="shutdown",
        )
        
        command = system_command.to_command()
        assert command.command_type == "runtime.stop"
        assert command.recipient_id == "test"
        assert command.sender_id == "sender"
        assert "reason" in command.payload

    def test_all_command_types(self):
        """Test that all command types can be created."""
        command_types = [
            "runtime.start",
            "runtime.stop",
            "model.load",
            "workflow.execute",
            "provider.connect",
            "memory.save",
            "knowledge.search",
            "terminal.execute_command",
            "repository.sync",
            "security.authenticate",
            "planning.create_plan",
            "automation.run",
            "workspace.create",
            "reasoning.start",
            "coordination.create_task",
            "context.create",
            "decision.make",
            "agent.create",
            "system.shutdown",
        ]
        
        for cmd_type in command_types:
            # Just verify we can access the command type
            method_name = cmd_type.replace(".", "_").replace("-", "_")
            assert hasattr(SystemCommands, method_name)


class TestSystemQueries:
    """Test standard system queries."""

    def test_system_queries_creation(self):
        """Test creating system queries."""
        # Test runtime queries
        query = SystemQueries.GetRuntimeHealth(
            target_runtime_id="test",
            sender_id="sender",
        )
        assert query.query_type == "runtime.get_health"
        assert query.target_runtime_id == "test"
        assert query.sender_id == "sender"

    def test_query_to_query_message(self):
        """Test converting query to Query message."""
        system_query = SystemQueries.GetRuntimeStatus(
            target_runtime_id="test",
            sender_id="sender",
        )
        
        query = system_query.to_query()
        assert query.query_type == "runtime.get_status"
        assert query.recipient_id == "test"
        assert query.sender_id == "sender"

    def test_all_query_types(self):
        """Test that all query types can be created."""
        query_types = [
            "runtime.get_health",
            "runtime.get_status",
            "model.get_loaded",
            "workflow.get_state",
            "provider.get",
            "memory.get",
            "knowledge.search",
            "terminal.get_sessions",
            "repository.get",
            "security.get_permissions",
            "planning.get_state",
            "automation.get_state",
            "workspace.get_state",
            "reasoning.get_state",
            "coordination.get_state",
            "context.get",
            "decision.get",
            "agent.get_state",
            "system.get_state",
        ]
        
        for query_type in query_types:
            # Just verify we can access the query type
            method_name = query_type.replace(".", "_")
            assert hasattr(SystemQueries, method_name)


class TestIntegrationRegistry:
    """Test the runtime integration registry."""

    @pytest.fixture
    def registry(self):
        """Create a registry for testing."""
        return RuntimeIntegrationRegistry(
            heartbeat_interval=1.0,
            heartbeat_timeout=2.0,
            enable_monitoring=False,
        )

    @pytest.mark.asyncio
    async def test_register_runtime(self, registry):
        """Test registering a runtime."""
        info = await registry.register(
            runtime_id="test_runtime",
            name="Test Runtime",
            type="test",
            version="1.0.0",
            capabilities={"test"},
        )
        
        assert info.runtime_id == "test_runtime"
        assert info.name == "Test Runtime"
        assert info.type == "test"
        assert info.status == RuntimeIntegrationStatus.INTEGRATED

    @pytest.mark.asyncio
    async def test_unregister_runtime(self, registry):
        """Test unregistering a runtime."""
        await registry.register(
            runtime_id="test_runtime",
            name="Test Runtime",
            type="test",
        )
        
        info = await registry.unregister("test_runtime")
        assert info.runtime_id == "test_runtime"
        assert registry.get("test_runtime") is None

    @pytest.mark.asyncio
    async def test_discover_by_capability(self, registry):
        """Test discovering runtimes by capability."""
        await registry.register(
            runtime_id="runtime1",
            name="Runtime 1",
            type="test",
            capabilities={"memory", "storage"},
        )
        await registry.register(
            runtime_id="runtime2",
            name="Runtime 2",
            type="test",
            capabilities={"memory"},
        )
        await registry.register(
            runtime_id="runtime3",
            name="Runtime 3",
            type="test",
            capabilities={"search"},
        )
        
        results = registry.discover(capability="memory")
        assert len(results) == 2
        assert "runtime1" in [r.runtime_id for r in results]
        assert "runtime2" in [r.runtime_id for r in results]

    @pytest.mark.asyncio
    async def test_list_all(self, registry):
        """Test listing all runtimes."""
        await registry.register(
            runtime_id="runtime1",
            name="Runtime 1",
            type="test",
        )
        await registry.register(
            runtime_id="runtime2",
            name="Runtime 2",
            type="test",
        )
        
        all_runtimes = registry.list_all()
        assert len(all_runtimes) == 2

    @pytest.mark.asyncio
    async def test_is_registered(self, registry):
        """Test checking if a runtime is registered."""
        assert not registry.is_registered("test_runtime")
        
        await registry.register(
            runtime_id="test_runtime",
            name="Test Runtime",
            type="test",
        )
        
        assert registry.is_registered("test_runtime")

    @pytest.mark.asyncio
    async def test_is_integrated(self, registry):
        """Test checking if a runtime is integrated."""
        assert not registry.is_integrated("test_runtime")
        
        await registry.register(
            runtime_id="test_runtime",
            name="Test Runtime",
            type="test",
        )
        
        assert registry.is_integrated("test_runtime")


class TestCommunicationFlow:
    """Test communication flow between runtimes."""

    @pytest.fixture
    def message_bus(self):
        """Create a message bus for testing."""
        return MessageBus()

    @pytest.fixture
    def event_bus(self):
        """Create an event bus for testing."""
        return EventBus()

    @pytest.fixture
    def command_bus(self):
        """Create a command bus for testing."""
        return CommandBus()

    @pytest.fixture
    def query_bus(self):
        """Create a query bus for testing."""
        return QueryBus()

    @pytest.mark.asyncio
    async def test_message_bus_communication(self, message_bus):
        """Test communication through message bus."""
        messages_received = []
        
        async def handler(message: Message) -> None:
            messages_received.append(message)
        
        message_bus.subscribe("test", handler)
        
        message = Message(
            message_type=MessageType.MESSAGE,
            sender_id="sender",
            recipient_id="recipient",
            payload={"test": "data"},
        )
        
        await message_bus.send(message)
        
        # Give handler time to process
        await asyncio.sleep(0.1)
        
        assert len(messages_received) == 1
        assert messages_received[0].payload["test"] == "data"

    @pytest.mark.asyncio
    async def test_event_bus_communication(self, event_bus):
        """Test communication through event bus."""
        events_received = []
        
        async def handler(event: Event) -> None:
            events_received.append(event)
        
        event_bus.subscribe("test.event", handler)
        
        event = Event(
            message_type=MessageType.EVENT,
            sender_id="sender",
            event_type="test.event",
            payload={"test": "data"},
        )
        
        await event_bus.publish(event)
        
        # Give handler time to process
        await asyncio.sleep(0.1)
        
        assert len(events_received) == 1
        assert events_received[0].event_type == "test.event"

    @pytest.mark.asyncio
    async def test_command_bus_communication(self, command_bus):
        """Test communication through command bus."""
        commands_received = []
        
        async def handler(command: Command) -> Any:
            commands_received.append(command)
            return {"success": True}
        
        command_bus.register_handler("test.command", handler)
        
        command = Command(
            message_type=MessageType.COMMAND,
            sender_id="sender",
            recipient_id="recipient",
            command_type="test.command",
            payload={"test": "data"},
        )
        
        result = await command_bus.send(command)
        
        assert result["success"] is True
        assert len(commands_received) == 1
        assert commands_received[0].command_type == "test.command"

    @pytest.mark.asyncio
    async def test_query_bus_communication(self, query_bus):
        """Test communication through query bus."""
        queries_received = []
        
        async def handler(query: Query) -> Any:
            queries_received.append(query)
            return {"success": True, "result": "data"}
        
        query_bus.register_handler("test.query", handler)
        
        query = Query(
            message_type=MessageType.QUERY,
            sender_id="sender",
            recipient_id="recipient",
            query_type="test.query",
            payload={"test": "data"},
        )
        
        result = await query_bus.ask(query)
        
        assert result["success"] is True
        assert result["result"] == "data"
        assert len(queries_received) == 1
        assert queries_received[0].query_type == "test.query"


class TestRuntimeLifecycle:
    """Test runtime lifecycle management."""

    @pytest.fixture
    def runtime_config(self):
        """Create a runtime configuration for testing."""
        return create_runtime_config(
            runtime_id="lifecycle_test",
            name="Lifecycle Test Runtime",
            version="1.0.0",
        )

    @pytest.mark.asyncio
    async def test_full_lifecycle(self, runtime_config):
        """Test full runtime lifecycle."""
        
        class LifecycleRuntime(BaseRuntime):
            def __init__(self, config):
                super().__init__(config, create_runtime_capabilities())
                self.lifecycle_events = []

            async def _initialize(self) -> None:
                self.lifecycle_events.append("initialize")

            async def _start(self) -> None:
                self.lifecycle_events.append("start")

            async def _stop(self) -> None:
                self.lifecycle_events.append("stop")

        runtime = LifecycleRuntime(runtime_config)
        
        # Test initialization
        await runtime.initialize()
        assert runtime.state == runtime.state.INITIALIZED
        assert "initialize" in runtime.lifecycle_events
        
        # Test start
        await runtime.start()
        assert runtime.state == runtime.state.RUNNING
        assert "start" in runtime.lifecycle_events
        
        # Test stop
        await runtime.stop()
        assert runtime.state == runtime.state.STOPPED
        assert "stop" in runtime.lifecycle_events

    @pytest.mark.asyncio
    async def test_pause_resume(self, runtime_config):
        """Test pause and resume functionality."""
        
        class PauseResumeRuntime(BaseRuntime):
            def __init__(self, config):
                super().__init__(config, create_runtime_capabilities())
                self.lifecycle_events = []

            async def _initialize(self) -> None:
                pass

            async def _start(self) -> None:
                pass

            async def _stop(self) -> None:
                pass

        runtime = PauseResumeRuntime(runtime_config)
        await runtime.initialize()
        await runtime.start()
        
        # Test pause
        await runtime.pause()
        assert runtime.state == runtime.state.PAUSED
        
        # Test resume
        await runtime.resume()
        assert runtime.state == runtime.state.RUNNING

    @pytest.mark.asyncio
    async def test_restart(self, runtime_config):
        """Test restart functionality."""
        
        class RestartRuntime(BaseRuntime):
            def __init__(self, config):
                super().__init__(config, create_runtime_capabilities())
                self.start_count = 0

            async def _initialize(self) -> None:
                pass

            async def _start(self) -> None:
                self.start_count += 1

            async def _stop(self) -> None:
                pass

        runtime = RestartRuntime(runtime_config)
        await runtime.initialize()
        await runtime.start()
        
        assert runtime.start_count == 1
        
        # Test restart
        await runtime.restart()
        assert runtime.start_count == 2
        assert runtime.state == runtime.state.RUNNING


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])
