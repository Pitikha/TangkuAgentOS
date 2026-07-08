# 📖 TangkuAgentOS Runtime Integration Guide

## 🎯 **Purpose**

This guide provides step-by-step instructions for integrating existing TangkuAgentOS runtimes with the **Runtime Communication Framework**, making it the **central nervous system** of the entire platform.

**Goal:** Every runtime communicates **ONLY** through the Runtime Communication Framework. No runtime should directly call another runtime.

---

## 🚀 **Quick Start**

### **For New Runtimes (Recommended)**

```python
from tangku_agentos.runtime_communication.integration import (
    BaseRuntime,
    RuntimeConfig,
    create_runtime_capabilities,
    SystemEvents,
    SystemCommands,
    SystemQueries,
)

class MyRuntime(BaseRuntime):
    def __init__(self):
        config = RuntimeConfig(
            runtime_id="my_runtime",
            name="My Runtime",
            version="1.0.0",
            description="My runtime description",
            capabilities={"my_capability"},
        )
        capabilities = create_runtime_capabilities(
            can_handle_commands=True,
            can_handle_queries=True,
            can_publish_events=True,
        )
        super().__init__(config, capabilities)

    async def _initialize(self) -> None:
        # Initialize runtime-specific components
        self._data = {}

    async def _start(self) -> None:
        # Start runtime-specific components
        pass

    async def _stop(self) -> None:
        # Stop runtime-specific components
        pass

    async def handle_command(self, command: Command) -> Any:
        # Handle incoming commands
        if command.command_type == "do_something":
            return await self._do_something(command)
        raise ValueError(f"Unknown command: {command.command_type}")

    async def handle_query(self, query: Query) -> Any:
        # Handle incoming queries
        if query.query_type == "get_info":
            return await self._get_info(query)
        raise ValueError(f"Unknown query: {query.query_type}")

# Usage
runtime = MyRuntime()
await runtime.initialize()
await runtime.start()

# Send a command to another runtime
result = await runtime.send_command(
    target_runtime_id="other_runtime",
    command_type="do_something",
    payload={"param": "value"}
)

# Publish an event
await runtime.publish_event(
    event_type="something.happened",
    payload={"data": "value"}
)
```

---

## 🔄 **Integration Approaches**

### **Approach 1: Full Integration (Recommended for New Runtimes)**

Inherit from `BaseRuntime` and implement all required methods.

**Pros:**
- Full access to all framework features
- Automatic registration and lifecycle management
- Built-in health monitoring
- Standard event publishing

**Cons:**
- Requires modifying runtime class hierarchy

**Steps:**
1. Make runtime inherit from `BaseRuntime`
2. Implement `_initialize()`, `_start()`, `_stop()`
3. Implement `handle_command()`, `handle_query()`
4. Replace direct calls with bus-based communication
5. Use standard events, commands, and queries

### **Approach 2: Mixin Integration (Recommended for Existing Runtimes)**

Use `RuntimeIntegrationMixin` to add communication capabilities to existing runtimes.

**Pros:**
- Minimal changes to existing code
- Gradual migration possible
- Maintains existing class hierarchy

**Cons:**
- Less integrated than full inheritance
- Manual initialization required

**Steps:**
1. Add `RuntimeIntegrationMixin` to runtime class
2. Call `initialize_communication()` during startup
3. Use mixin methods for communication
4. Gradually replace direct calls

### **Approach 3: Adapter Integration (For Legacy Runtimes)**

Use `LegacyRuntimeAdapter` to wrap existing runtimes.

**Pros:**
- Zero changes to existing runtime code
- Complete backward compatibility
- Can be removed after full migration

**Cons:**
- Additional indirection layer
- Less type-safe

**Steps:**
1. Create adapter for legacy runtime
2. Configure buses and services
3. Start the adapter
4. Legacy runtime methods are automatically routed through framework

---

## 📋 **Step-by-Step Integration Process**

### **Step 1: Choose Integration Approach**

Decide which approach to use based on your runtime's needs:
- **New runtimes:** Use Approach 1 (Full Integration)
- **Existing runtimes with minimal changes:** Use Approach 2 (Mixin Integration)
- **Legacy runtimes that can't be modified:** Use Approach 3 (Adapter Integration)

### **Step 2: Set Up Dependencies**

Ensure your runtime has access to the Runtime Communication Framework:

```python
# In your runtime's __init__.py or main module
from tangku_agentos.runtime_communication.integration import (
    BaseRuntime,
    RuntimeConfig,
    create_runtime_capabilities,
    SystemEvents,
    SystemCommands,
    SystemQueries,
)
```

### **Step 3: Define Runtime Configuration**

Create a configuration for your runtime:

```python
from tangku_agentos.runtime_communication.integration import create_runtime_config

config = create_runtime_config(
    runtime_id="my_runtime",
    name="My Runtime",
    version="1.0.0",
    description="Description of my runtime",
    capabilities={"capability1", "capability2"},
    dependencies=["dependency1", "dependency2"],
    auto_start=True,
    timeout=30.0,
    max_retries=3,
    metadata={"custom_key": "custom_value"},
)
```

### **Step 4: Define Runtime Capabilities**

Define what your runtime can do:

