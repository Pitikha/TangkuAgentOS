"""
AI Foundation Framework - Retrieval Result

This module defines the RetrievalResult class.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from typing import Any, Dict, List, Optional


class RetrievalSource(Enum):
    """Source of retrieved information."""
    MEMORY = auto()
    KNOWLEDGE = auto()
    EMBEDDING = auto()
    KEYWORD = auto()
    HYBRID = auto()
    GRAPH = auto()
    REPOSITORY = auto()
    WORKSPACE = auto()
    CUSTOM = auto()


class RetrievalStrategy(Enum):
    """Strategy used for retrieval."""
    SEMANTIC = auto()
    KEYWORD = auto()
    HYBRID = auto()
    GRAPH = auto()
    REPOSITORY = auto()
    WORKSPACE = auto()
    CUSTOM = auto()


@dataclass
class RetrievedItem:
    """
    Represents a single retrieved item.
    
    Attributes:
        content: The content of the retrieved item.
        source: Source of the item.
        score: Relevance score (0 to 1).
        metadata: Additional metadata.
        rank: Rank of the item in the results.
    """

    content: Any
    source: RetrievalSource = RetrievalSource.CUSTOM
    score: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    rank: int = 0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "content": self.content,
            "source": self.source.value,
            "score": self.score,
            "metadata": self.metadata,
            "rank": self.rank,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "RetrievedItem":
        """Create from dictionary."""
        source = RetrievalSource.CUSTOM
        if "source" in data and data["source"]:
            try:
                source = RetrievalSource(data["source"])
            except ValueError:
                pass

        return cls(
            content=data.get("content"),
            source=source,
            score=data.get("score", 0.0),
            metadata=data.get("metadata", {}),
            rank=data.get("rank", 0),
        )


@dataclass
class RetrievalResult:
    """
    Result from a retrieval operation.
    
    This class represents the results of a retrieval operation, which
    combines information from multiple sources including memory,
    knowledge, and embeddings.
    
    Attributes:
        query: The original query.
        items: List of retrieved items.
        strategy: Strategy used for retrieval.
        sources_used: Set of sources that contributed to the results.
        scores: List of scores for each item.
        metadata: Additional metadata.
        timestamp: When the retrieval was performed.
    """

    query: str
    items: List[RetrievedItem] = field(default_factory=list)
    strategy: RetrievalStrategy = RetrievalStrategy.HYBRID
    sources_used: Set[RetrievalSource] = field(default_factory=set)
    scores: List[float] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow)

    @property
    def count(self) -> int:
        """Get the number of retrieved items."""
        return len(self.items)

    @property
    def best_item(self) -> Optional[RetrievedItem]:
        """Get the best (highest scoring) item."""
        if not self.items:
            return None
        return max(self.items, key=lambda x: x.score)

    @property
    def best_score(self) -> float:
        """Get the best (highest) score."""
        if not self.scores:
            return 0.0
        return max(self.scores)

    @property
    def average_score(self) -> float:
        """Get the average score."""
        if not self.scores:
            return 0.0
        return sum(self.scores) / len(self.scores)

    def add_item(self, item: RetrievedItem) -> None:
        """Add a retrieved item to the results."""
        self.items.append(item)
        self.sources_used.add(item.source)
        self.scores.append(item.score)
        
        # Update rank
        item.rank = len(self.items)

    def sort_by_score(self, descending: bool = True) -> None:
        """Sort items by score."""
        self.items.sort(key=lambda x: x.score, reverse=descending)
        
        # Update ranks
        for i, item in enumerate(self.items):
            item.rank = i + 1

    def filter_by_score(self, min_score: float = 0.0) -> "RetrievalResult":
        """
        Filter items by minimum score.
        
        Args:
            min_score: Minimum score threshold.
        
        Returns:
            New RetrievalResult with filtered items.
        """
        filtered_items = [item for item in self.items if item.score >= min_score]
        filtered_scores = [item.score for item in filtered_items]
        
        return RetrievalResult(
            query=self.query,
            items=filtered_items,
            strategy=self.strategy,
            sources_used=self.sources_used,
            scores=filtered_scores,
            metadata=self.metadata,
            timestamp=self.timestamp,
        )

    def get_by_source(self, source: RetrievalSource) -> List[RetrievedItem]:
        """
        Get items from a specific source.
        
        Args:
            source: Source to filter by.
        
        Returns:
            List of items from the source.
        """
        return [item for item in self.items if item.source == source]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "query": self.query,
            "items": [item.to_dict() for item in self.items],
            "strategy": self.strategy.value,
            "sources_used": [s.value for s in self.sources_used],
            "scores": self.scores,
            "metadata": self.metadata,
            "timestamp": self.timestamp.isoformat(),
            "count": self.count,
            "best_score": self.best_score,
            "average_score": self.average_score,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "RetrievalResult":
        """Create from dictionary."""
        strategy = RetrievalStrategy.HYBRID
        if "strategy" in data and data["strategy"]:
            try:
                strategy = RetrievalStrategy(data["strategy"])
            except ValueError:
                pass

        sources_used = set()
        for source in data.get("sources_used", []):
            try:
                sources_used.add(RetrievalSource(source))
            except ValueError:
                pass

        return cls(
            query=data.get("query", ""),
            items=[RetrievedItem.from_dict(item) for item in data.get("items", [])],
            strategy=strategy,
            sources_used=sources_used,
            scores=data.get("scores", []),
            metadata=data.get("metadata", {}),
            timestamp=datetime.fromisoformat(data.get("timestamp", datetime.utcnow().isoformat())),
        )

    def __len__(self) -> int:
        """Get the number of items."""
        return self.count

    def __iter__(self):
        """Iterate over items."""
        return iter(self.items)

    def __getitem__(self, index: int) -> RetrievedItem:
        """Get an item by index."""
        return self.items[index]

    def __repr__(self) -> str:
        """Return string representation."""
        return (
            f"RetrievalResult("
            f"query={self.query[:30]!r}, "
            f"count={self.count}, "
            f"best_score={self.best_score:.2f})"
        )
