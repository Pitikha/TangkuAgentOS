from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict


@dataclass(frozen=True)
class DecisionMetadata:
    decision_id: str = ""
    name: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
