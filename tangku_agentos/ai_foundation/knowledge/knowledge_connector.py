"""
Knowledge Connector for TangkuAgentOS AI Foundation Framework.

This module integrates with the Knowledge Engine to retrieve, store, and manage knowledge.
It serves as the primary interface between the AI Foundation Framework and the Knowledge Engine.
"""

from typing import Any, Optional, Dict, List, Union
from dataclasses import dataclass, field
import logging
import asyncio
from enum import Enum

logger = logging.getLogger(__name__)


class KnowledgeType(Enum):
    """Supported knowledge types in TangkuAgentOS."""
    DOCUMENT = "document"
    REPOSITORY = "repository"
    CODE = "code"
    WORKFLOW = "workflow"
    AGENT = "agent"
    USER = "user"
    SYSTEM = "system"


@dataclass
class KnowledgeReference:
    """Represents a reference to a knowledge entry in the Knowledge Engine."""
    knowledge_id: str
    knowledge_type: KnowledgeType
    confidence: float = 1.0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class KnowledgeResult:
    """Result of a knowledge operation."""
    success: bool
    knowledge_id: Optional[str] = None
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class KnowledgeConnector:
    """Connects the AI Foundation Framework to the Knowledge Engine.

    This class provides a unified interface for all knowledge operations,
    including retrieval, storage, and management of knowledge across different types.
    """

    def __init__(self, knowledge_engine: Any):
        """Initialize the KnowledgeConnector.

        Args:
            knowledge_engine: The Knowledge Engine instance to connect to.
        """
        self._knowledge_engine = knowledge_engine
        self._lock = asyncio.Lock()
        logger.info("KnowledgeConnector initialized with Knowledge Engine.")

    async def retrieve(
        self,
        knowledge_references: List[Union[str, KnowledgeReference]],
        max_retries: int = 3,
    ) -> Dict[str, Dict[str, Any]]:
        """Retrieve multiple knowledge entries by their references.

        Args:
            knowledge_references: List of knowledge IDs or KnowledgeReference objects.
            max_retries: Maximum number of retries for failed retrievals.

        Returns:
            Dictionary mapping knowledge IDs to their data.
        """
        knowledge_entries = {}
        for ref in knowledge_references:
            if isinstance(ref, str):
                knowledge_id = ref
                knowledge_type = KnowledgeType.DOCUMENT
            else:
                knowledge_id = ref.knowledge_id
                knowledge_type = ref.knowledge_type

            for attempt in range(max_retries):
                try:
                    knowledge = await self._retrieve_single(knowledge_id, knowledge_type)
                    if knowledge:
                        knowledge_entries[knowledge_id] = knowledge
                    break
                except Exception as e:
                    logger.warning(f"Attempt {attempt + 1} failed for knowledge {knowledge_id}: {e}")
                    if attempt == max_retries - 1:
                        logger.error(f"Failed to retrieve knowledge {knowledge_id} after {max_retries} attempts.")

        logger.info(f"Retrieved {len(knowledge_entries)} knowledge entries.")
        return knowledge_entries

    async def _retrieve_single(
        self,
        knowledge_id: str,
        knowledge_type: KnowledgeType,
    ) -> Optional[Dict[str, Any]]:
        """Retrieve a single knowledge entry by its ID and type.

        Args:
            knowledge_id: The ID of the knowledge to retrieve.
            knowledge_type: The type of knowledge.

        Returns:
            The knowledge data if found, otherwise None.
        """
        async with self._lock:
            try:
                knowledge = await self._knowledge_engine.get_knowledge(knowledge_id, knowledge_type.value)
                logger.debug(f"Retrieved knowledge {knowledge_id} of type {knowledge_type.value}.")
                return knowledge
            except Exception as e:
                logger.error(f"Error retrieving knowledge {knowledge_id}: {e}")
                return None

    async def store(
        self,
        knowledge_type: KnowledgeType,
        data: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None,
        max_retries: int = 3,
    ) -> KnowledgeResult:
        """Store a new knowledge entry in the Knowledge Engine.

        Args:
            knowledge_type: The type of knowledge to store.
            data: The knowledge data to store.
            metadata: Optional metadata for the knowledge.
            max_retries: Maximum number of retries for failed storage.

        Returns:
            KnowledgeResult indicating success or failure.
        """
        for attempt in range(max_retries):
            try:
                knowledge_id = await self._knowledge_engine.store_knowledge(
                    knowledge_type.value,
                    data,
                    metadata or {},
                )
                logger.info(f"Stored knowledge {knowledge_id} of type {knowledge_type.value}.")
                return KnowledgeResult(
                    success=True,
                    knowledge_id=knowledge_id,
                    data=data,
                    metadata=metadata or {},
                )
            except Exception as e:
                logger.warning(f"Attempt {attempt + 1} failed to store knowledge: {e}")
                if attempt == max_retries - 1:
                    logger.error(f"Failed to store knowledge after {max_retries} attempts.")
                    return KnowledgeResult(
                        success=False,
                        error=str(e),
                    )
        return KnowledgeResult(success=False, error="Max retries exceeded.")

    async def search(
        self,
        query: str,
        knowledge_types: Optional[List[KnowledgeType]] = None,
        limit: int = 10,
        confidence_threshold: float = 0.5,
    ) -> List[Dict[str, Any]]:
        """Search for knowledge entries matching a query.

        Args:
            query: The search query.
            knowledge_types: List of knowledge types to search in. If None, searches all types.
            limit: Maximum number of results to return.
            confidence_threshold: Minimum confidence score for results.

        Returns:
            List of knowledge entries matching the query.
        """
        try:
            types = [kt.value for kt in knowledge_types] if knowledge_types else None
            results = await self._knowledge_engine.search_knowledge(
                query,
                types,
                limit,
                confidence_threshold,
            )
            logger.info(f"Found {len(results)} knowledge entries for query: {query[:50]}...")
            return results
        except Exception as e:
            logger.error(f"Error searching knowledge: {e}")
            return []

    async def update(
        self,
        knowledge_id: str,
        knowledge_type: KnowledgeType,
        updates: Dict[str, Any],
    ) -> KnowledgeResult:
        """Update an existing knowledge entry.

        Args:
            knowledge_id: The ID of the knowledge to update.
            knowledge_type: The type of knowledge.
            updates: Dictionary of updates to apply.

        Returns:
            KnowledgeResult indicating success or failure.
        """
        try:
            await self._knowledge_engine.update_knowledge(knowledge_id, knowledge_type.value, updates)
            logger.info(f"Updated knowledge {knowledge_id} of type {knowledge_type.value}.")
            return KnowledgeResult(success=True, knowledge_id=knowledge_id)
        except Exception as e:
            logger.error(f"Error updating knowledge {knowledge_id}: {e}")
            return KnowledgeResult(success=False, error=str(e))

    async def delete(
        self,
        knowledge_id: str,
        knowledge_type: KnowledgeType,
    ) -> KnowledgeResult:
        """Delete a knowledge entry from the Knowledge Engine.

        Args:
            knowledge_id: The ID of the knowledge to delete.
            knowledge_type: The type of knowledge.

        Returns:
            KnowledgeResult indicating success or failure.
        """
        try:
            await self._knowledge_engine.delete_knowledge(knowledge_id, knowledge_type.value)
            logger.info(f"Deleted knowledge {knowledge_id} of type {knowledge_type.value}.")
            return KnowledgeResult(success=True, knowledge_id=knowledge_id)
        except Exception as e:
            logger.error(f"Error deleting knowledge {knowledge_id}: {e}")
            return KnowledgeResult(success=False, error=str(e))
