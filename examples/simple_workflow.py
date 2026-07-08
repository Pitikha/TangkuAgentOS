#!/usr/bin/env python3
"""
Simple Workflow Example for TangkuAgentOS.

This example demonstrates how to:
1. Start the TangkuAgentOS kernel
2. Register runtimes (Provider, Memory, Workflow)
3. Execute a simple workflow that:
   - Generates text using a provider
   - Stores the result in memory
   - Retrieves and prints the stored memory
"""

import asyncio
import logging
from typing import Any, Dict

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


async def main():
    """Run the simple workflow example."""
    from tangku_agentos.kernel_runtime.kernel import KernelManager
    from tangku_agentos.provider_runtime.providers import OpenAIProvider
    from tangku_agentos.memory_engine.store import MemoryStore
    from tangku_agentos.workflow_engine.models import Workflow, Task
    from tangku_agentos.workflow_engine.manager import WorkflowManager

    # Initialize the kernel
    logger.info("Initializing TangkuAgentOS...")
    kernel = KernelManager()
    kernel.initialize()

    # Create and register the Provider Runtime
    logger.info("Setting up Provider Runtime...")
    provider = OpenAIProvider(
        api_key="your-api-key",  # Replace with your API key or use environment variable
        base_url="https://api.openai.com/v1",
        default_model="gpt-3.5-turbo",
    )
    kernel.register_runtime(provider, runtime_id="openai_provider")

    # Create and register the Memory Engine
    logger.info("Setting up Memory Engine...")
    memory_store = MemoryStore()
    kernel.register_runtime(memory_store, runtime_id="memory_store")

    # Create and register the Workflow Engine
    logger.info("Setting up Workflow Engine...")
    workflow_manager = WorkflowManager()
    kernel.register_runtime(workflow_manager, runtime_id="workflow_manager")

    # Start the kernel and all runtimes
    logger.info("Starting TangkuAgentOS...")
    kernel.startup()

    try:
        # Define a simple workflow
        async def generate_text(prompt: str) -> str:
            """Generate text using the provider."""
            logger.info(f"Generating text for prompt: {prompt}")
            return await provider.generate(prompt)

        async def store_memory(content: str, memory_id: str = "example_1") -> str:
            """Store content in memory."""
            logger.info(f"Storing memory: {memory_id}")
            await memory_store.add_memory(
                memory_id=memory_id,
                content=content,
                metadata={"source": "workflow"},
            )
            return memory_id

        async def retrieve_memory(memory_id: str) -> str:
            """Retrieve content from memory."""
            logger.info(f"Retrieving memory: {memory_id}")
            memory = await memory_store.get_memory(memory_id)
            return memory.content if memory else ""

        # Create tasks for the workflow
        generate_task = Task(
            task_id="generate",
            name="Generate Text",
            function=generate_text,
            dependencies=[],
        )

        store_task = Task(
            task_id="store",
            name="Store Memory",
            function=store_memory,
            dependencies=["generate"],
        )

        retrieve_task = Task(
            task_id="retrieve",
            name="Retrieve Memory",
            function=retrieve_memory,
            dependencies=["store"],
        )

        # Create the workflow
        workflow = Workflow(
            workflow_id="simple_example",
            name="Simple Example Workflow",
            tasks={
                "generate": generate_task,
                "store": store_task,
                "retrieve": retrieve_task,
            },
        )

        # Register the workflow
        await workflow_manager.register_workflow(workflow)
        logger.info("Workflow registered successfully")

        # Execute the workflow
        logger.info("Executing workflow...")
        prompt = "What is the capital of France?"
        result = await workflow_manager.execute_workflow(
            workflow_id="simple_example",
            inputs={"prompt": prompt},
        )

        # Print the results
        logger.info("Workflow execution complete!")
        logger.info(f"Generated text: {result.get('generate', 'N/A')}")
        logger.info(f"Stored memory ID: {result.get('store', 'N/A')}")
        logger.info(f"Retrieved memory: {result.get('retrieve', 'N/A')}")

    except Exception as e:
        logger.error(f"Error during workflow execution: {e}", exc_info=True)
    finally:
        # Shutdown the kernel
        logger.info("Shutting down TangkuAgentOS...")
        kernel.shutdown()


if __name__ == "__main__":
    asyncio.run(main())
