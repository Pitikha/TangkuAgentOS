"""AI Cognitive System - Context Engine"""
from __future__ import annotations
import asyncio, logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from typing import Any, Dict, List, Optional, TYPE_CHECKING
if TYPE_CHECKING:
    from tangku_agentos.cognitive_system.core.cognitive_config import CognitiveConfig
    from tangku_agentos.cognitive_system.core.cognitive_state import CognitiveState
logger = logging.getLogger(__name__)

class ContextType(Enum):
    CONVERSATION=auto(); EXECUTION=auto(); WORKSPACE=auto(); REPOSITORY=auto()
    RUNTIME=auto(); USER=auto(); SYSTEM=auto(); SHARED=auto()

@dataclass
class ContextEntry:
    context_id: str; context_type: ContextType; data: Any
    timestamp: datetime=field(default_factory=datetime.utcnow)
    expiration: Optional[datetime]=None; priority: int=0

@dataclass
class ContextResult:
    context: Dict[str, Any]; relevant_context: List[ContextEntry]=field(default_factory=list)
    missing_context: List[str]=field(default_factory=list)
    timestamp: datetime=field(default_factory=datetime.utcnow)

class ContextEngine:
    def __init__(self, config: "CognitiveConfig", state: "CognitiveState"):
        self._config=config; self._state=state; self._initialized=False; self._started=False
        self._contexts: Dict[str, ContextEntry]={}; self._context_stack: List[str]=[]
        self._metrics={"context_updates":0,"context_retrievals":0,"errors":0}
    
    async def initialize(self)->None:
        if self._initialized: return
        self._initialized=True
    
    async def start(self)->None:
        if self._started: return
        if not self._initialized: await self.initialize()
        self._started=True
    
    async def stop(self)->None:
        if not self._started: return
        self._started=False
    
    async def understand(self, data: Any, context_type: Optional[ContextType]=None) -> ContextResult:
        """Understand the context of the given data."""
        from tangku_agentos.cognitive_system.exceptions import ContextError
        try:
            # Extract context from data
            extracted_context=self._extract_context(data)
            
            # Retrieve relevant existing context
            relevant_context=self._retrieve_relevant_context(extracted_context, context_type)
            
            # Identify missing context
            missing_context=self._identify_missing_context(extracted_context, relevant_context)
            
            # Update context if needed
            if extracted_context:
                await self._update_context(extracted_context, context_type or ContextType.EXECUTION)
            
            self._metrics["context_retrievals"]+=1
            
            return ContextResult(
                context=extracted_context,
                relevant_context=relevant_context,
                missing_context=missing_context
            )
        except Exception as e:
            self._metrics["errors"]+=1
            raise ContextError(f"Failed to understand context: {e}") from e
    
    def _extract_context(self, data: Any) -> Dict[str, Any]:
        """Extract context information from data."""
        context={}
        
        if isinstance(data, dict):
            # Extract direct context fields
            for key in ["context", "conversation_id", "session_id", "user_id", "agent_id", "workspace", "repository", "goal"]:
                if key in data:
                    context[key]=data[key]
            
            # Extract from nested structures
            if "metadata" in data and isinstance(data["metadata"], dict):
                for key in ["conversation_id", "session_id", "user_id", "agent_id"]:
                    if key in data["metadata"]:
                        context[key]=data["metadata"][key]
        elif isinstance(data, str):
            # Try to extract context from text
            context["text"]=data
        
        # Add timestamp
        context["timestamp"]=datetime.utcnow().isoformat()
        
        return context
    
    def _retrieve_relevant_context(self, context: Dict[str, Any], context_type: Optional[ContextType]) -> List[ContextEntry]:
        """Retrieve context entries relevant to the given context."""
        relevant=[]
        
        for context_id, entry in self._contexts.items():
            # Check if context type matches
            if context_type and entry.context_type!=context_type:
                continue
            
            # Check if context is expired
            if entry.expiration and entry.expiration<datetime.utcnow():
                continue
            
            # Check if context is relevant
            if self._is_relevant(entry, context):
                relevant.append(entry)
        
        # Sort by priority and timestamp
        relevant.sort(key=lambda x: (x.priority, x.timestamp), reverse=True)
        
        return relevant[:10]  # Return top 10 most relevant
    
    def _is_relevant(self, entry: ContextEntry, context: Dict[str, Any]) -> bool:
        """Check if a context entry is relevant to the given context."""
        # Simple relevance check based on overlapping keys
        entry_keys=set(entry.data.keys()) if isinstance(entry.data, dict) else set()
        context_keys=set(context.keys())
        
        # If there are overlapping keys, it's relevant
        if entry_keys & context_keys:
            return True
        
        # Check for specific context types
        if entry.context_type==ContextType.CONVERSATION and "conversation_id" in context:
            if isinstance(entry.data, dict) and entry.data.get("conversation_id")==context.get("conversation_id"):
                return True
        
        if entry.context_type==ContextType.USER and "user_id" in context:
            if isinstance(entry.data, dict) and entry.data.get("user_id")==context.get("user_id"):
                return True
        
        return False
    
    def _identify_missing_context(self, context: Dict[str, Any], relevant: List[ContextEntry]) -> List[str]:
        """Identify missing context that would be helpful."""
        missing=[]
        
        # Check for common context fields
        common_fields=["conversation_id", "session_id", "user_id", "workspace", "repository", "goal"]
        
        for field in common_fields:
            if field not in context:
                # Check if any relevant context has this field
                has_field=any(
                    isinstance(entry.data, dict) and field in entry.data
                    for entry in relevant
                )
                if not has_field:
                    missing.append(field)
        
        return missing
    
    async def _update_context(self, context: Dict[str, Any], context_type: ContextType) -> None:
        """Update or add context."""
        context_id=self._generate_context_id(context, context_type)
        
        # Check if context already exists
        if context_id in self._contexts:
            # Update existing context
            existing=self._contexts[context_id]
            existing.data.update(context)
            existing.timestamp=datetime.utcnow()
        else:
            # Create new context entry
            entry=ContextEntry(
                context_id=context_id,
                context_type=context_type,
                data=context,
                timestamp=datetime.utcnow()
            )
            self._contexts[context_id]=entry
        
        self._metrics["context_updates"]+=1
        logger.debug(f"Context updated: {context_id}")
    
    def _generate_context_id(self, context: Dict[str, Any], context_type: ContextType) -> str:
        """Generate a unique ID for context."""
        # Use specific fields for ID generation based on type
        if context_type==ContextType.CONVERSATION:
            conv_id=context.get("conversation_id", "unknown")
            return f"conv_{conv_id}"
        elif context_type==ContextType.USER:
            user_id=context.get("user_id", "unknown")
            return f"user_{user_id}"
        elif context_type==ContextType.WORKSPACE:
            workspace=context.get("workspace", "unknown")
            return f"ws_{workspace}"
        elif context_type==ContextType.REPOSITORY:
            repo=context.get("repository", "unknown")
            return f"repo_{repo}"
        else:
            # Use a hash of the context
            import hashlib
            context_str=str(context)[:100]
            return f"ctx_{hashlib.sha256(context_str.encode()).hexdigest()[:16]}"
    
    async def get_context(self, context_id: str) -> Optional[ContextEntry]:
        """Get a specific context by ID."""
        return self._contexts.get(context_id)
    
    async def get_contexts(self, context_type: Optional[ContextType]=None) -> List[ContextEntry]:
        """Get all contexts of a specific type."""
        if context_type:
            return [entry for entry in self._contexts.values() if entry.context_type==context_type]
        return list(self._contexts.values())
    
    async def push_context(self, context: Dict[str, Any], context_type: ContextType) -> str:
        """Push a new context onto the stack."""
        context_id=self._generate_context_id(context, context_type)
        entry=ContextEntry(
            context_id=context_id,
            context_type=context_type,
            data=context,
            timestamp=datetime.utcnow()
        )
        self._contexts[context_id]=entry
        self._context_stack.append(context_id)
        return context_id
    
    async def pop_context(self) -> Optional[ContextEntry]:
        """Pop the most recent context from the stack."""
        if not self._context_stack:
            return None
        
        context_id=self._context_stack.pop()
        return self._contexts.get(context_id)
    
    async def clear_context(self, context_type: Optional[ContextType]=None) -> None:
        """Clear contexts of a specific type or all contexts."""
        if context_type:
            to_remove=[cid for cid, entry in self._contexts.items() if entry.context_type==context_type]
        else:
            to_remove=list(self._contexts.keys())
        
        for cid in to_remove:
            del self._contexts[cid]
            if cid in self._context_stack:
                self._context_stack.remove(cid)
    
    def get_metrics(self) -> Dict[str, Any]:
        return self._metrics.copy()
    
    def __repr__(self) -> str:
        return f"ContextEngine(initialized={self._initialized}, contexts={len(self._contexts)})"
