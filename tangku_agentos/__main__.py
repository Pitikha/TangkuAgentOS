#!/usr/bin/env python3
"""
Main entry point for TangkuAgentOS.

This module allows TangkuAgentOS to be run as a Python module:
    python -m tangku_agentos

It initializes the AI Kernel, starts all runtimes, and provides a unified interface
for managing the system.
"""

import signal
import sys
import logging
from typing import Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def setup_signal_handlers(kernel: "KernelManager") -> None:
    """Set up signal handlers for graceful shutdown."""
    
    def handle_shutdown(signum: int, frame: Optional[object]) -> None:
        """Handle shutdown signals (SIGINT, SIGTERM)."""
        logger.info(f"Received signal {signum}, shutting down...")
        try:
            kernel.shutdown()
        except Exception as e:
            logger.error(f"Error during shutdown: {e}")
        finally:
            sys.exit(0)
    
    signal.signal(signal.SIGINT, handle_shutdown)
    signal.signal(signal.SIGTERM, handle_shutdown)


def main() -> None:
    """Main entry point for TangkuAgentOS."""
    try:
        from tangku_agentos.kernel_runtime.kernel import KernelManager
    except ImportError as e:
        logger.error(f"Failed to import KernelManager: {e}")
        sys.exit(1)
    
    # Initialize the kernel
    kernel = KernelManager()
    setup_signal_handlers(kernel)
    
    try:
        # Initialize and start the kernel
        logger.info("Initializing TangkuAgentOS...")
        kernel.initialize()
        
        logger.info("Starting TangkuAgentOS...")
        kernel.startup()
        
        # Keep the kernel running
        logger.info("TangkuAgentOS is running. Press Ctrl+C to stop.")
        # Sleep indefinitely (signal handler will handle shutdown)
        try:
            while True:
                signal.pause()
        except KeyboardInterrupt:
            pass
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        raise
    finally:
        kernel.shutdown()


if __name__ == "__main__":
    main()