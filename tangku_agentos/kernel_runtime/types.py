"""Type definitions and dataclasses for TangkuAgentOS kernel runtime.

This module contains all the immutable data structures and type aliases used
throughout the kernel runtime system. These include runtime metadata, configuration,
context, health, and snapshot definitions.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Tuple


@dataclass(frozen=True)
class KernelRuntime:
    """Immutable representation of a runtime in the kernel.

    Attributes:
        runtime_id: Unique identifier for the runtime.
        name: Human-readable name of the runtime.
        status: Current status of the runtime (e.g., "registered", "running").
        metadata: Additional metadata associated with the runtime.
    """

    runtime_id: str
    name: str
    status: str = "registered"
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class KernelContext:
    """Immutable representation of a kernel context.

    Attributes:
        context_id: Unique identifier for the context.
        profile_name: Name of the profile associated with the context.
        metadata: Additional metadata associated with the context.
        runtime_ids: Tuple of runtime IDs associated with the context.
    """

    context_id: str
    profile_name: str = "default"
    metadata: Dict[str, Any] = field(default_factory=dict)
    runtime_ids: Tuple[str, ...] = ()


@dataclass(frozen=True)
class KernelConfiguration:
    """Immutable representation of kernel configuration.

    Attributes:
        configuration_id: Unique identifier for the configuration.
        profile_name: Name of the profile associated with the configuration.
        values: Dictionary of configuration values.
        bootstrap_steps: Tuple of bootstrap step names.
    """

    configuration_id: str
    profile_name: str = "default"
    values: Dict[str, Any] = field(default_factory=dict)
    bootstrap_steps: Tuple[str, ...] = (
        "config",
        "runtime-registration",
        "dependency-resolution",
        "health-check",
    )


@dataclass(frozen=True)
class KernelMetadata:
    """Immutable representation of kernel metadata.

    Attributes:
        metadata_id: Unique identifier for the metadata.
        name: Human-readable name of the metadata.
        values: Dictionary of metadata values.
        version: Version of the metadata.
    """

    metadata_id: str
    name: str
    values: Dict[str, Any] = field(default_factory=dict)
    version: str = "1.0.0"


@dataclass(frozen=True)
class KernelStatistics:
    """Immutable representation of kernel statistics.

    Attributes:
        statistics_id: Unique identifier for the statistics.
        counters: Dictionary of counter metrics.
        totals: Dictionary of total metrics.
    """

    statistics_id: str
    counters: Dict[str, int] = field(default_factory=dict)
    totals: Dict[str, int] = field(default_factory=dict)


@dataclass(frozen=True)
class KernelHealth:
    """Immutable representation of kernel health status.

    Attributes:
        health_id: Unique identifier for the health status.
        status: Current health status (e.g., "healthy", "degraded").
        summary: Human-readable summary of the health status.
        metrics: Dictionary of health metrics.
    """

    health_id: str
    status: str = "healthy"
    summary: str = "healthy"
    metrics: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class SystemSnapshot:
    """Immutable representation of a system state snapshot.

    Attributes:
        snapshot_id: Unique identifier for the snapshot.
        state_id: Unique identifier for the state.
        values: Dictionary of snapshot values.
    """

    snapshot_id: str
    state_id: str
    values: Dict[str, Any] = field(default_factory=dict)
