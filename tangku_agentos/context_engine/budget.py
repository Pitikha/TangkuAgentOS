from __future__ import annotations

from .compressor import ContextCompressor
from .models import ContextBudget, ContextObject
from .optimizer import ContextOptimizer


class ContextBudgetManager:
    """Manage token budgeting for contexts."""

    def __init__(self, compressor: ContextCompressor | None = None, optimizer: ContextOptimizer | None = None) -> None:
        self._compressor = compressor or ContextCompressor()
        self._optimizer = optimizer or ContextOptimizer()

    def allocate(self, context: ContextObject, budget: ContextBudget | None = None) -> ContextObject:
        budget = budget or ContextBudget(max_tokens=context.configuration.max_tokens)
        if context.statistics.token_count > budget.max_tokens:
            context = self._compressor.compress(context)
        context.configuration.max_tokens = min(context.configuration.max_tokens, budget.max_tokens)
        context = self._optimizer.optimize(context)
        return context