```python
from tangku_agentos.runtime_communication.integration import create_runtime_capabilities

capabilities = create_runtime_capabilities(
    can_handle_commands=True,
    can_handle_queries=True,
    can_publish_events=True,
    can_subscribe_events=True,
    can_broadcast=True,
    can_stream=False,  # Only if runtime supports streaming
    can_execute_tasks=True,
    supports_health_checks=True,
    supports_metrics=True,
    supports_tracing=True,
)
```

### **Step 5: Implement Runtime Class**

#### **Option A: Full Integration (Inherit from BaseRuntime)**

```python
from tangku_agentos.runtime_communication.integration import BaseRuntime

class MyRuntime(BaseRuntime):
    def __init__(self, config: RuntimeConfig):
        super().__init__(config, capabilities)
        # Initialize runtime-specific state
        self._state = {}

    async def _initialize(self) -> None:
        """Initialize runtime-specific components."""
        # Initialize databases, connections, etc.
        self._database = await connect_to_database()

    async def _start(self) -> None:
        """Start runtime-specific components."""
        # Start background tasks, listeners, etc.
        self._background_task = asyncio.create_task(self._background_loop())

    async def _stop(self) -> None:
        """Stop runtime-specific components."""
        # Stop background tasks, close connections, etc.
        if hasattr(self, "_background_task"):
            self._background_task.cancel()
            try:
                await self._background_task
            except asyncio.CancelledError:
                pass

    async def handle_command(self, command: Command) -> Any:
        """Handle incoming commands."""
        if command.command_type == "save_data":
            return await self._handle_save_data(command)
        elif command.command_type == "delete_data":
            return await self._handle_delete_data(command)
        else:
            raise ValueError(f"Unknown command: {command.command_type}")

    async def handle_query(self, query: Query) -> Any:
        """Handle incoming queries."""
        if query.query_type == "get_data":
            return await self._handle_get_data(query)
        elif query.query_type == "search_data":
            return await self._handle_search_data(query)
        else:
            raise ValueError(f"Unknown query: {query.query_type}")

    async def _handle_save_data(self, command: Command) -> Any:
        """Handle save data command."""
        payload = command.payload or {}
        data_id = payload.get("data_id")
        data = payload.get("data")
        
        # Save data
        await self._database.save(data_id, data)
        
        # Publish event
        await self.publish_event("data.saved", {"data_id": data_id})
        
        return {"success": True, "data_id": data_id}

    async def _handle_get_data(self, query: Query) -> Any:
        """Handle get data query."""
        payload = query.payload or {}
        data_id = payload.get("data_id")
        
        # Get data
        data = await self._database.get(data_id)
        
        return {"data_id": data_id, "data": data}
```

#### **Option B: Mixin Integration (Add to Existing Runtime)**

```python
from tangku_agentos.runtime_communication.integration import RuntimeIntegrationMixin

class MyExistingRuntime(RuntimeIntegrationMixin):
    def __init__(self):
        super().__init__(
            runtime_id="my_runtime",
            name="My Runtime",
            version="1.0.0",
        )
        # Existing runtime initialization
        self._state = {}

    async def start(self) -> None:
        # Initialize communication
        await self.initialize_communication()
        
        # Existing startup code
        self._database = await connect_to_database()

    async def stop(self) -> None:
        # Clean up communication
        await self.cleanup_communication()
        
        # Existing shutdown code
        await self._database.close()

    async def do_something(self, param: str) -> Any:
        # Instead of direct call, send command through framework
        result = await self.send_command(
            target_runtime_id="other_runtime",
            command_type="do_something",
            payload={"param": param}
        )
        return result
```

#### **Option C: Adapter Integration (Wrap Legacy Runtime)**

```python
from tangku_agentos.runtime_communication.integration import LegacyRuntimeAdapter

# Existing legacy runtime (cannot be modified)
class LegacyMemoryRuntime:
    def save(self, data_id: str, data: Any) -> bool:
        # Legacy save implementation
        return True
    
    def load(self, data_id: str) -> Any:
        # Legacy load implementation
        return None

# Wrap with adapter
adapter = LegacyRuntimeAdapter(
    legacy_runtime=LegacyMemoryRuntime(),
    runtime_id="memory_runtime",
    name="Memory Runtime",
    type="memory",
    version="1.0.0",
    capabilities={"memory", "storage"},
)

# Start the adapter
await adapter.start()

# Now the legacy runtime can receive commands and queries
# Commands are automatically mapped to legacy methods
# Example: "save" command -> legacy_runtime.save()
```

### **Step 6: Replace Direct Communication**

Replace all direct runtime-to-runtime calls with bus-based communication:

**Before (Direct Call):**
```python
# Direct method call
result = other_runtime.process_data(data)
```

**After (Bus-Based):**
```python
# Send command through CommandBus
result = await self.send_command(
    target_runtime_id="other_runtime",
    command_type="process_data",
    payload={"data": data}
)
```

**Common Patterns:**

| Old Pattern | New Pattern | Bus to Use |
|-------------|-------------|------------|
| `other_runtime.method()` | `send_command()` | CommandBus |
| `other_runtime.query()` | `send_query()` | QueryBus |
| `other_runtime.notify()` | `publish_event()` | EventBus |
| `other_runtime.broadcast()` | `broadcast()` | BroadcastBus |
| `other_runtime.request()` | `request_response()` | RequestResponseBus |

