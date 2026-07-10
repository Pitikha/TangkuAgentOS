"""Working Memory for Cognitive System"""
import asyncio, logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, TYPE_CHECKING
if TYPE_CHECKING:
    from tangku_agentos.cognitive_system.core.cognitive_config import CognitiveConfig
    from tangku_agentos.cognitive_system.core.cognitive_state import CognitiveState
logger = logging.getLogger(__name__)

@dataclass
class MemoryItem:
    memory_id: str; data: Any; metadata: Dict[str, Any]=field(default_factory=dict)
    timestamp: datetime=field(default_factory=datetime.utcnow)
    access_count: int=0

class WorkingMemory:
    def __init__(self, config: "CognitiveConfig", state: "CognitiveState"):
        self._config=config; self._state=state; self._memory: Dict[str, MemoryItem]={}
        self._metrics={"stored":0,"retrieved":0}
    
    async def initialize(self)->None: pass
    async def start(self)->None: pass
    async def stop(self)->None: pass
    
    async def store(self, key: str, data: Any) -> str:
        item=MemoryItem(memory_id=key, data=data)
        self._memory[key]=item
        self._metrics["stored"]+=1
        return key
    
    async def retrieve(self, query: Any, limit: int=10) -> List[Any]:
        query_str=str(query).lower()
        results=[]
        for item in self._memory.values():
            if query_str in str(item.data).lower():
                item.access_count+=1
                results.append(item.data)
        return results[:limit]
    
    async def get(self, key: str) -> Optional[Any]:
        if key not in self._memory: return None
        self._memory[key].access_count+=1
        return self._memory[key].data
    
    async def update(self, key: str, data: Any) -> bool:
        if key not in self._memory: return False
        self._memory[key].data=data
        self._memory[key].timestamp=datetime.utcnow()
        return True
    
    async def remove(self, key: str) -> bool:
        if key not in self._memory: return False
        del self._memory[key]
        return True
    
    async def clear(self) -> None: self._memory.clear()
    def get_metrics(self) -> Dict[str, Any]: return self._metrics.copy()
