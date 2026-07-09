"""
Context Ranking for TangkuAgentOS AI Foundation Framework.

This module ranks context sources by importance for optimization.
"""

from typing import Any, Dict, List
from dataclasses import dataclass


@dataclass
class RankedContext:
    """Represents a ranked context source."""
    key: str
    value: Any
    score: float


class ContextRanker:
    """Ranks context sources by importance for TangkuAgentOS."""

    def __init__(self):
        self._default_weights = {
            "session": 1.0,
            "conversation": 0.9,
            "memory": 0.8,
            "knowledge": 0.7,
            "user": 0.6,
            "system": 0.5,
        }

    async def rank(self, context: Dict[str, Any]) -> List[str]:
        """Rank context keys by importance."""
        ranked = []
        for key, value in context.items():
            score = self._calculate_score(key, value)
            ranked.append(RankedContext(key=key, value=value, score=score))
        
        # Sort by score in descending order
        ranked.sort(key=lambda x: x.score, reverse=True)
        return [item.key for item in ranked]

    def _calculate_score(self, key: str, value: Any) -> float:
        """Calculate the importance score for a context key."""
        base_score = self._default_weights.get(key, 0.5)
        
        # Adjust score based on value type and size
        if isinstance(value, str):
            # Longer strings are more important (up to a point)
            length_score = min(len(value) / 1000, 1.0)
        elif isinstance(value, list):
            # More items are more important (up to a point)
            length_score = min(len(value) / 10, 1.0)
        elif isinstance(value, dict):
            # More keys are more important (up to a point)
            length_score = min(len(value) / 5, 1.0)
        else:
            length_score = 0.5
        
        return base_score * (0.5 + length_score * 0.5)

    def set_weight(self, key: str, weight: float) -> None:
        """Set the weight for a specific context key."""
        self._default_weights[key] = weight
