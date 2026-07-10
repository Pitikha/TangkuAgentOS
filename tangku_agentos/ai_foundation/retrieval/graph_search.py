"""
Graph Search for TangkuAgentOS AI Foundation Framework.

Performs graph-based search on knowledge graphs.
"""
from typing import Any, Optional, Dict, List, Set
from dataclasses import dataclass, field
import logging
from collections import deque

logger = logging.getLogger(__name__)


@dataclass
class GraphNode:
    """Represents a node in a knowledge graph."""
    node_id: str
    label: str
    properties: Dict[str, Any] = field(default_factory=dict)
    neighbors: List[str] = field(default_factory=list)


@dataclass
class GraphSearchResult:
    """Result of a graph search operation."""
    query: str
    results: List[GraphNode]
    paths: List[List[str]]
    metadata: Dict[str, Any] = field(default_factory=dict)


class GraphSearcher:
    """Performs graph-based search for TangkuAgentOS.

    This class provides methods for searching knowledge graphs,
    including breadth-first, depth-first, and shortest-path searches.
    """

    def __init__(self):
        """Initialize the GraphSearcher."""
        self._graph: Dict[str, GraphNode] = {}
        logger.info("GraphSearcher initialized.")

    def add_node(self, node_id: str, label: str, properties: Optional[Dict[str, Any]] = None) -> None:
        """Add a node to the graph.

        Args:
            node_id: The ID of the node.
            label: The label of the node.
            properties: Optional properties for the node.
        """
        self._graph[node_id] = GraphNode(
            node_id=node_id,
            label=label,
            properties=properties or {},
        )
        logger.debug(f"Added node: {node_id}")

    def add_edge(self, source_id: str, target_id: str) -> None:
        """Add an edge between two nodes.

        Args:
            source_id: The ID of the source node.
            target_id: The ID of the target node.
        """
        if source_id in self._graph and target_id in self._graph:
            self._graph[source_id].neighbors.append(target_id)
            logger.debug(f"Added edge: {source_id} -> {target_id}")

    async def breadth_first_search(
        self,
        start_node_id: str,
        max_depth: int = 3,
    ) -> GraphSearchResult:
        """Perform breadth-first search from a starting node.

        Args:
            start_node_id: The ID of the node to start the search from.
            max_depth: Maximum depth to search.

        Returns:
            GraphSearchResult containing the search results.
        """
        if start_node_id not in self._graph:
            return GraphSearchResult(
                query=start_node_id,
                results=[],
                paths=[],
                metadata={"error": f"Node {start_node_id} not found"},
            )

        visited = set()
        queue = deque([(start_node_id, 0, [start_node_id])])
        results = []
        paths = []

        while queue:
            node_id, depth, path = queue.popleft()
            if node_id in visited or depth > max_depth:
                continue
            visited.add(node_id)
            node = self._graph[node_id]
            results.append(node)
            paths.append(path)

            for neighbor_id in node.neighbors:
                if neighbor_id not in visited:
                    queue.append((neighbor_id, depth + 1, path + [neighbor_id]))

        logger.info(f"Performed BFS from node: {start_node_id}")
        return GraphSearchResult(
            query=start_node_id,
            results=results,
            paths=paths,
            metadata={"max_depth": max_depth, "nodes_visited": len(visited)},
        )

    async def depth_first_search(
        self,
        start_node_id: str,
        max_depth: int = 3,
    ) -> GraphSearchResult:
        """Perform depth-first search from a starting node.

        Args:
            start_node_id: The ID of the node to start the search from.
            max_depth: Maximum depth to search.

        Returns:
            GraphSearchResult containing the search results.
        """
        if start_node_id not in self._graph:
            return GraphSearchResult(
                query=start_node_id,
                results=[],
                paths=[],
                metadata={"error": f"Node {start_node_id} not found"},
            )

        visited = set()
        stack = [(start_node_id, 0, [start_node_id])]
        results = []
        paths = []

        while stack:
            node_id, depth, path = stack.pop()
            if node_id in visited or depth > max_depth:
                continue
            visited.add(node_id)
            node = self._graph[node_id]
            results.append(node)
            paths.append(path)

            for neighbor_id in reversed(node.neighbors):
                if neighbor_id not in visited:
                    stack.append((neighbor_id, depth + 1, path + [neighbor_id]))

        logger.info(f"Performed DFS from node: {start_node_id}")
        return GraphSearchResult(
            query=start_node_id,
            results=results,
            paths=paths,
            metadata={"max_depth": max_depth, "nodes_visited": len(visited)},
        )

    async def shortest_path(
        self,
        start_node_id: str,
        end_node_id: str,
    ) -> GraphSearchResult:
        """Find the shortest path between two nodes.

        Args:
            start_node_id: The ID of the starting node.
            end_node_id: The ID of the target node.

        Returns:
            GraphSearchResult containing the shortest path.
        """
        if start_node_id not in self._graph or end_node_id not in self._graph:
            return GraphSearchResult(
                query=f"{start_node_id} -> {end_node_id}",
                results=[],
                paths=[],
                metadata={"error": "Start or end node not found"},
            )

        queue = deque([(start_node_id, [start_node_id])])
        visited = set()

        while queue:
            node_id, path = queue.popleft()
            if node_id == end_node_id:
                results = [self._graph[nid] for nid in path]
                logger.info(f"Found shortest path from {start_node_id} to {end_node_id}")
                return GraphSearchResult(
                    query=f"{start_node_id} -> {end_node_id}",
                    results=results,
                    paths=[path],
                    metadata={"path_length": len(path)},
                )
            if node_id in visited:
                continue
            visited.add(node_id)
            for neighbor_id in self._graph[node_id].neighbors:
                if neighbor_id not in visited:
                    queue.append((neighbor_id, path + [neighbor_id]))

        return GraphSearchResult(
            query=f"{start_node_id} -> {end_node_id}",
            results=[],
            paths=[],
            metadata={"error": "No path found"},
        )

    async def search_by_label(
        self,
        label: str,
        max_depth: int = 2,
    ) -> GraphSearchResult:
        """Search for nodes with a specific label.

        Args:
            label: The label to search for.
            max_depth: Maximum depth to search from each matching node.

        Returns:
            GraphSearchResult containing nodes with the specified label.
        """
        start_nodes = [
            node_id for node_id, node in self._graph.items()
            if node.label == label
        ]

        all_results = []
        all_paths = []

        for start_node_id in start_nodes:
            bfs_result = await self.breadth_first_search(start_node_id, max_depth)
            all_results.extend(bfs_result.results)
            all_paths.extend(bfs_result.paths)

        logger.info(f"Found {len(all_results)} nodes with label: {label}")
        return GraphSearchResult(
            query=label,
            results=all_results,
            paths=all_paths,
            metadata={"label": label, "nodes_found": len(all_results)},
        )
