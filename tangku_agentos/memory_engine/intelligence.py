from __future__ import annotations

from collections import defaultdict
from typing import Any


class MemoryIntelligence:
    """Lightweight memory intelligence layer for conversations, projects, and semantic recall."""

    def __init__(self) -> None:
        self._records: dict[tuple[str, str], dict[str, Any]] = {}
        self._index: dict[str, dict[str, list[str]]] = defaultdict(lambda: defaultdict(list))

    def store(self, memory_type: str, key: str, content: str, namespace: str = "default", metadata: dict[str, Any] | None = None) -> dict[str, Any]:
        record = {
            "memory_type": memory_type,
            "key": key,
            "content": content,
            "namespace": namespace,
            "metadata": metadata or {},
            "importance": self._score_importance(content),
        }
        self._records[(namespace, key)] = record
        for token in self._tokenize(content):
            self._index[namespace][token].append(key)
        return record

    def retrieve(self, query: str, namespace: str = "default", limit: int = 5) -> list[dict[str, Any]]:
        query_tokens = self._tokenize(query)
        if not query_tokens:
            return []

        scored: list[tuple[float, dict[str, Any]]] = []
        for record in self._records.values():
            if record["namespace"] != namespace:
                continue
            overlap = sum(1 for token in query_tokens if token in self._tokenize(record["content"]))
            if overlap == 0:
                continue
            score = overlap + record["importance"]
            scored.append((score, record))

        scored.sort(key=lambda item: item[0], reverse=True)
        return [
            {
                "key": record["key"],
                "content": record["content"],
                "namespace": record["namespace"],
                "score": score,
                "importance": record["importance"],
            }
            for score, record in scored[:limit]
        ]

    def remember(self, memory_type: str, key: str, content: str, namespace: str = "default") -> dict[str, Any]:
        return self.store(memory_type=memory_type, key=key, content=content, namespace=namespace)

    def compress_context(self, namespace: str = "default") -> list[dict[str, Any]]:
        return [record for (ns, _), record in self._records.items() if ns == namespace]

    def _tokenize(self, text: str) -> set[str]:
        return {token for token in text.lower().replace("-", " ").split() if token}

    def _score_importance(self, content: str) -> float:
        return min(3.0, 1.0 + len(content.split()) / 10.0)