### **Step 7: Use Standard System Events**

Publish standard system events for lifecycle and important operations:

```python
from tangku_agentos.runtime_communication.integration import SystemEvents

# Publish runtime-specific events
await self.publish_event(
    SystemEvents.runtime_started(
        runtime_id=self.runtime_id,
        name=self.config.name,
        type=self._get_runtime_type(),
        version=self.config.version,
    ).to_event()
)

# Publish memory events
await self.publish_event(
    SystemEvents.memory_saved(
        runtime_id=self.runtime_id,
        memory_id="mem_123",
        size=1024,
    ).to_event()
)

# Publish workflow events
await self.publish_event(
    SystemEvents.workflow_started(
        runtime_id=self.runtime_id,
        workflow_id="workflow_123",
        workflow_type="data_processing",
    ).to_event()
)
```

### **Step 8: Use Standard System Commands**

Send standard system commands to other runtimes:

```python
from tangku_agentos.runtime_communication.integration import SystemCommands

# Send runtime commands
await self.command_bus.send(
    SystemCommands.StartRuntime(
        target_runtime_id="other_runtime",
        sender_id=self.runtime_id,
    ).to_command()
)

# Send model commands
await self.command_bus.send(
    SystemCommands.LoadModel(
        target_runtime_id="model_runtime",
        sender_id=self.runtime_id,
        model_id="model_123",
        model_name="My Model",
        model_type="llm",
    ).to_command()
)

# Send workflow commands
await self.command_bus.send(
    SystemCommands.ExecuteWorkflow(
        target_runtime_id="workflow_engine",
        sender_id=self.runtime_id,
        workflow_id="workflow_123",
        input_data={"param": "value"},
    ).to_command()
)
```

### **Step 9: Use Standard System Queries**

Send standard system queries to other runtimes:

```python
from tangku_agentos.runtime_communication.integration import SystemQueries

# Query runtime status
result = await self.query_bus.ask(
    SystemQueries.GetRuntimeStatus(
        target_runtime_id="other_runtime",
        sender_id=self.runtime_id,
    ).to_query()
)

# Query loaded models
models = await self.query_bus.ask(
    SystemQueries.GetLoadedModels(
        target_runtime_id="model_runtime",
        sender_id=self.runtime_id,
    ).to_query()
)

# Query memory
memory = await self.query_bus.ask(
    SystemQueries.GetMemory(
        target_runtime_id="memory_engine",
        sender_id=self.runtime_id,
        memory_id="mem_123",
    ).to_query()
)
```

### **Step 10: Register with Kernel**

Register your runtime with the Kernel Runtime Manager:

```python
from tangku_agentos.kernel_runtime.integration import RuntimeOrchestrator

# Get the orchestrator (usually injected or singleton)
orchestrator = RuntimeOrchestrator()

# Register your runtime
await orchestrator.register_runtime(my_runtime)

# Start your runtime
await orchestrator.start_runtime(my_runtime.runtime_id)
```

### **Step 11: Implement Health Checks**

Implement health checks for your runtime:

```python
async def _initialize(self) -> None:
    # Register health checks
    from tangku_agentos.runtime_communication import HealthCheck, HealthStatus
    
    async def database_health_check(runtime_id: str) -> HealthCheckResult:
        try:
            # Check database connection
            if await self._database.ping():
                return HealthCheckResult(
                    runtime_id=runtime_id,
                    check_name="database",
                    status=HealthStatus.HEALTHY,
                    message="Database connection OK",
                    passed=True,
                )
            else:
                return HealthCheckResult(
                    runtime_id=runtime_id,
                    check_name="database",
                    status=HealthStatus.UNHEALTHY,
                    message="Database connection failed",
                    passed=False,
                )
        except Exception as e:
            return HealthCheckResult(
                runtime_id=runtime_id,
                check_name="database",
                status=HealthStatus.UNHEALTHY,
                message=f"Database error: {e}",
                passed=False,
            )
    
    check = HealthCheck(
        name="database",
        description="Check database connection",
        check_func=database_health_check,
        interval=30.0,
        timeout=5.0,
        critical=True,
    )
    
    self.health_service.register_check(self.runtime_id, check)
```

### **Step 12: Test Integration**

Test that your runtime is properly integrated:

```python
# Test command handling
result = await runtime.send_command(
    target_runtime_id=runtime.runtime_id,
    command_type="save_data",
    payload={"data_id": "test_123", "data": {"key": "value"}}
)
assert result["success"] is True

# Test query handling
result = await runtime.send_query(
    target_runtime_id=runtime.runtime_id,
    query_type="get_data",
    payload={"data_id": "test_123"}
)
assert result["data_id"] == "test_123"

# Test event publishing
await runtime.publish_event(
    event_type="test.event",
    payload={"message": "test"}
)

# Test registration
assert runtime.registry.get(runtime.runtime_id) is not None

# Test health
assert await runtime.is_runtime_healthy(runtime.runtime_id) is True
```

---

## 📁 **Runtime-Specific Integration Guides**

### **1. Kernel Runtime Integration**

