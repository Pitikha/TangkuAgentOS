"""AI Cognitive System - Perception Engine"""
from __future__ import annotations
import asyncio, hashlib, logging, re
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from typing import Any, Dict, List, Optional, Tuple, TYPE_CHECKING
if TYPE_CHECKING:
    from tangku_agentos.cognitive_system.core.cognitive_config import CognitiveConfig
    from tangku_agentos.cognitive_system.core.cognitive_state import CognitiveState
logger = logging.getLogger(__name__)

class InputCategory(Enum):
    TEXT=auto(); AUDIO=auto(); VISUAL=auto(); DOCUMENT=auto(); CODE=auto()
    STRUCTURED=auto(); EVENT=auto(); SYSTEM=auto(); MULTI_MODAL=auto()

@dataclass
class PerceivedData:
    perceived_id: str; original_input: Any; processed_data: Any; type: str; category: InputCategory
    features: Dict[str, Any]=field(default_factory=dict); metadata: Dict[str, Any]=field(default_factory=dict)
    timestamp: datetime=field(default_factory=datetime.utcnow)
    processing_time: float=0.0; confidence: float=1.0

class PerceptionEngine:
    def __init__(self, config: "CognitiveConfig", state: "CognitiveState"):
        self._config=config; self._state=state; self._initialized=False; self._started=False
        self._lock=asyncio.Lock(); self._metrics={"inputs_processed":0,"errors":0}
    
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
    
    async def process(self, input_data: Any, input_type: Optional[str]=None) -> PerceivedData:
        import time
        from tangku_agentos.cognitive_system.exceptions import PerceptionError
        start_time=time.time()
        try:
            actual_type=input_type or self._infer_type(input_data)
            processed, category=await self._process(input_data, actual_type)
            features=self._extract_features(processed, actual_type, category)
            return PerceivedData(
                perceived_id=self._generate_id(input_data, actual_type),
                original_input=input_data, processed_data=processed, type=actual_type,
                category=category, features=features, processing_time=time.time()-start_time
            )
        except Exception as e:
            self._metrics["errors"]+=1
            raise PerceptionError(f"Failed to process input: {e}") from e
    
    def _infer_type(self, data: Any)->str:
        if isinstance(data, str): return "text"
        if isinstance(data, bytes): return "document"
        if isinstance(data, dict): return data.get("type","structured").lower()
        if isinstance(data, list): return "multi_modal"
        return "structured"
    
    def _generate_id(self, data: Any, typ: str)->str:
        s=str(data)[:100]
        return f"perceived_{hashlib.sha256(f'{typ}:{s}:{datetime.utcnow().isoformat()}'.encode()).hexdigest()[:16]}"
    
    async def _process(self, data: Any, typ: str)->Tuple[Any, InputCategory]:
        if typ=="text":
            content=data["content"] if isinstance(data,dict) else str(data)
            processed=self._normalize(content)
            return processed, InputCategory.CODE if self._is_code(processed) else InputCategory.TEXT
        if typ in ("voice","audio"): return data.get("transcript","[Voice transcribed]"), InputCategory.TEXT
        if typ=="image": return data.get("description","[Image analyzed]"), InputCategory.VISUAL
        if typ=="document":
            if isinstance(data,dict) and "content" in data: return data["content"], InputCategory.DOCUMENT
            return f"[Document: {data.get('path','')}]", InputCategory.DOCUMENT
        if typ=="repository":
            n=data.get("name","Repository"); u=data.get("url","")
            return f"Repository: {n}" + (f" ({u})" if u else ""), InputCategory.STRUCTURED
        if typ=="terminal_output":
            c=data.get("command",""); o=data.get("output",""); e=data.get("exit_code",0)
            return f"Command: {c}\nExit: {e}\nOutput: {o}", InputCategory.TEXT
        if typ=="runtime_event":
            return {"event_type":data.get("event_type","unknown"),"runtime_id":data.get("runtime_id",""),"payload":data.get("payload",{})}, InputCategory.EVENT
        if typ=="system_event":
            return {"event_type":data.get("event_type","unknown"),"source":data.get("source",""),"payload":data.get("payload",{})}, InputCategory.SYSTEM
        if typ=="workspace_change":
            return {"change_type":data.get("change_type","unknown"),"path":data.get("path",""),"content":data.get("content","")}, InputCategory.STRUCTURED
        if typ=="structured": return data if isinstance(data,dict) else {"data":data}, InputCategory.STRUCTURED
        if typ=="multi_modal" and isinstance(data,list):
            processed=[]
            for item in data:
                it, _=await self._process(item, item.get("type","unknown"))
                processed.append({"type":item.get("type","unknown"),"data":it})
            return processed, InputCategory.MULTI_MODAL
        return str(data), InputCategory.STRUCTURED
    
    def _normalize(self, text: str)->str:
        return re.sub(r'\s+', ' ', text.strip().replace('\r\n','\n').replace('\r','\n'))
    
    def _is_code(self, text: str)->bool:
        return bool(re.search(r'def\s+\w+|class\s+\w+|import\s+|function\s+\w+', text))
    
    def _extract_features(self, data: Any, typ: str, category: InputCategory)->Dict[str, Any]:
        if typ=="text":
            if not isinstance(data, str): data=str(data)
            w=data.split(); s=[x for x in re.split(r'[.!?]+', data) if x.strip()]
            return {"length":len(data),"word_count":len(w),"sentence_count":len(s),
                    "language":"en","is_code":self._is_code(data),"category":category.value}
        if typ=="code":
            if not isinstance(data, str): data=str(data)
            l=data.split('\n')
            return {"language":self._detect_lang(data),
                    "lines":len([x for x in l if x.strip() and not x.strip().startswith('#')]),
                    "functions":len(re.findall(r'def\s+\w+', data)),"classes":len(re.findall(r'class\s+\w+', data)),
                    "category":category.value}
        return {"category":category.value}
    
    def _detect_lang(self, code: str)->str:
        if 'def ' in code: return "python"
        if 'function ' in code: return "javascript"
        if 'public ' in code: return "java"
        if '#include' in code: return "cpp"
        return "unknown"
    
    def get_metrics(self)->Dict[str, Any]: return self._metrics.copy()
