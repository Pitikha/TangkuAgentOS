from __future__ import annotations

from .interfaces import ContextBuilderInterface
from .models import ContextMetadata, ContextObject, ContextPriority, ContextSegment, ContextSource


class ContextBuilder(ContextBuilderInterface):
    """Build a context object from metadata and source attributes."""

    def build(self, metadata: ContextMetadata) -> ContextObject:
        context_id = metadata.attributes.get("context_id") or metadata.segment_id or f"{metadata.source.value}-{metadata.timestamp or 'default'}"
        content = str(metadata.attributes.get("content", ""))
        segment = ContextSegment(
            segment_id=metadata.segment_id or context_id,
            content=content,
            source=metadata.source,
            priority=metadata.attributes.get("priority", ContextPriority.MEDIUM),
            metadata={"timestamp": metadata.timestamp, **metadata.attributes},
        )
        return ContextObject(
            context_id=context_id,
            segments=[segment],
            references=[],
            priority=segment.priority,
            metadata={"source": metadata.source.value, **metadata.attributes},
        )
