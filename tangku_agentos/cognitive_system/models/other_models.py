"""
AI Cognitive System - Other Models

This module contains additional models for the cognitive system:
- CognitiveContext: Context for cognitive processes
- MemoryEntry: Memory entry model
- KnowledgeQuery: Knowledge query model
- ReasoningResult: Reasoning result model
- PlanningResult: Planning result model
- DecisionResult: Decision result model
- ActionPlan: Action plan model
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Union


# CognitiveContext is already defined in cognitive_state.py
# We'll create a simplified version here for the models package

@dataclass
class MemoryEntry:
    """
    Represents an entry in the cognitive memory system.
    
    Attributes:
        memory_id: Unique identifier for the memory.
        content: The content of the memory.
        type: Type of memory (working, short_term, long_term, episodic, semantic).
        metadata: Additional metadata.
        created_at: When the memory was created.
        updated_at: When the memory was last updated.
        accessed_at: When the memory was last accessed.
        access_count: Number of times the memory has been accessed.
        relevance: Relevance score.
        confidence: Confidence in the memory.
        tags: Tags for categorization.
        relationships: Relationships to other memories.
    """

    memory_id: str
    content: Any
    type: str = "working"
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    accessed_at: datetime = field(default_factory=datetime.utcnow)
    access_count: int = 0
    relevance: float = 1.0
    confidence: float = 1.0
    tags: Set[str] = field(default_factory=set)
    relationships: Dict[str, List[str]] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "memory_id": self.memory_id,
            "content": str(self.content)[:200] + "..." if len(str(self.content)) > 200 else str(self.content),
            "type": self.type,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "accessed_at": self.accessed_at.isoformat(),
            "access_count": self.access_count,
            "relevance": self.relevance,
            "confidence": self.confidence,
            "tags": list(self.tags),
            "relationships": self.relationships,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MemoryEntry":
        """Create from dictionary."""
        return cls(
            memory_id=data.get("memory_id", ""),
            content=data.get("content", ""),
            type=data.get("type", "working"),
            metadata=data.get("metadata", {}),
            created_at=datetime.fromisoformat(data.get("created_at", datetime.utcnow().isoformat())),
            updated_at=datetime.fromisoformat(data.get("updated_at", datetime.utcnow().isoformat())),
            accessed_at=datetime.fromisoformat(data.get("accessed_at", datetime.utcnow().isoformat())),
            access_count=data.get("access_count", 0),
            relevance=data.get("relevance", 1.0),
            confidence=data.get("confidence", 1.0),
            tags=set(data.get("tags", [])),
            relationships=data.get("relationships", {}),
        )


@dataclass
class KnowledgeQuery:
    """
    Represents a query to the knowledge system.
    
    Attributes:
        query_id: Unique identifier for the query.
        query: The query string.
        type: Type of query (search, retrieve, update, delete).
        parameters: Query parameters.
        filters: Filters for the query.
        limit: Maximum number of results.
        offset: Offset for pagination.
        sort_by: Field to sort by.
        sort_order: Sort order (asc, desc).
        timestamp: When the query was made.
        metadata: Additional metadata.
    """

    query_id: str = ""
    query: str = ""
    type: str = "search"
    parameters: Dict[str, Any] = field(default_factory=dict)
    filters: Dict[str, Any] = field(default_factory=dict)
    limit: int = 10
    offset: int = 0
    sort_by: str = "relevance"
    sort_order: str = "desc"
    timestamp: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "query_id": self.query_id,
            "query": self.query,
            "type": self.type,
            "parameters": self.parameters,
            "filters": self.filters,
            "limit": self.limit,
            "offset": self.offset,
            "sort_by": self.sort_by,
            "sort_order": self.sort_order,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "KnowledgeQuery":
        """Create from dictionary."""
        return cls(
            query_id=data.get("query_id", ""),
            query=data.get("query", ""),
            type=data.get("type", "search"),
            parameters=data.get("parameters", {}),
            filters=data.get("filters", {}),
            limit=data.get("limit", 10),
            offset=data.get("offset", 0),
            sort_by=data.get("sort_by", "relevance"),
            sort_order=data.get("sort_order", "desc"),
            timestamp=datetime.fromisoformat(data.get("timestamp", datetime.utcnow().isoformat())),
            metadata=data.get("metadata", {}),
        )


@dataclass
class ReasoningResult:
    """
    Represents the result of a reasoning operation.
    
    Attributes:
        result_id: Unique identifier for the result.
        reasoning_type: Type of reasoning performed.
        input: The input that was reasoned about.
        output: The output of the reasoning.
        steps: Steps taken during reasoning.
        intermediate_results: Intermediate results.
        confidence: Confidence in the result.
        sources: Sources used in reasoning.
        timestamp: When the reasoning was performed.
        duration: Time taken for reasoning.
        metadata: Additional metadata.
    """

    result_id: str = ""
    reasoning_type: str = ""
    input: Any = None
    output: Any = None
    steps: List[Dict[str, Any]] = field(default_factory=list)
    intermediate_results: List[Any] = field(default_factory=list)
    confidence: float = 0.0
    sources: List[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.utcnow)
    duration: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "result_id": self.result_id,
            "reasoning_type": self.reasoning_type,
            "input": str(self.input)[:100] + "..." if self.input and len(str(self.input)) > 100 else str(self.input),
            "output": str(self.output)[:100] + "..." if self.output and len(str(self.output)) > 100 else str(self.output),
            "steps": self.steps,
            "intermediate_results": [str(r)[:50] + "..." if len(str(r)) > 50 else str(r) for r in self.intermediate_results],
            "confidence": self.confidence,
            "sources": self.sources,
            "timestamp": self.timestamp.isoformat(),
            "duration": self.duration,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ReasoningResult":
        """Create from dictionary."""
        return cls(
            result_id=data.get("result_id", ""),
            reasoning_type=data.get("reasoning_type", ""),
            input=data.get("input"),
            output=data.get("output"),
            steps=data.get("steps", []),
            intermediate_results=data.get("intermediate_results", []),
            confidence=data.get("confidence", 0.0),
            sources=data.get("sources", []),
            timestamp=datetime.fromisoformat(data.get("timestamp", datetime.utcnow().isoformat())),
            duration=data.get("duration", 0.0),
            metadata=data.get("metadata", {}),
        )


@dataclass
class PlanningResult:
    """
    Represents the result of a planning operation.
    
    Attributes:
        plan_id: Unique identifier for the plan.
        goal: The goal being planned for.
        steps: List of steps in the plan.
        dependencies: Dependencies between steps.
        resources: Resources required for the plan.
        timeline: Timeline for the plan.
        confidence: Confidence in the plan.
        feasibility: Feasibility score.
        risk: Risk assessment.
        cost: Estimated cost.
        timestamp: When the plan was created.
        duration: Time taken for planning.
        metadata: Additional metadata.
    """

    plan_id: str = ""
    goal: str = ""
    steps: List[Dict[str, Any]] = field(default_factory=list)
    dependencies: Dict[str, List[str]] = field(default_factory=dict)
    resources: Dict[str, Any] = field(default_factory=dict)
    timeline: Dict[str, Any] = field(default_factory=dict)
    confidence: float = 0.0
    feasibility: float = 0.0
    risk: float = 0.0
    cost: float = 0.0
    timestamp: datetime = field(default_factory=datetime.utcnow)
    duration: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "plan_id": self.plan_id,
            "goal": self.goal,
            "steps": self.steps,
            "dependencies": self.dependencies,
            "resources": self.resources,
            "timeline": self.timeline,
            "confidence": self.confidence,
            "feasibility": self.feasibility,
            "risk": self.risk,
            "cost": self.cost,
            "timestamp": self.timestamp.isoformat(),
            "duration": self.duration,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PlanningResult":
        """Create from dictionary."""
        return cls(
            plan_id=data.get("plan_id", ""),
            goal=data.get("goal", ""),
            steps=data.get("steps", []),
            dependencies=data.get("dependencies", {}),
            resources=data.get("resources", {}),
            timeline=data.get("timeline", {}),
            confidence=data.get("confidence", 0.0),
            feasibility=data.get("feasibility", 0.0),
            risk=data.get("risk", 0.0),
            cost=data.get("cost", 0.0),
            timestamp=datetime.fromisoformat(data.get("timestamp", datetime.utcnow().isoformat())),
            duration=data.get("duration", 0.0),
            metadata=data.get("metadata", {}),
        )


@dataclass
class DecisionResult:
    """
    Represents the result of a decision operation.
    
    Attributes:
        decision_id: Unique identifier for the decision.
        options: List of options considered.
        selected_option: The selected option.
        reasoning: Reasoning for the decision.
        confidence: Confidence in the decision.
        utility: Utility score of the decision.
        risk: Risk assessment.
        cost: Estimated cost.
        constraints: Constraints considered.
        permissions: Permissions checked.
        resources: Resources required.
        timestamp: When the decision was made.
        duration: Time taken for decision making.
        metadata: Additional metadata.
    """

    decision_id: str = ""
    options: List[Any] = field(default_factory=list)
    selected_option: Any = None
    reasoning: str = ""
    confidence: float = 0.0
    utility: float = 0.0
    risk: float = 0.0
    cost: float = 0.0
    constraints: List[str] = field(default_factory=list)
    permissions: List[str] = field(default_factory=list)
    resources: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow)
    duration: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "decision_id": self.decision_id,
            "options": [str(o)[:50] + "..." if len(str(o)) > 50 else str(o) for o in self.options],
            "selected_option": str(self.selected_option)[:100] + "..." if self.selected_option and len(str(self.selected_option)) > 100 else str(self.selected_option),
            "reasoning": self.reasoning[:200] + "..." if len(self.reasoning) > 200 else self.reasoning,
            "confidence": self.confidence,
            "utility": self.utility,
            "risk": self.risk,
            "cost": self.cost,
            "constraints": self.constraints,
            "permissions": self.permissions,
            "resources": self.resources,
            "timestamp": self.timestamp.isoformat(),
            "duration": self.duration,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DecisionResult":
        """Create from dictionary."""
        return cls(
            decision_id=data.get("decision_id", ""),
            options=data.get("options", []),
            selected_option=data.get("selected_option"),
            reasoning=data.get("reasoning", ""),
            confidence=data.get("confidence", 0.0),
            utility=data.get("utility", 0.0),
            risk=data.get("risk", 0.0),
            cost=data.get("cost", 0.0),
            constraints=data.get("constraints", []),
            permissions=data.get("permissions", []),
            resources=data.get("resources", {}),
            timestamp=datetime.fromisoformat(data.get("timestamp", datetime.utcnow().isoformat())),
            duration=data.get("duration", 0.0),
            metadata=data.get("metadata", {}),
        )


@dataclass
class ActionPlan:
    """
    Represents an action plan for execution.
    
    Attributes:
        plan_id: Unique identifier for the plan.
        goal: The goal of the plan.
        actions: List of actions to execute.
        dependencies: Dependencies between actions.
        resources: Resources required.
        constraints: Constraints to consider.
        permissions: Permissions required.
        estimated_duration: Estimated duration for execution.
        estimated_cost: Estimated cost.
        confidence: Confidence in the plan.
        risk: Risk assessment.
        priority: Priority of the plan.
        timestamp: When the plan was created.
        metadata: Additional metadata.
    """

    plan_id: str = ""
    goal: str = ""
    actions: List[Dict[str, Any]] = field(default_factory=list)
    dependencies: Dict[str, List[str]] = field(default_factory=dict)
    resources: Dict[str, Any] = field(default_factory=dict)
    constraints: List[str] = field(default_factory=list)
    permissions: List[str] = field(default_factory=list)
    estimated_duration: float = 0.0
    estimated_cost: float = 0.0
    confidence: float = 0.0
    risk: float = 0.0
    priority: int = 1
    timestamp: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "plan_id": self.plan_id,
            "goal": self.goal,
            "actions": self.actions,
            "dependencies": self.dependencies,
            "resources": self.resources,
            "constraints": self.constraints,
            "permissions": self.permissions,
            "estimated_duration": self.estimated_duration,
            "estimated_cost": self.estimated_cost,
            "confidence": self.confidence,
            "risk": self.risk,
            "priority": self.priority,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ActionPlan":
        """Create from dictionary."""
        return cls(
            plan_id=data.get("plan_id", ""),
            goal=data.get("goal", ""),
            actions=data.get("actions", []),
            dependencies=data.get("dependencies", {}),
            resources=data.get("resources", {}),
            constraints=data.get("constraints", []),
            permissions=data.get("permissions", []),
            estimated_duration=data.get("estimated_duration", 0.0),
            estimated_cost=data.get("estimated_cost", 0.0),
            confidence=data.get("confidence", 0.0),
            risk=data.get("risk", 0.0),
            priority=data.get("priority", 1),
            timestamp=datetime.fromisoformat(data.get("timestamp", datetime.utcnow().isoformat())),
            metadata=data.get("metadata", {}),
        )


# Update the models __init__.py to include these
# This is handled by the main __init__.py in the models package
