from __future__ import annotations

from threading import RLock
from typing import Any, Dict


class DocumentationGenerator:
    def __init__(self) -> None:
        self._lock = RLock()

    def generate(self, name: str, content: dict[str, Any]) -> dict[str, Any]:
        with self._lock:
            return {"name": name, **content}


class APIReferenceGenerator:
    def __init__(self) -> None:
        self._lock = RLock()

    def generate(self, api_name: str) -> dict[str, Any]:
        with self._lock:
            return {"api_name": api_name}


class SDKDocumentationManager:
    def __init__(self) -> None:
        self._lock = RLock()

    def generate(self, sdk_id: str) -> dict[str, Any]:
        with self._lock:
            return {"sdk_id": sdk_id}


class ExtensionTemplateGenerator:
    def __init__(self) -> None:
        self._lock = RLock()

    def generate(self, extension_id: str) -> dict[str, Any]:
        with self._lock:
            return {"extension_id": extension_id}
