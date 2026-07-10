"""Long-Term Memory Interface for Cognitive System"""
import asyncio, logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, TYPE_CHECKING
if TYPE_CHECKING:
    from tangku_agentos.cognitive_system.core.cognitive_config import CognitiveConfig
    from tangku_agentos.cognitive_system.core.cognitive_state import CognitiveState
logger = logging.getLogger(__name__)

@dataclass
class LTMEntry:
    entry_id: str; data: Any; metadata: Dict[str, Any]=field(default_factory=dict)
    timestamp: datetime=field(default_factory=datetime.utcnow)
    tags: List[str]=field(default_factory=list)

class LongTermMemoryInterface:
    def __init__(self, config: "CognitiveConfig", state: "CognitiveState"):
        self._config=config; self._state=state; self._memory: Dict[str, LTMEntry]={}
        self._index: Dict[str, List[str]]= {}; self._metrics={"stored":0,"retrieved":0}
    
    async def initialize(self)->None: pass
    async def start(self)->None: pass
    async def stop(self)->None: pass
    
    async def store(self, data: Any, metadata: Optional[Dict[str, Any]]=None) -> str:
        import hashlib
        entry_id=hashlib.sha256(str(data).encode()).hexdigest()[:16]
        tags=metadata.get("tags", []) if metadata else []
        entry=LTMEntry(entry_id=entry_id, data=data, metadata=metadata or {}, tags=tags)
        self._memory[entry_id]=entry
        self._index_tags(entry)
        self._metrics["stored"]+=1
        return entry_id
    
    def _index_tags(self, entry: LTMEntry) -> None:
        for tag in entry.tags:
            if tag not in self._index: self._index[tag]=[]
            self._index[tag].append(entry.entry_id)
    
    async def retrieve(self, query: Any, limit: int=10) -> List[Any]:
        query_str=str(query).lower()
        results=[]
        for entry in self._memory.values():
            if query_str in str(entry.data).lower() or query_str in str(entry.metadata).lower():
                results.append(entry.data)
        return results[:limit]
    
    async def retrieve_by_tag(self, tag: str, limit: int=10) -> List[Any]:
        if tag not in self._index: return []
        results=[]
        for entry_id in self._index[tag][:limit]:
            if entry_id in self._memory:
                results.append(self._memory[entry_id].data)
        return results
    
    async def update(self, entry_id: str, data: Any) -> bool:
        if entry_id not in self._memory: return False
        self._memory[entry_id].data=data
        self._memory[entry_id].timestamp=datetime.utcnow()
        return True
    
    async def remove(self, entry_id: str) -> bool:
        if entry_id not in self._memory: return False
        entry=self._memory[entry_id]
        for tag in entry.tags:
            if tag in self._index and entry_id in self._index[tag]:
                self._index[tag].remove(entry_id)
        del self._memory[entry_id]
        return True
    
    async def clear(self) -> None:
        self._memory.clear(); self._index.clear()
    def get_metrics(self) -> Dict[str, Any]: return self._metrics.copy()
