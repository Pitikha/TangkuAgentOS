"""
Context Optimizer for TangkuAgentOS AI Foundation Framework.

This module optimizes context for AI requests by ranking, deduplicating, and compressing.
"""

from typing import Any, Optional, Dict, List
from dataclasses import dataclass
from .context_ranking import ContextRanker


@dataclass
class OptimizationResult:
    """Result of a context optimization operation."""
    original_context: Dict[str, Any]
    optimized_context: Dict[str, Any]
    removed_keys: List[str]
    compression_ratio: float


class ContextOptimizer:
    """Optimizes context for AI requests in TangkuAgentOS."""

    def __init__(self, ranker: Optional[ContextRanker] = None):
        self._ranker = ranker or ContextRanker()

    async def optimize(
        self,
        context: Dict[str, Any],
        max_tokens: int,
        **kwargs: Any,
    ) -> OptimizationResult:
        """Optimize context to fit within a token budget."""
        # Rank context keys by importance
        ranked_keys = await self._ranker.rank(context)
        
        # Calculate token usage for each key
        token_usage = {}
        for key in ranked_keys:
            token_usage[key] = self._estimate_tokens(context[key])
        
        # Select keys to keep within the budget
        selected_keys = []
        total_tokens = 0
        for key in ranked_keys:
            if total_tokens + token_usage[key] <= max_tokens:
                selected_keys.append(key)
                total_tokens += token_usage[key]
            else:
                break
        
        # Build optimized context
        optimized_context = {k: context[k] for k in selected_keys}
        removed_keys = [k for k in context if k not in selected_keys]
        
        return OptimizationResult(
            original_context=context,
            optimized_context=optimized_context,
            removed_keys=removed_keys,
            compression_ratio=total_tokens / max_tokens if max_tokens > 0 else 1.0,
        )

    def _estimate_tokens(self, value: Any) -> int:
        """Estimate the number of tokens in a value."""
        if isinstance(value, str):
            return len(value) // 4  # Rough estimate: 1 token ~ 4 characters
        elif isinstance(value, list):
            return sum(self._estimate_tokens(item) for item in value)
        elif isinstance(value, dict):
            return sum(self._estimate_tokens(v) for v in value.values())
        else:
            return 1  # Default for other types
