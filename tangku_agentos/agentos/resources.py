from __future__ import annotations

from threading import RLock
from typing import Dict

from .exceptions import AgentRuntimeError
from .types import AgentResourceAllocation, AgentResourceBudget, AgentMetadata


class AgentResourceManager:
    """Tracks agent resource budgets and allocations."""

    def __init__(self) -> None:
        self._budgets: Dict[str, AgentResourceBudget] = {}
        self._allocations: Dict[str, AgentResourceAllocation] = {}
        self._lock = RLock()

    def set_budget(self, agent_id: str, budget: AgentResourceBudget) -> None:
        with self._lock:
            self._budgets[agent_id] = budget

    def get_budget(self, agent_id: str) -> AgentResourceBudget:
        with self._lock:
            budget = self._budgets.get(agent_id)
            if budget is None:
                raise AgentRuntimeError(f"Resource budget not found for agent: {agent_id}")
            return budget

    def request_allocation(self, allocation: AgentResourceAllocation) -> None:
        with self._lock:
            budget = self.get_budget(allocation.agent_id)
            reserved = self._reserved_resources(allocation.agent_id)
            if (
                reserved.cpu_reserved + allocation.cpu_reserved > budget.cpu_budget
                or reserved.memory_reserved + allocation.memory_reserved > budget.memory_budget
                or reserved.token_reserved + allocation.token_reserved > budget.token_budget
                or reserved.time_reserved_seconds + allocation.time_reserved_seconds > budget.time_budget_seconds
            ):
                raise AgentRuntimeError(f"Insufficient resources available for agent: {allocation.agent_id}")
            self._allocations[allocation.allocation_id] = allocation

    def release_allocation(self, allocation_id: str) -> None:
        with self._lock:
            if allocation_id in self._allocations:
                del self._allocations[allocation_id]

    def get_allocation(self, allocation_id: str) -> AgentResourceAllocation:
        with self._lock:
            allocation = self._allocations.get(allocation_id)
            if allocation is None:
                raise AgentRuntimeError(f"Allocation not found: {allocation_id}")
            return allocation

    def list_allocations(self, agent_id: str | None = None) -> list[AgentResourceAllocation]:
        with self._lock:
            allocations = list(self._allocations.values())
            if agent_id is None:
                return allocations
            return [allocation for allocation in allocations if allocation.agent_id == agent_id]

    def _reserved_resources(self, agent_id: str) -> AgentResourceAllocation:
        allocations = [allocation for allocation in self._allocations.values() if allocation.agent_id == agent_id]
        return AgentResourceAllocation(
            allocation_id="reserved",
            agent_id=agent_id,
            cpu_reserved=sum(allocation.cpu_reserved for allocation in allocations),
            memory_reserved=sum(allocation.memory_reserved for allocation in allocations),
            token_reserved=sum(allocation.token_reserved for allocation in allocations),
            time_reserved_seconds=sum(allocation.time_reserved_seconds for allocation in allocations),
            metadata={},
        )

    def usage_report(self, agent_id: str) -> dict[str, float | int]:
        reserved = self._reserved_resources(agent_id)
        return {
            "cpu_reserved": reserved.cpu_reserved,
            "memory_reserved": reserved.memory_reserved,
            "token_reserved": reserved.token_reserved,
            "time_reserved_seconds": reserved.time_reserved_seconds,
        }