The Kernel Runtime is the **orchestrator** and has special responsibilities:

```python
from tangku_agentos.kernel_runtime.integration import (
    KernelCommunicator,
    KernelRuntimeManager,
    RuntimeOrchestrator,
)

class KernelRuntime:
    def __init__(self):
        # Initialize the orchestrator
        self.orchestrator = RuntimeOrchestrator()

    async def initialize(self) -> None:
        # Initialize the orchestrator
        await self.orchestrator.initialize()

    async def start(self) -> None:
        # Start the orchestrator
        await self.orchestrator.start()

    async def register_runtime(self, runtime: BaseRuntime) -> None:
        # Register runtime with orchestrator
        await self.orchestrator.register_runtime(runtime)

    async def start_runtime(self, runtime_id: str) -> None:
        # Start runtime through orchestrator
        await self.orchestrator.start_runtime(runtime_id)

    async def stop_runtime(self, runtime_id: str) -> None:
        # Stop runtime through orchestrator
        await self.orchestrator.stop_runtime(runtime_id)

    async def shutdown(self) -> None:
        # Shutdown the orchestrator
        await self.orchestrator.shutdown()
```

**Kernel Responsibilities:**
- Initialize all communication buses
- Start all runtime services
- Register all runtimes
- Monitor system health
- Handle runtime failures
- Perform graceful shutdown

### **2. Memory Engine Integration**

See `memory_runtime_example.py` for a complete example.

**Key Features:**
- Save, load, delete, update, clear memory
- Search and list memories
- Publish memory events
- Handle memory commands and queries

**Integration Points:**
- Register with Kernel Runtime
- Use CommandBus for memory operations
- Use QueryBus for memory queries
- Use EventBus for memory events

### **3. Knowledge Engine Integration**

**Key Features:**
- Index, search, delete knowledge
- Sync knowledge from sources
- Publish knowledge events
- Handle knowledge commands and queries

**Example:**
```python
class KnowledgeRuntime(BaseRuntime):
    async def _initialize(self) -> None:
        # Initialize knowledge storage
        self._knowledge_store = KnowledgeStore()
        
        # Register command handlers
        self.register_command_handler("index", self._handle_index)
        self.register_command_handler("search", self._handle_search)
        
        # Register query handlers
        self.register_query_handler("get", self._handle_get)
        self.register_query_handler("search", self._handle_search_query)

    async def _handle_index(self, command: Command) -> Any:
        payload = command.payload or {}
        document_id = payload.get("document_id")
        content = payload.get("content")
        
        # Index document
        await self._knowledge_store.index(document_id, content)
        
        # Publish event
        await self.publish_event(
            SystemEvents.knowledge_indexed(
                runtime_id=self.runtime_id,
                document_id=document_id,
                source=payload.get("source", "unknown"),
                size=len(content),
            ).event_type,
            SystemEvents.knowledge_indexed(
                runtime_id=self.runtime_id,
                document_id=document_id,
                source=payload.get("source", "unknown"),
                size=len(content),
            ).metadata,
        )
        
        return {"success": True, "document_id": document_id}
```

### **4. Workflow Engine Integration**

**Key Features:**
- Execute, pause, resume, cancel workflows
- Track workflow state and history
- Publish workflow events
- Handle workflow commands and queries

**Example:**
```python
class WorkflowRuntime(BaseRuntime):
    async def _initialize(self) -> None:
        # Initialize workflow engine
        self._workflow_engine = WorkflowEngine()
        
        # Register command handlers
        self.register_command_handler("execute", self._handle_execute)
        self.register_command_handler("pause", self._handle_pause)
        
        # Register query handlers
        self.register_query_handler("get_state", self._handle_get_state)
        self.register_query_handler("get_history", self._handle_get_history)

    async def _handle_execute(self, command: Command) -> Any:
        payload = command.payload or {}
        workflow_id = payload.get("workflow_id")
        workflow_type = payload.get("workflow_type")
        input_data = payload.get("input_data", {})
        
        # Execute workflow
        result = await self._workflow_engine.execute(
            workflow_id, workflow_type, input_data
        )
        
        # Publish event
        await self.publish_event(
            SystemEvents.workflow_started(
                runtime_id=self.runtime_id,
                workflow_id=workflow_id,
                workflow_type=workflow_type,
                input_data=input_data,
            ).to_event()
        )
        
        return {"success": True, "workflow_id": workflow_id}
```

### **5. Provider Runtime Integration**

**Key Features:**
- Connect, disconnect, test providers
- Manage provider lifecycle
- Publish provider events
- Handle provider commands and queries

**Example:**
```python
class ProviderRuntime(BaseRuntime):
    async def _initialize(self) -> None:
        # Initialize provider manager
        self._provider_manager = ProviderManager()
        
        # Register command handlers
        self.register_command_handler("connect", self._handle_connect)
        self.register_command_handler("disconnect", self._handle_disconnect)
        
        # Register query handlers
        self.register_query_handler("get_status", self._handle_get_status)
        self.register_query_handler("list", self._handle_list)

    async def _handle_connect(self, command: Command) -> Any:
        payload = command.payload or {}
        provider_id = payload.get("provider_id")
        provider_type = payload.get("provider_type")
        config = payload.get("config", {})
        
        # Connect provider
        provider = await self._provider_manager.connect(
            provider_id, provider_type, config
        )
        
        # Publish event
        await self.publish_event(
            SystemEvents.provider_connected(
                runtime_id=self.runtime_id,
                provider_id=provider_id,
                provider_type=provider_type,
                config=config,
            ).to_event()
        )
        
        return {"success": True, "provider_id": provider_id}
```

