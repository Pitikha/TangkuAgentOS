"""
Knowledge Citation for TangkuAgentOS AI Foundation Framework.

This module handles generation of citations for knowledge entries used in AI responses.
"""

from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
import logging
from datetime import datetime
from .knowledge_connector import KnowledgeType

logger = logging.getLogger(__name__)


@dataclass
class Citation:
    """Represents a citation for a knowledge entry."""
    knowledge_id: str
    knowledge_type: KnowledgeType
    source: str
    content: str
    timestamp: datetime
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CitationResult:
    """Result of a citation generation operation."""
    citations: List[Citation]
    metadata: Dict[str, Any] = field(default_factory=dict)


class KnowledgeCitationGenerator:
    """Generates citations for knowledge entries used in AI responses.

    This class provides methods for generating citations for knowledge entries
    that are used in AI model responses, ensuring traceability and transparency.
    """

    def __init__(self):
        """Initialize the KnowledgeCitationGenerator."""
        logger.info("KnowledgeCitationGenerator initialized.")

    async def generate_citations(
        self,
        knowledge_entries: List[Dict[str, Any]],
        response: str,
    ) -> CitationResult:
        """Generate citations for knowledge entries used in a response.

        Args:
            knowledge_entries: List of knowledge entries used in the response.
            response: The AI response to generate citations for.

        Returns:
            CitationResult containing the generated citations.
        """
        citations = []
        for entry in knowledge_entries:
            citation = Citation(
                knowledge_id=entry.get("id", ""),
                knowledge_type=KnowledgeType(entry.get("knowledge_type", "document")),
                source=entry.get("source", ""),
                content=entry.get("content", "")[:200],
                timestamp=datetime.fromisoformat(entry.get("timestamp", datetime.utcnow().isoformat())),
                metadata=entry.get("metadata", {}),
            )
            citations.append(citation)

        logger.info(f"Generated {len(citations)} citations for response.")
        return CitationResult(
            citations=citations,
            metadata={"response_length": len(response)},
        )

    async def generate_citation_for_query(
        self,
        query: str,
        knowledge_entries: List[Dict[str, Any]],
    ) -> CitationResult:
        """Generate citations for knowledge entries matching a query.

        Args:
            query: The query used to retrieve the knowledge entries.
            knowledge_entries: List of knowledge entries matching the query.

        Returns:
            CitationResult containing the generated citations.
        """
        citations = []
        for entry in knowledge_entries:
            citation = Citation(
                knowledge_id=entry.get("id", ""),
                knowledge_type=KnowledgeType(entry.get("knowledge_type", "document")),
                source=entry.get("source", ""),
                content=entry.get("content", "")[:200],
                timestamp=datetime.fromisoformat(entry.get("timestamp", datetime.utcnow().isoformat())),
                metadata={"query": query},
            )
            citations.append(citation)

        logger.info(f"Generated {len(citations)} citations for query: {query[:50]}...")
        return CitationResult(
            citations=citations,
            metadata={"query": query},
        )

    def format_citation(self, citation: Citation) -> str:
        """Format a citation for display.

        Args:
            citation: The citation to format.

        Returns:
            Formatted citation string.
        """
        return f"[{citation.knowledge_type.value.upper()}:{citation.knowledge_id}] {citation.source} - {citation.content}"
