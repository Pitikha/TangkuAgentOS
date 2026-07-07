from __future__ import annotations

from .interfaces import ContextOptimizerInterface
from .models import ContextObject, ContextPriority


class ContextOptimizer(ContextOptimizerInterface):
    """Order and de-duplicate context segments for stable assembly."""

    def optimize(self, context: ContextObject) -> ContextObject:
        priority_rank = {
            ContextPriority.CRITICAL: 0,
            ContextPriority.HIGH: 1,
            ContextPriority.MEDIUM: 2,
            ContextPriority.LOW: 3,
        }
        ordered_segments = sorted(
            context.segments,
            key=lambda segment: (priority_rank.get(segment.priority, 99), segment.segment_id),
        )
        seen: set[str] = set()
        unique_segments = []
        for segment in ordered_segments:
            if segment.segment_id in seen:
                continue
            seen.add(segment.segment_id)
            unique_segments.append(segment)
        context.segments = unique_segments
        return context
