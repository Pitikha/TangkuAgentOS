from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(slots=True)
class SDKArtifact:
    name: str
    kind: str
    metadata: dict[str, Any] | None = None


class TangkuDeveloperSDK:
    """A lightweight SDK for creating agents, tools, plugins, and workflows."""

    def __init__(self) -> None:
        self._artifacts: list[SDKArtifact] = []

    def create_agent(self, name: str) -> SDKArtifact:
        artifact = SDKArtifact(name=name, kind="agent", metadata={"provider": "default"})
        self._artifacts.append(artifact)
        return artifact

    def create_tool(self, name: str) -> SDKArtifact:
        artifact = SDKArtifact(name=name, kind="tool", metadata={"capabilities": []})
        self._artifacts.append(artifact)
        return artifact

    def create_plugin(self, name: str) -> SDKArtifact:
        artifact = SDKArtifact(name=name, kind="plugin", metadata={"version": "1.0.0"})
        self._artifacts.append(artifact)
        return artifact

    def create_workflow(self, name: str) -> SDKArtifact:
        artifact = SDKArtifact(name=name, kind="workflow", metadata={"steps": []})
        self._artifacts.append(artifact)
        return artifact

    def list_artifacts(self) -> list[SDKArtifact]:
        return list(self._artifacts)
