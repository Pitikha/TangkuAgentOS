from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple, Union


Metadata = Dict[str, Any]


@dataclass(frozen=True)
class EventPayload:
    data: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class EventRecord:
    name: str
    payload: EventPayload
    timestamp: float
    metadata: Metadata = field(default_factory=dict)


ConfigValue = Union[str, int, float, bool, None, List["ConfigValue"], Dict[str, "ConfigValue"]]
ConfigKey = str
ConfigData = Dict[ConfigKey, ConfigValue]
ConfigurationSchema = Dict[str, Any]
EventHandler = Any
RegistryKey = str
RegistryValue = Any
RegistryEntry = Any
StateData = Dict[str, Any]
StateSnapshot = Dict[str, Any]
StateChangeType = str
LifecycleState = str
