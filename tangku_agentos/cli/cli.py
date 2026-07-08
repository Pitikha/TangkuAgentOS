#!/usr/bin/env python3
"""
Command-line interface for TangkuAgentOS.

This module provides commands for managing TangkuAgentOS, including:
- Starting and stopping the kernel
- Checking runtime status
- Managing configurations
"""

import click
import logging
from typing import Optional, Dict, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Global kernel instance (lazy-loaded)
_kernel: Optional["KernelManager"] = None


def get_kernel() -> "KernelManager":
    """Get or create the global kernel instance."""
    global _kernel
    if _kernel is None:
        from tangku_agentos.kernel_runtime.kernel import KernelManager
        _kernel = KernelManager()
    return _kernel


@click.group()
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose logging")
def cli(verbose: bool) -> None:
    """TangkuAgentOS CLI - Manage the AI Operating System."""
    if verbose:
        logging.getLogger().setLevel(logging.DEBUG)
        logger.debug("Verbose logging enabled")


@cli.command()
@click.option("--config", "-c", type=click.Path(), help="Path to configuration file")
def start(config: Optional[str]) -> None:
    """Start TangkuAgentOS and all registered runtimes."""
    kernel = get_kernel()
    
    try:
        if config:
            # Load custom configuration
            from tangku_agentos.core_runtime.configuration import ConfigManager
            config_manager = ConfigManager()
            config_manager.load_config(config)
            kernel._config.update(config_manager.get_config())
            click.echo(f"Loaded configuration from {config}")
        
        click.echo("Initializing TangkuAgentOS...")
        kernel.initialize()
        
        click.echo("Starting TangkuAgentOS...")
        kernel.startup()
        
        click.echo("✅ TangkuAgentOS started successfully!")
        click.echo("Run 'tangku-agentos status' to check runtime status.")
    except Exception as e:
        click.echo(f"❌ Failed to start TangkuAgentOS: {e}", err=True)
        logger.error(f"Startup error: {e}", exc_info=True)
        raise click.Abort()


@cli.command()
def stop() -> None:
    """Stop TangkuAgentOS and all runtimes."""
    kernel = get_kernel()
    
    try:
        click.echo("Stopping TangkuAgentOS...")
        kernel.shutdown()
        click.echo("✅ TangkuAgentOS stopped successfully!")
    except Exception as e:
        click.echo(f"❌ Failed to stop TangkuAgentOS: {e}", err=True)
        logger.error(f"Shutdown error: {e}", exc_info=True)
        raise click.Abort()


@cli.command()
@click.option("--json", "-j", is_flag=True, help="Output status as JSON")
def status(json: bool) -> None:
    """Check the status of TangkuAgentOS and all runtimes."""
    kernel = get_kernel()
    
    try:
        status_data = kernel.status()
        
        if json:
            import json
            click.echo(json.dumps(status_data, indent=2))
        else:
            click.echo("=== TangkuAgentOS Status ===")
            click.echo(f"Kernel State: {status_data.get('state', 'unknown')}")
            click.echo(f"Number of Runtimes: {status_data.get('runtime_count', 0)}")
            click.echo("\n--- Runtime Details ---")
            for runtime_id, runtime_info in status_data.get('runtimes', {}).items():
                click.echo(f"  {runtime_id}:")
                click.echo(f"    Status: {runtime_info.get('status', 'unknown')}")
                click.echo(f"    State: {runtime_info.get('state', 'unknown')}")
                deps = runtime_info.get('dependencies', [])
                if deps:
                    click.echo(f"    Dependencies: {', '.join(deps)}")
    except Exception as e:
        click.echo(f"❌ Failed to get status: {e}", err=True)
        logger.error(f"Status error: {e}", exc_info=True)
        raise click.Abort()


@cli.command()
@click.argument("runtime_id")
def restart(runtime_id: str) -> None:
    """Restart a specific runtime."""
    kernel = get_kernel()
    
    try:
        click.echo(f"Restarting runtime: {runtime_id}")
        # Note: This assumes the kernel has a restart_runtime method
        # If not, we'll need to implement it
        if hasattr(kernel, 'restart_runtime'):
            kernel.restart_runtime(runtime_id)
        else:
            # Fallback: stop and start the runtime
            kernel.stop_runtime(runtime_id)
            kernel.start_runtime(runtime_id)
        click.echo(f"✅ Runtime '{runtime_id}' restarted successfully!")
    except Exception as e:
        click.echo(f"❌ Failed to restart runtime '{runtime_id}': {e}", err=True)
        logger.error(f"Restart error for {runtime_id}: {e}", exc_info=True)
        raise click.Abort()


@cli.command()
def health() -> None:
    """Check the health of TangkuAgentOS."""
    kernel = get_kernel()
    
    try:
        health_data = kernel.health()
        click.echo("=== TangkuAgentOS Health ===")
        click.echo(f"Status: {health_data.get('status', 'unknown')}")
        click.echo(f"Summary: {health_data.get('summary', 'No summary')}")
        
        if 'details' in health_data:
            click.echo("\n--- Runtime Health ---")
            for runtime_id, health_info in health_data['details'].items():
                click.echo(f"  {runtime_id}: {health_info.get('status', 'unknown')}")
    except Exception as e:
        click.echo(f"❌ Failed to get health status: {e}", err=True)
        logger.error(f"Health check error: {e}", exc_info=True)
        raise click.Abort()


@cli.command()
@click.option("--output", "-o", type=click.Path(), help="Save config to file")
def config(output: Optional[str]) -> None:
    """Show or save the current configuration."""
    kernel = get_kernel()
    
    try:
        config_data = kernel.dump_state()
        
        if output:
            import json
            with open(output, 'w') as f:
                json.dump(config_data, f, indent=2)
            click.echo(f"✅ Configuration saved to {output}")
        else:
            import json
            click.echo(json.dumps(config_data, indent=2))
    except Exception as e:
        click.echo(f"❌ Failed to get configuration: {e}", err=True)
        logger.error(f"Config error: {e}", exc_info=True)
        raise click.Abort()


@cli.command()
def logs() -> None:
    """Show TangkuAgentOS logs."""
    click.echo("=== TangkuAgentOS Logs ===")
    click.echo("Use 'tangku-agentos start --verbose' for detailed logs.")
    # In a real implementation, we would stream logs from the logger


@cli.command()
def version() -> None:
    """Show TangkuAgentOS version."""
    from tangku_agentos import __version__
    click.echo(f"TangkuAgentOS version: {__version__}")


if __name__ == "__main__":
    cli()