### **6. Model Runtime Integration**

**Key Features:**
- Load, unload models
- Run inference
- Manage model lifecycle
- Publish model events
- Handle model commands and queries

**Example:**
```python
class ModelRuntime(BaseRuntime):
    async def _initialize(self) -> None:
        # Initialize model manager
        self._model_manager = ModelManager()
        
        # Register command handlers
        self.register_command_handler("load", self._handle_load)
        self.register_command_handler("unload", self._handle_unload)
        self.register_command_handler("run_inference", self._handle_run_inference)
        
        # Register query handlers
        self.register_query_handler("get_loaded", self._handle_get_loaded)
        self.register_query_handler("get_info", self._handle_get_info)

    async def _handle_load(self, command: Command) -> Any:
        payload = command.payload or {}
        model_id = payload.get("model_id")
        model_name = payload.get("model_name")
        model_type = payload.get("model_type")
        config = payload.get("config", {})
        
        # Load model
        model = await self._model_manager.load(
            model_id, model_name, model_type, config
        )
        
        # Publish event
        await self.publish_event(
            SystemEvents.model_loaded(
                runtime_id=self.runtime_id,
                model_id=model_id,
                model_name=model_name,
                model_type=model_type,
            ).to_event()
        )
        
        return {"success": True, "model_id": model_id}

    async def _handle_run_inference(self, command: Command) -> Any:
        payload = command.payload or {}
        model_id = payload.get("model_id")
        prompt = payload.get("prompt")
        parameters = payload.get("parameters", {})
        
        # Run inference
        result = await self._model_manager.run_inference(
            model_id, prompt, parameters
        )
        
        # Publish events
        await self.publish_event(
            SystemEvents.model_inference_started(
                runtime_id=self.runtime_id,
                model_id=model_id,
                inference_id=result.get("inference_id"),
            ).to_event()
        )
        
        # Return result
        return result
```

---

## 🔧 **Integration Utilities**

### **1. Command and Query Registration**

```python
# Register command handlers
runtime.register_command_handler("command_type", handler_function)

# Register query handlers
runtime.register_query_handler("query_type", handler_function)

# Register event handlers
runtime.register_event_handler("event_type", handler_function)

# Unregister handlers
runtime.unregister_command_handler("command_type")
runtime.unregister_query_handler("query_type")
runtime.unregister_event_handler("event_type")
```

### **2. Sending Messages**

```python
# Send command
result = await runtime.send_command(
    target_runtime_id="target",
    command_type="command_type",
    payload={"key": "value"},
    timeout=30.0,
    priority="high",
)

# Send query
result = await runtime.send_query(
    target_runtime_id="target",
    query_type="query_type",
    payload={"key": "value"},
    timeout=30.0,
    priority="normal",
)

# Publish event
await runtime.publish_event(
    event_type="event_type",
    payload={"key": "value"},
    priority="normal",
)

# Broadcast message
count = await runtime.broadcast(
    broadcast_type="broadcast_type",
    payload={"key": "value"},
    channels=["channel1", "channel2"],
    priority="normal",
)

# Send generic message
await runtime.send_message(
    target_runtime_id="target",
    message_type=MessageType.COMMAND,
    payload={"key": "value"},
)
```

### **3. Using Standard System Components**

```python
from tangku_agentos.runtime_communication.integration import (
    SystemEvents,
    SystemCommands,
    SystemQueries,
)

# Publish standard event
await runtime.event_bus.publish(
    SystemEvents.memory_updated(
        runtime_id=runtime.runtime_id,
        operation="save",
        memory_id="mem_123",
    ).to_event()
)

# Send standard command
await runtime.command_bus.send(
    SystemCommands.SaveMemory(
        target_runtime_id="memory_engine",
        sender_id=runtime.runtime_id,
        memory_id="mem_123",
        data={"key": "value"},
    ).to_command()
)

# Send standard query
result = await runtime.query_bus.ask(
    SystemQueries.GetMemory(
        target_runtime_id="memory_engine",
        sender_id=runtime.runtime_id,
        memory_id="mem_123",
    ).to_query()
)
```

### **4. Accessing Services**

```python
# Access runtime registry
runtime_info = runtime.registry.get("runtime_id")
all_runtimes = runtime.registry.list_all()

# Access health service
health = runtime.health_service.get_health("runtime_id")
runtime.health_service.register_check("runtime_id", health_check)

# Access discovery service
runtimes = runtime.discovery_service.discover(
    type="memory",
    capability="storage",
)

# Access status manager
status = runtime.status_manager.get_status("runtime_id")

# Access metadata registry
metadata = runtime.metadata_registry.get_metadata("runtime_id")

# Access context manager
context = runtime.context_manager.get_context("context_id")

# Access session manager
session = runtime.session_manager.get_session("session_id")
```

