from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Protocol


class Detector(Protocol):
    def detect(self, path: str) -> list[str]:
        ...


@dataclass
class DetectorRegistration:
    name: str
    detector: Detector
    kind: str = 'generic'


class DetectionRegistry:
    """Registry for language, framework, builder, and package manager detectors."""

    def __init__(self) -> None:
        self._detectors: dict[str, list[DetectorRegistration]] = {}

    def register(self, kind: str, name: str, detector: Detector) -> None:
        self._detectors.setdefault(kind, []).append(DetectorRegistration(name=name, detector=detector, kind=kind))

    def detect(self, kind: str, path: str) -> list[str]:
        results: list[str] = []
        for registration in self._detectors.get(kind, []):
            results.extend(registration.detector.detect(path))
        return results


class LanguageDetector:
    """Detect languages from file names or directories."""

    def detect(self, path: str) -> list[str]:
        lowered = path.lower()
        if 'py' in lowered:
            return ['python']
        if 'js' in lowered or 'ts' in lowered:
            return ['javascript']
        return []


class PackageManagerDetector:
    """Detect package manager clues in a path."""

    def detect(self, path: str) -> list[str]:
        if 'requirements' in path.lower() or 'pyproject' in path.lower():
            return ['pip']
        if 'package.json' in path.lower():
            return ['npm']
        return []


class BuildSystemDetector:
    """Detect build-system clues in a path."""

    def detect(self, path: str) -> list[str]:
        if 'setup.py' in path.lower() or 'pyproject.toml' in path.lower():
            return ['setuptools']
        if 'package.json' in path.lower():
            return ['npm']
        return []


class FrameworkDetector:
    """Detect framework clues in a path."""

    def detect(self, path: str) -> list[str]:
        if 'django' in path.lower():
            return ['django']
        if 'flask' in path.lower():
            return ['flask']
        if 'fastapi' in path.lower():
            return ['fastapi']
        return []
