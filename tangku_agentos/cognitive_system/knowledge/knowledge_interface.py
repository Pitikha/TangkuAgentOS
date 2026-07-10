"""Knowledge Interface for Cognitive System"""
import asyncio, logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, TYPE_CHECKING
if TYPE_CHECKING:
    from tangku_agentos.cognitive_system.core.cognitive_config import CognitiveConfig
    from tangku_agentos.cognitive_system.core.cognitive_state import CognitiveState
logger = logging.getLogger(__name__)

@dataclass
class KnowledgeEntry:
    entry_id: str; content: str; metadata: Dict[str, Any]=field(default_factory=dict)
    source: str=""; confidence: float=0.0; tags: List[str]=field(default_factory=list)
    timestamp: datetime=field(default_factory=datetime.utcnow)

class KnowledgeInterface:
    def __init__(self, config: "CognitiveConfig", state: "CognitiveState"):
        self._config=config; self._state=state; self._knowledge: Dict[str, KnowledgeEntry]={}
        self._index: Dict[str, List[str]]= {}; self._metrics={"queries":0,"updates":0}
    
    async def initialize(self)->None: pass
    async def start(self)->None: pass
    async def stop(self)->None: pass
    
    async def retrieve(self, query: Any, limit: int=10) -> Dict[str, Any]:
        query_str=str(query).lower()
        results=[]
        for entry in self._knowledge.values():
            if query_str in entry.content.lower() or query_str in str(entry.metadata).lower():
                results.append({"entry_id": entry.entry_id, "content": entry.content, "metadata": entry.metadata, "confidence": entry.confidence})
        return {"results": results[:limit], "count": len(results)}
    
    async def search(self, query: str, limit: int=10) -> Dict[str, Any]:
        return await self.retrieve(query, limit)
    
    async def update(self, data: Any) -> str:
        import hashlib
        if isinstance(data, dict) and "content" in data:
            content=data["content"]
            entry_id=hashlib.sha256(content.encode()).hexdigest()[:16]
        else:
            content=str(data)
            entry_id=hashlib.sha256(content.encode()).hexdigest()[:16]
        
        entry=KnowledgeEntry(
            entry_id=entry_id,
            content=content,
            metadata=data if isinstance(data, dict) else {},
            confidence=data.get("confidence", 0.5) if isinstance(data, dict) else 0.5
        )
        self._knowledge[entry_id]=entry
        self._index_content(entry)
        self._metrics["updates"]+=1
        return entry_id
    
    def _index_content(self, entry: KnowledgeEntry) -> None:
        words=entry.content.lower().split()
        for word in set(words):
            if len(word)>3:
                if word not in self._index: self._index[word]=[]
                self._index[word].append(entry.entry_id)
    
    async def get(self, entry_id: str) -> Optional[KnowledgeEntry]:
        return self._knowledge.get(entry_id)
    
    async def remove(self, entry_id: str) -> bool:
        if entry_id not in self._knowledge: return False
        del self._knowledge[entry_id]
        return True
    
    async def clear(self) -> None:
        self._knowledge.clear(); self._index.clear()
    def get_metrics(self) -> Dict[str, Any]: return self._metrics.copy()
