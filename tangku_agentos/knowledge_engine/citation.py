from __future__ import annotations

from .interfaces import CitationManagerInterface
from .models import KnowledgeCitation, KnowledgeItem, KnowledgeSource


class CitationManager(CitationManagerInterface):
    """Track citations from knowledge items to their sources."""

    def __init__(self) -> None:
        self._citations: dict[str, KnowledgeCitation] = {}

    def cite(self, item: KnowledgeItem, source: KnowledgeSource) -> None:
        citation = KnowledgeCitation(
            citation_id=f"{item.item_id}-{source.source_id}",
            item_id=item.item_id,
            source_id=source.source_id,
            metadata={"title": item.metadata.title, "source_type": source.source_type.value},
        )
        self._citations[citation.citation_id] = citation
