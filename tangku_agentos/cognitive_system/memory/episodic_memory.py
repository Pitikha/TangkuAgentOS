"""Episodic Memory Interface for Cognitive System - Event-based Memory"""
import asyncio, logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, TYPE_CHECKING
if TYPE_CHECKING:
    from tangku_agentos.cognitive_system.core.cognitive_config import CognitiveConfig
    from tangku_agentos.cognitive_system.core.cognitive_state import CognitiveState
logger = logging.getLogger(__name__)

@dataclass
class Episode:
    episode_id: str; event: str; data: Any; metadata: Dict[str, Any]=field(default_factory=dict)
    timestamp: datetime=field(default_factory=datetime.utcnow)
    duration: float=0.0; location: str=""; participants: List[str]=field(default_factory=list)
    tags: List[str]=field(default_factory=list); importance: float=0.5

class EpisodicMemoryInterface:
    def __init__(self, config: "CognitiveConfig", state: "CognitiveState"):
        self._config=config; self._state=state; self._episodes: Dict[str, Episode]={}
        self._event_index: Dict[str, List[str]]= {}; self._time_index: Dict[str, List[str]]= {}
        self._tag_index: Dict[str, List[str]]= {}; self._metrics={"episodes":0,"retrievals":0}
    
    async def initialize(self)->None: pass
    async def start(self)->None: pass
    async def stop(self)->None: pass
    
    async def record_episode(
        self,
        event: str,
        data: Any,
        metadata: Optional[Dict[str, Any]]=None,
        timestamp: Optional[datetime]=None,
        duration: float=0.0,
        location: str="",
        participants: Optional[List[str]]=None,
        tags: Optional[List[str]]=None,
        importance: float=0.5
    ) -> str:
        """Record a new episode in memory."""
        import hashlib
        episode_id=f"ep_{hashlib.sha256(f'{event}:{timestamp or datetime.utcnow().isoformat()}'.encode()).hexdigest()[:16]}"
        
        episode=Episode(
            episode_id=episode_id,
            event=event,
            data=data,
            metadata=metadata or {},
            timestamp=timestamp or datetime.utcnow(),
            duration=duration,
            location=location,
            participants=participants or [],
            tags=tags or [],
            importance=importance
        )
        
        self._episodes[episode_id]=episode
        self._index_episode(episode)
        self._metrics["episodes"]+=1
        return episode_id
    
    def _index_episode(self, episode: Episode) -> None:
        """Index episode for fast retrieval."""
        # Event index
        if episode.event not in self._event_index:
            self._event_index[episode.event]=[]
        self._event_index[episode.event].append(episode.episode_id)
        
        # Time index (by date)
        date_str=episode.timestamp.strftime("%Y-%m-%d")
        if date_str not in self._time_index:
            self._time_index[date_str]=[]
        self._time_index[date_str].append(episode.episode_id)
        
        # Tag index
        for tag in episode.tags:
            if tag not in self._tag_index:
                self._tag_index[tag]=[]
            self._tag_index[tag].append(episode.episode_id)
    
    async def retrieve_episodes(
        self,
        query: Any,
        limit: int=10,
        start_time: Optional[datetime]=None,
        end_time: Optional[datetime]=None,
        tags: Optional[List[str]]=None,
        event: Optional[str]=None
    ) -> List[Episode]:
        """Retrieve episodes matching criteria."""
        query_str=str(query).lower()
        candidates=set()
        
        # Search by event
        if event:
            if event in self._event_index:
                candidates.update(self._event_index[event])
        
        # Search by time range
        if start_time or end_time:
            for date_str, episode_ids in self._time_index.items():
                try:
                    date=datetime.strptime(date_str, "%Y-%m-%d")
                    if start_time and date<start_time.date(): continue
                    if end_time and date>end_time.date(): continue
                    candidates.update(episode_ids)
                except: pass
        
        # Search by tags
        if tags:
            for tag in tags:
                if tag in self._tag_index:
                    if not candidates:
                        candidates.update(self._tag_index[tag])
                    else:
                        candidates.intersection_update(self._tag_index[tag])
        
        # If no candidates from filters, search all
        if not candidates:
            candidates=set(self._episodes.keys())
        
        # Filter by query
        results=[]
        for episode_id in candidates:
            if episode_id not in self._episodes: continue
            episode=self._episodes[episode_id]
            if query_str in str(episode.data).lower() or query_str in episode.event.lower():
                results.append(episode)
        
        # Sort by timestamp (most recent first)
        results.sort(key=lambda x: x.timestamp, reverse=True)
        self._metrics["retrievals"]+=1
        return results[:limit]
    
    async def get_episode(self, episode_id: str) -> Optional[Episode]:
        """Get a specific episode."""
        return self._episodes.get(episode_id)
    
    async def get_episodes_by_event(self, event: str, limit: int=10) -> List[Episode]:
        """Get episodes by event type."""
        if event not in self._event_index: return []
        episode_ids=self._event_index[event][:limit]
        return [self._episodes[eid] for eid in episode_ids if eid in self._episodes]
    
    async def get_episodes_by_date(self, date: datetime, limit: int=10) -> List[Episode]:
        """Get episodes by date."""
        date_str=date.strftime("%Y-%m-%d")
        if date_str not in self._time_index: return []
        episode_ids=self._time_index[date_str][:limit]
        return [self._episodes[eid] for eid in episode_ids if eid in self._episodes]
    
    async def get_episodes_by_tag(self, tag: str, limit: int=10) -> List[Episode]:
        """Get episodes by tag."""
        if tag not in self._tag_index: return []
        episode_ids=self._tag_index[tag][:limit]
        return [self._episodes[eid] for eid in episode_ids if eid in self._episodes]
    
    async def get_recent_episodes(self, limit: int=10) -> List[Episode]:
        """Get most recent episodes."""
        episodes=list(self._episodes.values())
        episodes.sort(key=lambda x: x.timestamp, reverse=True)
        return episodes[:limit]
    
    async def update_episode(self, episode_id: str, **kwargs) -> bool:
        """Update an episode."""
        if episode_id not in self._episodes: return False
        for key, value in kwargs.items():
            if hasattr(self._episodes[episode_id], key):
                setattr(self._episodes[episode_id], key, value)
        return True
    
    async def remove_episode(self, episode_id: str) -> bool:
        """Remove an episode."""
        if episode_id not in self._episodes: return False
        episode=self._episodes[episode_id]
        # Remove from indexes
        if episode.event in self._event_index:
            if episode_id in self._event_index[episode.event]:
                self._event_index[episode.event].remove(episode_id)
        date_str=episode.timestamp.strftime("%Y-%m-%d")
        if date_str in self._time_index:
            if episode_id in self._time_index[date_str]:
                self._time_index[date_str].remove(episode_id)
        for tag in episode.tags:
            if tag in self._tag_index:
                if episode_id in self._tag_index[tag]:
                    self._tag_index[tag].remove(episode_id)
        del self._episodes[episode_id]
        return True
    
    async def clear_episodes(self) -> None:
        """Clear all episodes."""
        self._episodes.clear()
        self._event_index.clear()
        self._time_index.clear()
        self._tag_index.clear()
    
    def get_metrics(self) -> Dict[str, Any]: return self._metrics.copy()
