from __future__ import annotations

from .interfaces import ContextCompressorInterface
from .models import ContextObject, ContextPriority


class ContextCompressor(ContextCompressorInterface):
    """Reduce context size by retaining only the highest-priority segments."""

    def compress(self, context: ContextObject) -> ContextObject:
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
        limit = context.configuration.max_tokens
        retained: list = []
        token_total = 0
        for segment in ordered_segments:
            segment_tokens = len(segment.content.split())
            if token_total + segment_tokens > limit:
                continue
            retained.append(segment)
            token_total += segment_tokens
        context.segments = retained
        return context
