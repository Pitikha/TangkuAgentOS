from __future__ import annotations

from .interfaces import KnowledgeStatisticsManagerInterface


class KnowledgeStatisticsManager(KnowledgeStatisticsManagerInterface):
    """Collect knowledge engine counters."""

    def __init__(self) -> None:
        self._counts: dict[str, int] = {
            "documents": 0,
            "sources": 0,
            "nodes": 0,
            "edges": 0,
            "entity_count": 0,
            "relationship_count": 0,
            "graph_size": 0,
            "search_count": 0,
            "update_count": 0,
            "traversal_count": 0,
            "cache_hits": 0,
            "cache_misses": 0,
        }

    def statistics(self) -> dict[str, int]:
        return dict(self._counts)

    def update(self, **kwargs: int) -> None:
        self._counts.update(kwargs)

    def record_search(self, count: int = 1) -> None:
        self._counts["search_count"] += count

    def record_update(self, count: int = 1) -> None:
        self._counts["update_count"] += count

    def record_cache_hit(self, count: int = 1) -> None:
        self._counts["cache_hits"] += count

    def record_cache_miss(self, count: int = 1) -> None:
        self._counts["cache_misses"] += count

    def record_entity(self, count: int = 1) -> None:
        self._counts["entity_count"] += count

    def record_relationship(self, count: int = 1) -> None:
        self._counts["relationship_count"] += count

    def record_traversal(self, count: int = 1) -> None:
        self._counts["traversal_count"] += count