---

## 🛡️ **Error Handling**

### **1. Handling Command Errors**

```python
async def handle_command(self, command: Command) -> Any:
    try:
        if command.command_type == "save":
            return await self._handle_save(command)
        elif command.command_type == "load":
            return await self._handle_load(command)
        else:
            raise ValueError(f"Unknown command: {command.command_type}")
    except ValueError as e:
        # Validation error
        raise MessageValidationError(str(e)) from e
    except RuntimeError as e:
        # Runtime error
        raise RuntimeError(f"Runtime error: {e}") from e
    except Exception as e:
        # Unexpected error
        logger.error(f"Error handling command {command.command_type}: {e}")
        raise
```

### **2. Handling Query Errors**

```python
async def handle_query(self, query: Query) -> Any:
    try:
        if query.query_type == "get":
            return await self._handle_get(query)
        elif query.query_type == "search":
            return await self._handle_search(query)
        else:
            raise ValueError(f"Unknown query: {query.query_type}")
    except ValueError as e:
        # Validation error
        raise MessageValidationError(str(e)) from e
    except Exception as e:
        # Unexpected error
        logger.error(f"Error handling query {query.query_type}: {e}")
        raise
```

### **3. Handling Timeouts**

```python
async def send_command_with_timeout(self, target: str, command_type: str, payload: dict) -> Any:
    try:
        return await asyncio.wait_for(
            self.send_command(target, command_type, payload),
            timeout=30.0,
        )
    except asyncio.TimeoutError:
        raise MessageTimeoutError(
            f"Command {command_type} to {target} timed out"
        )
```

### **4. Handling Retries**

```python
async def send_command_with_retry(self, target: str, command_type: str, payload: dict, max_retries: int = 3) -> Any:
    last_error = None
    for attempt in range(max_retries):
        try:
            return await self.send_command(target, command_type, payload)
        except Exception as e:
            last_error = e
            if attempt < max_retries - 1:
                await asyncio.sleep(1.0 * (2 ** attempt))  # Exponential backoff
    raise last_error
```

---

## 📊 **Monitoring and Observability**

### **1. Metrics Collection**

```python
# Get runtime metrics
metrics = runtime.get_metrics()

# Get bus metrics
bus_metrics = runtime.message_bus.get_metrics()

# Get service metrics
health_metrics = runtime.health_service.get_metrics()
```

### **2. Health Checks**

```python
# Register health check
from tangku_agentos.runtime_communication import HealthCheck, HealthStatus

async def database_health_check(runtime_id: str) -> HealthCheckResult:
    try:
        if await database.ping():
            return HealthCheckResult(
                runtime_id=runtime_id,
                check_name="database",
                status=HealthStatus.HEALTHY,
                message="Database connection OK",
                passed=True,
            )
        else:
            return HealthCheckResult(
                runtime_id=runtime_id,
                check_name="database",
                status=HealthStatus.UNHEALTHY,
                message="Database connection failed",
                passed=False,
            )
    except Exception as e:
        return HealthCheckResult(
            runtime_id=runtime_id,
            check_name="database",
            status=HealthStatus.UNHEALTHY,
            message=f"Database error: {e}",
            passed=False,
        )

check = HealthCheck(
    name="database",
    description="Check database connection",
    check_func=database_health_check,
    interval=30.0,
    timeout=5.0,
    critical=True,
)

runtime.health_service.register_check(runtime.runtime_id, check)
```

### **3. Logging**

```python
# Structured logging is built into the framework
# All important operations are automatically logged

# Custom logging
import logging
logger = logging.getLogger(__name__)

logger.info(f"Runtime {runtime.runtime_id} started")
logger.error(f"Error processing command: {error}")
logger.debug(f"Processing query: {query.query_type}")
```

### **4. Tracing**

```python
# Tracing is automatically added to all messages
# Each message has:
# - trace_id: Unique trace identifier
# - correlation_id: Links related messages
# - timestamp: When message was sent

# Custom tracing
from tangku_agentos.runtime_communication import TraceContextManager

tracer = TraceContextManager()
context = tracer.start_trace(
    operation="process_command",
    runtime_id=runtime.runtime_id,
)

# Add spans
context.add_span(
    name="validate_command",
    start_time=time.time(),
    end_time=time.time() + 0.1,
)

# End trace
context.end_trace()
```

---

## 🔄 **Migration Strategies**

### **1. Big Bang Migration**

**Description:** Migrate all runtimes at once.

**Pros:**
- Clean slate
- No compatibility issues
- Simpler testing

**Cons:**
- High risk
- Long downtime
- All-or-nothing

**Steps:**
1. Implement new framework
2. Migrate all runtimes
3. Test thoroughly
4. Deploy all at once

### **2. Gradual Migration (Recommended)**

**Description:** Migrate runtimes one by one.

**Pros:**
- Lower risk
- Can test each runtime individually
- Can roll back if issues

**Cons:**
- Need backward compatibility
- More complex testing

**Steps:**
1. Implement new framework
2. Add backward compatibility layer
3. Migrate runtimes one by one
4. Test each runtime
5. Remove backward compatibility after all runtimes are migrated

### **3. Parallel Migration**

**Description:** Run old and new systems in parallel.

