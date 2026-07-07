from __future__ import annotations

from threading import RLock
from typing import Any, Dict

from .interfaces import GraphManagerInterface
from .models import KnowledgeGraphEdge, KnowledgeGraphNode, KnowledgeRelationship


class KnowledgeGraphManager(GraphManagerInterface):
    """In-process knowledge graph manager for semantic relationships."""

    def __init__(self) -> None:
        self._nodes: Dict[str, KnowledgeGraphNode] = {}
        self._edges: Dict[str, KnowledgeGraphEdge] = {}
        self._lock = RLock()
        self._relationships: Dict[str, KnowledgeRelationship] = {}

    def register_node(self, node: KnowledgeGraphNode) -> None:
        with self._lock:
            self._nodes[node.node_id] = node

    def register_edge(self, edge: KnowledgeGraphEdge) -> None:
        with self._lock:
            self._edges[edge.edge_id] = edge

    def add_node(self, node_id: str, label: str, metadata: dict[str, Any] | None = None) -> None:
        with self._lock:
            self._nodes[node_id] = KnowledgeGraphNode(node_id=node_id, label=label, metadata=metadata or {})

    def add_edge(self, source_node_id: str, target_node_id: str, relationship: str, metadata: dict[str, Any] | None = None) -> None:
        with self._lock:
            edge_id = f"{source_node_id}->{target_node_id}:{relationship}"
            self._edges[edge_id] = KnowledgeGraphEdge(edge_id=edge_id, source_node_id=source_node_id, target_node_id=target_node_id, relationship=relationship, metadata=metadata or {})
            self._relationships[edge_id] = KnowledgeRelationship(relationship_id=edge_id, source_entity_id=source_node_id, target_entity_id=target_node_id, relationship_type=relationship, metadata=metadata or {})

    def outgoing_relationships(self, entity_id: str) -> list[KnowledgeRelationship]:
        with self._lock:
            return [relationship for relationship in self._relationships.values() if relationship.source_entity_id == entity_id]

    def incoming_relationships(self, entity_id: str) -> list[KnowledgeRelationship]:
        with self._lock:
            return [relationship for relationship in self._relationships.values() if relationship.target_entity_id == entity_id]

    def traverse(self, entity_id: str, max_depth: int = 1) -> list[KnowledgeRelationship]:
        with self._lock:
            visited: set[str] = set()
            results: list[KnowledgeRelationship] = []
            queue: list[tuple[str, int]] = [(entity_id, 0)]
            while queue:
                current, depth = queue.pop()
                if depth > max_depth or current in visited:
                    continue
                visited.add(current)
                for relationship in self._relationships.values():
                    if relationship.source_entity_id == current:
                        results.append(relationship)
                        queue.append((relationship.target_entity_id, depth + 1))
            return results

    def neighborhood(self, entity_id: str) -> dict[str, list[KnowledgeRelationship]]:
        return {"incoming": self.incoming_relationships(entity_id), "outgoing": self.outgoing_relationships(entity_id)}

    def statistics(self) -> dict[str, int]:
        with self._lock:
            return {"node_count": len(self._nodes), "edge_count": len(self._edges), "relationship_count": len(self._relationships)}

    def snapshot(self) -> dict[str, Any]:
        with self._lock:
            return {
                "nodes": {node_id: {"label": node.label, "metadata": dict(node.metadata)} for node_id, node in self._nodes.items()},
                "edges": {edge_id: {"source": edge.source_node_id, "target": edge.target_node_id, "relationship": edge.relationship, "metadata": dict(edge.metadata)} for edge_id, edge in self._edges.items()},
            }
