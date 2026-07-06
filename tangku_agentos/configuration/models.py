from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict


@dataclass(frozen=True)
class Configuration:
    config_id: str
    settings: Dict[str, Any] = field(default_factory=dict)