**Pros:**
- Zero downtime
- Can compare results
- Easy rollback

**Cons:**
- Double resource usage
- Complex synchronization
- Need to handle duplicate messages

**Steps:**
1. Implement new framework
2. Deploy alongside old system
3. Route some traffic to new system
4. Compare results
5. Gradually increase traffic to new system
6. Shut down old system

---

## 🧪 **Testing Integration**

### **1. Unit Testing**

```python
import pytest
from unittest.mock import AsyncMock, MagicMock

@pytest.mark.asyncio
async def test_command_handling():
    # Create runtime
    runtime = MyRuntime(config)
    
    # Mock dependencies
    runtime.command_bus = MagicMock()
    runtime.event_bus = MagicMock()
    
    # Test command handling
    command = Command(
        command_type="save",
        payload={"data_id": "test", "data": {"key": "value"}},
    )
    
    result = await runtime.handle_command(command)
    
    assert result["success"] is True
    assert result["data_id"] == "test"
    runtime.event_bus.publish.assert_called_once()
```

### **2. Integration Testing**

```python
@pytest.mark.asyncio
async def test_runtime_integration():
    # Create orchestrator
    orchestrator = RuntimeOrchestrator()
    await orchestrator.initialize()
    
    # Create and register runtime
    runtime = MyRuntime(config)
    await orchestrator.register_runtime(runtime)
    await orchestrator.start_runtime(runtime.runtime_id)
    
    # Test command sending
    result = await runtime.send_command(
        target_runtime_id=runtime.runtime_id,
        command_type="save",
        payload={"data_id": "test", "data": {"key": "value"}},
    )
    
    assert result["success"] is True
    
    # Test query sending
    result = await runtime.send_query(
        target_runtime_id=runtime.runtime_id,
        query_type="get",
        payload={"data_id": "test"},
    )
    
    assert result["data_id"] == "test"
    
    # Clean up
    await orchestrator.stop_runtime(runtime.runtime_id)
    await orchestrator.shutdown()
```

### **3. End-to-End Testing**

```python
@pytest.mark.asyncio
async def test_end_to_end():
    # Create orchestrator
    orchestrator = RuntimeOrchestrator()
    await orchestrator.initialize()
    
    # Create runtimes
    runtime_a = RuntimeA(config_a)
    runtime_b = RuntimeB(config_b)
    
    # Register and start runtimes
    await orchestrator.register_all_runtimes([runtime_a, runtime_b])
    await orchestrator.start_all_runtimes()
    
    # Test communication from A to B
    result = await runtime_a.send_command(
        target_runtime_id=runtime_b.runtime_id,
        command_type="do_something",
        payload={"param": "value"},
    )
    
    assert result["success"] is True
    
    # Test event publishing
    await runtime_a.publish_event(
        event_type="test.event",
        payload={"message": "test"},
    )
    
    # Clean up
    await orchestrator.stop_all_runtimes()
    await orchestrator.shutdown()
```

---

## 📚 **Best Practices**

### **1. Runtime Design**

- **Single Responsibility:** Each runtime should have a single, well-defined responsibility
- **Loose Coupling:** Runtimes should not depend on specific implementations of other runtimes
- **High Cohesion:** Related functionality should be grouped in the same runtime
- **Stateless:** Runtimes should be stateless where possible, or externalize state
- **Idempotent:** Commands should be idempotent (can be safely retried)

### **2. Communication Design**

- **Use Appropriate Bus:** Choose the right bus for each communication pattern
  - CommandBus: For commands that change state
  - QueryBus: For queries that retrieve data
  - EventBus: For notifications and pub/sub
  - BroadcastBus: For one-to-many notifications
  - RequestResponseBus: For request/reply patterns
- **Use Standard Types:** Prefer standard system events, commands, and queries
- **Keep Payloads Small:** Message payloads should be small and focused
- **Use Correlation IDs:** Always include correlation IDs for tracing
- **Handle Timeouts:** Always specify timeouts for commands and queries

### **3. Error Handling**

- **Fail Fast:** Detect and report errors as early as possible
- **Graceful Degradation:** Handle errors gracefully without crashing
- **Retry Appropriately:** Only retry transient errors
- **Circuit Breakers:** Use circuit breakers for external dependencies
- **Dead Letter Queues:** Use DLQ for messages that repeatedly fail

### **4. Performance**

- **Async-First:** All operations should be async
- **Batch Operations:** Batch small operations where possible
- **Cache Results:** Cache frequent query results
- **Limit Concurrency:** Use semaphores to limit concurrent operations
- **Monitor Performance:** Track latency, throughput, and errors

### **5. Security**

- **Validate Inputs:** Always validate command and query payloads
- **Authenticate:** Verify sender identity for sensitive operations
- **Authorize:** Check permissions before performing operations
- **Encrypt Sensitive Data:** Encrypt sensitive data in messages
- **Audit:** Log important operations for auditing

### **6. Observability**

- **Structured Logging:** Use structured logging for all operations
- **Distributed Tracing:** Use tracing to track requests across runtimes
- **Metrics:** Collect metrics for all important operations
- **Health Checks:** Implement health checks for all runtimes
- **Alerts:** Set up alerts for critical errors and performance issues

