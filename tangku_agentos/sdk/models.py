from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Any, List


@dataclass(frozen=True)
class SDKRegistration:
    sdk_id: str
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class SDKInterface:
    name: str
    version: str
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class SDKExtensionPoint:
    extension_id: str
    description: str = ''
    metadata: Dict[str, Any] = field(default_factory=dict)
