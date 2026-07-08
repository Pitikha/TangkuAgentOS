#!/usr/bin/env python3
"""
Basic Usage Example for TangkuAgentOS.

This example demonstrates the basic usage of TangkuAgentOS:
1. Initialize the kernel
2. Start the kernel
3. Check status
4. Shutdown the kernel
"""

from tangku_agentos.kernel_runtime.kernel import KernelManager


def main():
    """Run the basic usage example."""
    print("=== 🚀 TangkuAgentOS Basic Usage Example ===\n")

    # Step 1: Create the kernel
    print("1. Creating KernelManager...")
    kernel = KernelManager()
    print(f"   Kernel ID: {kernel._kernel_id}\n")

    # Step 2: Initialize the kernel
    print("2. Initializing kernel...")
    state = kernel.initialize()
    print(f"   Initialization complete. State: {state.get('state', 'unknown')}\n")

    # Step 3: Start the kernel
    print("3. Starting kernel...")
    status = kernel.startup()
    print(f"   Kernel started. Status: {status.get('state', 'unknown')}\n")

    # Step 4: Check kernel status
    print("4. Checking kernel status...")
    status = kernel.status()
    print(f"   Kernel ID: {status.get('kernel_id', 'N/A')}")
    print(f"   State: {status.get('state', 'unknown')}")
    print(f"   Runtime Count: {status.get('runtime_count', 0)}\n")

    # Step 5: Check health
    print("5. Checking kernel health...")
    health = kernel.health()
    print(f"   Status: {health.get('status', 'unknown')}")
    print(f"   Summary: {health.get('summary', 'No summary')}\n")

    # Step 6: List runtimes
    print("6. Listing registered runtimes...")
    runtimes = kernel.list_runtimes()
    if runtimes:
        for runtime_id in runtimes:
            runtime = kernel.get_runtime(runtime_id)
            print(f"   - {runtime_id}: {runtime.status if runtime else 'unknown'}")
    else:
        print("   No runtimes registered.")
    print()

    # Step 7: Shutdown the kernel
    print("7. Shutting down kernel...")
    kernel.shutdown()
    print("   Kernel stopped.\n")

    print("=== ✅ Example Complete ===")


if __name__ == "__main__":
    main()