---

## 🚨 **Troubleshooting**

### **1. Runtime Not Registered**

**Symptom:** Commands to a runtime fail with "Runtime not found"

**Causes:**
- Runtime not registered with registry
- Runtime not started
- Runtime ID is incorrect

**Solutions:**
- Check runtime registration: `runtime.registry.get(runtime_id)`
- Check runtime status: `runtime.status_manager.get_status(runtime_id)`
- Verify runtime ID: `runtime.runtime_id`
- Check runtime is started: `runtime.state == RuntimeState.RUNNING`

### **2. Command/Query Timeout**

**Symptom:** Commands or queries timeout

**Causes:**
- Target runtime is slow
- Target runtime is not responding
- Network issues
- Timeout too short

**Solutions:**
- Increase timeout: `timeout=60.0`
- Check target runtime health: `runtime.health_service.get_health(target_id)`
- Check target runtime logs
- Check network connectivity

### **3. Message Not Delivered**

**Symptom:** Messages are not being delivered

**Causes:**
- Target runtime not subscribed to event
- Target runtime not registered for command/query
- Message filtering
- Bus configuration issue

**Solutions:**
- Check target runtime subscriptions: `runtime.event_bus.list_subscriptions()`
- Check target runtime handlers: `runtime.command_bus.list_handlers()`
- Check message filtering: Verify message metadata matches filters
- Check bus configuration: Verify bus is properly configured

### **4. Memory Leaks**

**Symptom:** Memory usage grows over time

**Causes:**
- Not cleaning up resources
- Caching too much data
- Message accumulation
- Circular references

**Solutions:**
- Implement proper cleanup in `_stop()`
- Limit cache sizes
- Use weak references where appropriate
- Monitor memory usage: `runtime.get_metrics()`

### **5. Deadlocks**

**Symptom:** System hangs or becomes unresponsive

**Causes:**
- Circular dependencies between runtimes
- Lock ordering issues
- Long-running synchronous operations

**Solutions:**
- Use async operations everywhere
- Avoid synchronous I/O
- Use timeouts for all operations
- Check for circular dependencies

---

## 📖 **Glossary**

| Term | Definition |
|------|------------|n|n|n
| **Runtime** | A component in TangkuAgentOS that provides specific functionality |
| **BaseRuntime** | Base class that all runtimes should inherit from |
| **MessageBus** | Bus for direct messaging between runtimes |
| **EventBus** | Bus for publish/subscribe messaging |
| **CommandBus** | Bus for command execution |
| **QueryBus** | Bus for query/response patterns |
| **BroadcastBus** | Bus for one-to-many messaging |
| **RequestResponseBus** | Bus for request/reply patterns |
| **RuntimeRegistry** | Service for registering and discovering runtimes |
| **RuntimeDiscoveryService** | Service for discovering runtimes by criteria |
| **RuntimeHealthService** | Service for monitoring runtime health |
| **RuntimeStatusManager** | Service for tracking runtime status |
| **RuntimeMetadataRegistry** | Service for managing runtime metadata |
| **RuntimeContextManager** | Service for managing communication contexts |
| **RuntimeSessionManager** | Service for managing communication sessions |
| **SystemEvents** | Standard system events |
| **SystemCommands** | Standard system commands |
| **SystemQueries** | Standard system queries |
| **RuntimeIntegrationMixin** | Mixin for adding communication to existing runtimes |
| **LegacyRuntimeAdapter** | Adapter for wrapping legacy runtimes |
| **RuntimeOrchestrator** | Orchestrates all runtimes in the system |
| **KernelCommunicator** | Central communication hub for the kernel |
| **KernelRuntimeManager** | Manages kernel runtime lifecycle |

---

## 🎯 **Summary**

This guide provides comprehensive instructions for integrating existing TangkuAgentOS runtimes with the Runtime Communication Framework. Follow these steps to ensure all runtimes communicate through the framework:

1. **Choose Integration Approach** - Full, Mixin, or Adapter
2. **Set Up Dependencies** - Import required components
3. **Define Configuration** - Create runtime config and capabilities
4. **Implement Runtime Class** - Extend BaseRuntime or use mixin
5. **Replace Direct Communication** - Use buses for all communication
6. **Use Standard Types** - Use SystemEvents, SystemCommands, SystemQueries
7. **Register with Kernel** - Register runtime with orchestrator
8. **Implement Health Checks** - Add health monitoring
9. **Test Integration** - Verify runtime works correctly
10. **Monitor and Observe** - Add metrics, logging, and tracing

**Result:** A fully integrated TangkuAgentOS system where all runtimes communicate through the Runtime Communication Framework.

---

## 📚 **Additional Resources**

- [Runtime Communication Framework Documentation](../README.md)
- [Phase 1 Implementation Summary](../PHASE1_COMPLETE.md)
- [Integration Phase Documentation](../INTEGRATION_PHASE.md)
- [Communication Flow Diagrams](../diagrams/communication_flow.md)
- [Implementation Summary](../IMPLEMENTATION_SUMMARY.md)
- [Memory Runtime Example](./examples/memory_runtime_example.py)

---

*Generated on: July 9, 2026*
*Part of: TangkuAgentOS Runtime Communication Framework*
