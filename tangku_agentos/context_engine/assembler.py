from __future__ import annotations

from .interfaces import ContextBuilderInterface
from .models import ContextMetadata, ContextObject, ContextPriority, ContextReference, ContextSegment, ContextSource


class ContextAssembler:
    """Assemble multiple contexts into one merged context object."""

    def __init__(self, builder: ContextBuilderInterface | None = None) -> None:
        self._builder = builder

    def assemble(self, contexts: list[ContextObject], metadata: ContextMetadata | None = None) -> ContextObject:
        if not contexts:
            metadata = metadata or ContextMetadata(source=ContextSource.CONFIGURATION)
            return self._builder.build(metadata) if self._builder is not None else ContextObject(context_id="assembled")
        merged_segments: list[ContextSegment] = []
        references: list[ContextReference] = []
        for context in contexts:
            merged_segments.extend(context.segments)
            references.extend(context.references)
        priority = max(
            (context.priority for context in contexts),
            key=lambda priority: [ContextPriority.LOW, ContextPriority.MEDIUM, ContextPriority.HIGH, ContextPriority.CRITICAL].index(priority),
            default=ContextPriority.MEDIUM,
        )
        assembled = ContextObject(
            context_id=f"merged-{len(contexts)}",
            segments=merged_segments,
            references=references,
            priority=priority,
            metadata={"source": "assembled", **(metadata.attributes if metadata else {})},
        )
        return assembled
