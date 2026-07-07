from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List


@dataclass(frozen=True)
class ContextBudget:
    budget_id: str
    token_limit: int
    window_size: int
    reserved_tokens: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ContextPolicy:
    policy_id: str
    name: str
    description: str = ""
    rules: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
