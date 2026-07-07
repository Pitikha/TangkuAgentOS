from __future__ import annotations

from .interfaces import KnowledgeProvider
from .models import KnowledgeDocument, KnowledgeMetadata, KnowledgeSource, KnowledgeSourceType


class KnowledgeProviderImpl(KnowledgeProvider):
    """Create lightweight knowledge documents from registered sources."""

    def ingest(self, source: KnowledgeSource) -> KnowledgeDocument:
        metadata = KnowledgeMetadata(
            title=source.metadata.title or source.uri or source.source_id,
            source_type=source.source_type,
            tags=list(source.metadata.tags),
            attributes={"uri": source.uri, **source.metadata.attributes},
        )
        return KnowledgeDocument(
            item_id=source.source_id,
            document_id=source.source_id,
            content={"uri": source.uri, "source_type": source.source_type.value},
            metadata=metadata,
            source=source,
        )
