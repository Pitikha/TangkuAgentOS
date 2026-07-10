"""Semantic Memory Interface for Cognitive System - Concept-based Memory"""
import asyncio, logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, TYPE_CHECKING
if TYPE_CHECKING:
    from tangku_agentos.cognitive_system.core.cognitive_config import CognitiveConfig
    from tangku_agentos.cognitive_system.core.cognitive_state import CognitiveState
logger = logging.getLogger(__name__)

@dataclass
class Concept:
    concept_id: str; name: str; definition: str; examples: List[str]=field(default_factory=list)
    related_concepts: List[str]=field(default_factory=list)
    metadata: Dict[str, Any]=field(default_factory=dict)
    timestamp: datetime=field(default_factory=datetime.utcnow)
    confidence: float=0.5; usage_count: int=0

class SemanticMemoryInterface:
    def __init__(self, config: "CognitiveConfig", state: "CognitiveState"):
        self._config=config; self._state=state; self._concepts: Dict[str, Concept]={}
        self._name_index: Dict[str, str]= {}; self._relation_index: Dict[str, List[str]]= {}
        self._tag_index: Dict[str, List[str]]= {}; self._metrics={"concepts":0,"retrievals":0}
    
    async def initialize(self)->None: pass
    async def start(self)->None: pass
    async def stop(self)->None: pass
    
    async def store_concept(
        self,
        name: str,
        definition: str,
        concept_id: Optional[str]=None,
        examples: Optional[List[str]]=None,
        related_concepts: Optional[List[str]]=None,
        metadata: Optional[Dict[str, Any]]=None,
        confidence: float=0.5
    ) -> str:
        """Store a new concept in semantic memory."""
        import hashlib
        if not concept_id:
            concept_id=f"concept_{hashlib.sha256(f'{name}:{definition}'.encode()).hexdigest()[:16]}"
        
        concept=Concept(
            concept_id=concept_id,
            name=name,
            definition=definition,
            examples=examples or [],
            related_concepts=related_concepts or [],
            metadata=metadata or {},
            confidence=confidence
        )
        
        self._concepts[concept_id]=concept
        self._index_concept(concept)
        self._metrics["concepts"]+=1
        return concept_id
    
    def _index_concept(self, concept: Concept) -> None:
        """Index concept for fast retrieval."""
        # Name index (lowercase)
        name_lower=concept.name.lower()
        self._name_index[name_lower]=concept.concept_id
        
        # Relation index
        for related in concept.related_concepts:
            if related not in self._relation_index:
                self._relation_index[related]=[]
            self._relation_index[related].append(concept.concept_id)
        
        # Tag index (from metadata)
        tags=concept.metadata.get("tags", [])
        for tag in tags:
            if tag not in self._tag_index:
                self._tag_index[tag]=[]
            self._tag_index[tag].append(concept.concept_id)
    
    async def retrieve_concepts(
        self,
        query: Any,
        limit: int=10,
        include_related: bool=True
    ) -> List[Concept]:
        """Retrieve concepts matching the query."""
        query_str=str(query).lower()
        results=[]
        
        # Direct name match
        if query_str in self._name_index:
            concept_id=self._name_index[query_str]
            if concept_id in self._concepts:
                results.append(self._concepts[concept_id])
        
        # Search in definitions
        for concept in self._concepts.values():
            if query_str in concept.definition.lower():
                if concept.concept_id not in [r.concept_id for r in results]:
                    results.append(concept)
        
        # Search in examples
        for concept in self._concepts.values():
            for example in concept.examples:
                if query_str in example.lower():
                    if concept.concept_id not in [r.concept_id for r in results]:
                        results.append(concept)
                    break
        
        # Include related concepts
        if include_related and results:
            related_ids=set()
            for concept in results:
                related_ids.update(concept.related_concepts)
            for concept_id in related_ids:
                if concept_id in self._concepts:
                    concept=self._concepts[concept_id]
                    if concept.concept_id not in [r.concept_id for r in results]:
                        results.append(concept)
        
        # Sort by confidence and usage
        results.sort(key=lambda x: (x.confidence, x.usage_count), reverse=True)
        self._metrics["retrievals"]+=1
        return results[:limit]
    
    async def get_concept(self, concept_id: str) -> Optional[Concept]:
        """Get a specific concept."""
        return self._concepts.get(concept_id)
    
    async def get_concept_by_name(self, name: str) -> Optional[Concept]:
        """Get concept by name."""
        name_lower=name.lower()
        if name_lower in self._name_index:
            concept_id=self._name_index[name_lower]
            return self._concepts.get(concept_id)
        return None
    
    async def get_related_concepts(self, concept_id: str, limit: int=10) -> List[Concept]:
        """Get concepts related to a specific concept."""
        if concept_id not in self._concepts: return []
        concept=self._concepts[concept_id]
        related_ids=concept.related_concepts
        results=[]
        for cid in related_ids:
            if cid in self._concepts:
                results.append(self._concepts[cid])
        return results[:limit]
    
    async def get_concepts_by_tag(self, tag: str, limit: int=10) -> List[Concept]:
        """Get concepts by tag."""
        if tag not in self._tag_index: return []
        concept_ids=self._tag_index[tag][:limit]
        return [self._concepts[cid] for cid in concept_ids if cid in self._concepts]
    
    async def update_concept(self, concept_id: str, **kwargs) -> bool:
        """Update a concept."""
        if concept_id not in self._concepts: return False
        concept=self._concepts[concept_id]
        for key, value in kwargs.items():
            if hasattr(concept, key):
                setattr(concept, key, value)
        # Re-index if name changed
        if "name" in kwargs:
            old_name=concept.name.lower()
            if old_name in self._name_index:
                del self._name_index[old_name]
            self._name_index[concept.name.lower()]=concept_id
        return True
    
    async def remove_concept(self, concept_id: str) -> bool:
        """Remove a concept."""
        if concept_id not in self._concepts: return False
        concept=self._concepts[concept_id]
        # Remove from indexes
        if concept.name.lower() in self._name_index:
            del self._name_index[concept.name.lower()]
        for related in concept.related_concepts:
            if related in self._relation_index:
                if concept_id in self._relation_index[related]:
                    self._relation_index[related].remove(concept_id)
        tags=concept.metadata.get("tags", [])
        for tag in tags:
            if tag in self._tag_index:
                if concept_id in self._tag_index[tag]:
                    self._tag_index[tag].remove(concept_id)
        del self._concepts[concept_id]
        return True
    
    async def link_concepts(self, concept_id1: str, concept_id2: str) -> bool:
        """Link two concepts together."""
        if concept_id1 not in self._concepts or concept_id2 not in self._concepts:
            return False
        if concept_id2 not in self._concepts[concept_id1].related_concepts:
            self._concepts[concept_id1].related_concepts.append(concept_id2)
        if concept_id1 not in self._concepts[concept_id2].related_concepts:
            self._concepts[concept_id2].related_concepts.append(concept_id1)
        # Update relation index
        if concept_id2 not in self._relation_index:
            self._relation_index[concept_id2]=[]
        if concept_id1 not in self._relation_index[concept_id2]:
            self._relation_index[concept_id2].append(concept_id1)
        if concept_id1 not in self._relation_index:
            self._relation_index[concept_id1]=[]
        if concept_id2 not in self._relation_index[concept_id1]:
            self._relation_index[concept_id1].append(concept_id2)
        return True
    
    async def unlink_concepts(self, concept_id1: str, concept_id2: str) -> bool:
        """Unlink two concepts."""
        if concept_id1 not in self._concepts or concept_id2 not in self._concepts:
            return False
        if concept_id2 in self._concepts[concept_id1].related_concepts:
            self._concepts[concept_id1].related_concepts.remove(concept_id2)
        if concept_id1 in self._concepts[concept_id2].related_concepts:
            self._concepts[concept_id2].related_concepts.remove(concept_id1)
        # Update relation index
        if concept_id2 in self._relation_index:
            if concept_id1 in self._relation_index[concept_id2]:
                self._relation_index[concept_id2].remove(concept_id1)
        if concept_id1 in self._relation_index:
            if concept_id2 in self._relation_index[concept_id1]:
                self._relation_index[concept_id1].remove(concept_id2)
        return True
    
    async def clear_concepts(self) -> None:
        """Clear all concepts."""
        self._concepts.clear()
        self._name_index.clear()
        self._relation_index.clear()
        self._tag_index.clear()
    
    def get_metrics(self) -> Dict[str, Any]: return self._metrics.copy()
