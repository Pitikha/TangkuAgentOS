"""Memory Consolidation Engine for Cognitive System"""
import asyncio, logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, TYPE_CHECKING
if TYPE_CHECKING:
    from tangku_agentos.cognitive_system.core.cognitive_config import CognitiveConfig
    from tangku_agentos.cognitive_system.core.cognitive_state import CognitiveState
    from tangku_agentos.cognitive_system.memory.working_memory import WorkingMemory
    from tangku_agentos.cognitive_system.memory.long_term_memory import LongTermMemoryInterface
logger = logging.getLogger(__name__)

@dataclass
class ConsolidationResult:
    consolidated_count: int=0; moved_to_ltm: int=0; compressed_count: int=0
    expired_count: int=0; optimized_count: int=0
    timestamp: datetime=field(default_factory=datetime.utcnow)
    duration: float=0.0

class MemoryConsolidationEngine:
    def __init__(
        self,
        config: "CognitiveConfig",
        state: "CognitiveState",
        working_memory: Optional["WorkingMemory"]=None,
        long_term_memory: Optional["LongTermMemoryInterface"]=None
    ):
        self._config=config; self._state=state
        self._working_memory=working_memory
        self._long_term_memory=long_term_memory
        self._metrics={"consolidations":0,"errors":0}
        self._last_consolidation: Optional[datetime]=None
    
    async def initialize(self)->None: pass
    async def start(self)->None: pass
    async def stop(self)->None: pass
    
    async def consolidate(self) -> ConsolidationResult:
        """Perform memory consolidation."""
        from tangku_agentos.cognitive_system.exceptions import MemoryError
        import time
        start_time=time.time()
        
        try:
            result=ConsolidationResult()
            
            # Move important items from working memory to long-term memory
            if self._working_memory and self._long_term_memory:
                result.moved_to_ltm=await self._move_to_long_term()
            
            # Compress old memories
            result.compressed_count=await self._compress_memories()
            
            # Expire old memories
            result.expired_count=await self._expire_memories()
            
            # Optimize memory structure
            result.optimized_count=await self._optimize_memory()
            
            result.consolidated_count=(
                result.moved_to_ltm + result.compressed_count + 
                result.expired_count + result.optimized_count
            )
            result.duration=time.time()-start_time
            self._last_consolidation=datetime.utcnow()
            self._metrics["consolidations"]+=1
            
            return result
            
        except Exception as e:
            self._metrics["errors"]+=1
            raise MemoryError(f"Memory consolidation failed: {e}") from e
    
    async def _move_to_long_term(self) -> int:
        """Move important items from working to long-term memory."""
        if not self._working_memory or not self._long_term_memory:
            return 0
        
        moved=0
        working_items=self._working_memory._memory  # Access internal storage
        
        for memory_id, item in list(working_items.items()):
            # Check if item should be moved to long-term memory
            if self._should_move_to_ltm(item):
                # Store in long-term memory
                await self._long_term_memory.store(
                    data=item.data,
                    metadata={
                        "source": "working_memory",
                        "original_id": memory_id,
                        "access_count": item.access_count,
                        "timestamp": item.timestamp.isoformat()
                    }
                )
                # Remove from working memory
                await self._working_memory.remove(memory_id)
                moved+=1
        
        return moved
    
    def _should_move_to_ltm(self, item: Any) -> bool:
        """Determine if an item should be moved to long-term memory."""
        # Move if accessed frequently
        if item.access_count>3:
            return True
        
        # Move if it's been in working memory for a while
        age=(datetime.utcnow()-item.timestamp).total_seconds()
        if age>3600:  # More than 1 hour
            return True
        
        # Move if marked as important
        if item.metadata.get("important", False):
            return True
        
        return False
    
    async def _compress_memories(self) -> int:
        """Compress old memories to save space."""
        if not self._long_term_memory:
            return 0
        
        compressed=0
        ltm_items=self._long_term_memory._memory  # Access internal storage
        
        for entry_id, entry in list(ltm_items.items()):
            # Check if entry should be compressed
            if self._should_compress(entry):
                # Compress the data
                compressed_data=self._compress_data(entry.data)
                if compressed_data!=entry.data:
                    await self._long_term_memory.update(entry_id, compressed_data)
                    compressed+=1
        
        return compressed
    
    def _should_compress(self, entry: Any) -> bool:
        """Determine if an entry should be compressed."""
        # Compress if it's old
        age=(datetime.utcnow()-entry.timestamp).total_seconds()
        if age>86400:  # More than 1 day
            return True
        
        # Compress if it's large
        data_size=len(str(entry.data))
        if data_size>10000:  # More than 10KB
            return True
        
        return False
    
    def _compress_data(self, data: Any) -> Any:
        """Compress data for storage."""
        # Simple compression: truncate long strings
        if isinstance(data, str):
            if len(data)>10000:
                return data[:10000] + "... [TRUNCATED]"
        elif isinstance(data, dict):
            # Compress dictionary values
            compressed={}
            for key, value in data.items():
                if isinstance(value, str) and len(value)>1000:
                    compressed[key]=value[:1000] + "... [TRUNCATED]"
                else:
                    compressed[key]=value
            return compressed
        
        return data
    
    async def _expire_memories(self) -> int:
        """Remove expired memories."""
        expired=0
        
        # Expire working memory items
        if self._working_memory:
            working_items=self._working_memory._memory
            for memory_id, item in list(working_items.items()):
                if item.expiration and item.expiration<datetime.utcnow():
                    await self._working_memory.remove(memory_id)
                    expired+=1
        
        # Expire long-term memory items
        if self._long_term_memory:
            ltm_items=self._long_term_memory._memory
            expiration_age=self._config.memory.memory_expiration_age if self._config else 86400
            for entry_id, entry in list(ltm_items.items()):
                age=(datetime.utcnow()-entry.timestamp).total_seconds()
                if age>expiration_age:
                    await self._long_term_memory.remove(entry_id)
                    expired+=1
        
        return expired
    
    async def _optimize_memory(self) -> int:
        """Optimize memory structure."""
        optimized=0
        
        # Rebuild indexes if needed
        if self._long_term_memory:
            # Rebuild tag index
            self._long_term_memory._index={}
            for entry_id, entry in self._long_term_memory._memory.items():
                for tag in entry.tags:
                    if tag not in self._long_term_memory._index:
                        self._long_term_memory._index[tag]=[]
                    self._long_term_memory._index[tag].append(entry_id)
            optimized+=1
        
        return optimized
    
    async def get_consolidation_stats(self) -> Dict[str, Any]:
        """Get memory consolidation statistics."""
        return {
            "last_consolidation": self._last_consolidation,
            "metrics": self._metrics.copy()
        }
    
    def get_metrics(self) -> Dict[str, Any]: return self._metrics.copy()
