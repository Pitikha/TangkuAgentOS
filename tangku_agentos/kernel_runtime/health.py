"""Health monitoring for TangkuAgentOS kernel runtimes.

This module provides utilities for monitoring the health of the kernel and its
runtimes, including health checks and status reporting.
"""

from __future__ import annotations

from typing import Any, Dict, Final, List, Optional, Set


class KernelHealthMonitor:
    """Monitors the health of the kernel and its runtimes.

    This class provides methods for checking the health of the kernel and its
    runtimes, aggregating health statuses, and generating health reports.

    Attributes:
        None (stateless class).
    """

    @staticmethod
    def determine_health_status(
        runtime_states: Set[str],
        lifecycle_state: str,
    ) -> Dict[str, Any]:
        """Determines the overall health status of the kernel.

        Args:
            runtime_states: A set of runtime states (e.g., "running", "failed").
            lifecycle_state: The current lifecycle state of the kernel.

        Returns:
            A dictionary containing the health status, summary, and statuses.
        """
        if "failed" in runtime_states:
            status = "degraded"
            summary = "one or more runtimes failed"
        elif "restarting" in runtime_states:
            status = "restarting"
            summary = "runtimes are restarting"
        elif "running" in runtime_states or lifecycle_state == "running":
            status = "healthy"
            summary = "all runtimes healthy"
        else:
            status = "stopped"
            summary = "kernel is stopped"

        return {
            "status": status,
            "summary": summary,
            "statuses": sorted(runtime_states),
        }

    @staticmethod
    def get_health(
        runtime_states: Dict[str, str],
        lifecycle_state: str,
    ) -> Dict[str, Any]:
        """Generates a health report for the kernel.

        Args:
            runtime_states: A dictionary mapping runtime IDs to their states.
            lifecycle_state: The current lifecycle state of the kernel.

        Returns:
            A dictionary containing the health status, summary, and statuses.
        """
        if not runtime_states:
            return {"status": "healthy", "summary": "no runtimes registered"}

        states: Set[str] = set(runtime_states.values())
        return KernelHealthMonitor.determine_health_status(states, lifecycle_state)
