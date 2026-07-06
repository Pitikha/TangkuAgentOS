from __future__ import annotations

import json

from .interfaces import MemorySerializer
from .models import MemoryRecord


class MemorySerializerImpl(MemorySerializer):
    """Serialize memory records to JSON and back."""

    def serialize(self, record: MemoryRecord) -> str:
        return json.dumps(record.__dict__)

    def deserialize(self, payload: str) -> MemoryRecord:
        data = json.loads(payload)
        return MemoryRecord(**data)
