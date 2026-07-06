from __future__ import annotations

from abc import ABC, abstractmethod
from threading import RLock
from typing import Any

from .constants import AgentState
from .exceptions import AgentLifecycleError, AgentStateError
from .interfaces import BaseAgent
from .messages import AgentMessage, AgentResult, AgentTask
from .types import AgentContext, AgentDescriptor


class Agent(BaseAgent, ABC):
    """Base Agent runtime abstraction."""

    def __init__(self, descriptor: AgentDescriptor, context: AgentContext) -> None:
        self._descriptor = descriptor
        self._context = context
        self._state = AgentState.INITIALIZING
        self._lock = RLock()

    @property
    def descriptor(self) -> AgentDescriptor:
        return self._descriptor

    @property
    def context(self) -> AgentContext:
        return self._context

    @property
    def state(self) -> AgentState:
        with self._lock:
            return self._state

    def initialize(self) -> None:
        with self._lock:
            if self._state not in {AgentState.INITIALIZING, AgentState.STOPPED, AgentState.FAILED}:
                raise AgentStateError(f"Cannot initialize from state {self._state}")
            self._transition_state(AgentState.READY)

    def activate(self) -> None:
        with self._lock:
            if self._state not in {AgentState.READY, AgentState.PAUSED, AgentState.SLEEPING, AgentState.RECOVERING}:
                raise AgentStateError(f"Cannot activate from state {self._state}")
            self._transition_state(AgentState.RUNNING)

    def pause(self) -> None:
        with self._lock:
            if self._state != AgentState.RUNNING:
                raise AgentStateError("Agent must be running to pause.")
            self._transition_state(AgentState.PAUSED)

    def resume(self) -> None:
        with self._lock:
            if self._state not in {AgentState.PAUSED, AgentState.SLEEPING}:
                raise AgentStateError("Agent must be paused or sleeping to resume.")
            self._transition_state(AgentState.RUNNING)

    def sleep(self) -> None:
        with self._lock:
            if self._state != AgentState.RUNNING:
                raise AgentStateError("Agent must be running to sleep.")
            self._transition_state(AgentState.SLEEPING)

    def stop(self) -> None:
        with self._lock:
            if self._state == AgentState.STOPPED:
                return
            self._transition_state(AgentState.STOPPED)

    def restart(self) -> None:
        with self._lock:
            if self._state == AgentState.RUNNING:
                self.stop()
            self._transition_state(AgentState.INITIALIZING)
            self._transition_state(AgentState.READY)
            self._transition_state(AgentState.RUNNING)

    def shutdown(self) -> None:
        with self._lock:
            self._transition_state(AgentState.SHUTTING_DOWN)
            self._transition_state(AgentState.STOPPED)

    def recover(self) -> None:
        with self._lock:
            if self._state != AgentState.FAILED:
                raise AgentStateError("Agent must be in failed state to recover.")
            self._transition_state(AgentState.RECOVERING)
            self._transition_state(AgentState.RUNNING)

    def send_message(self, message: AgentMessage) -> None:
        self.handle_message(message)

    def handle_task(self, task: AgentTask) -> AgentResult:
        return self.execute_task(task)

    @abstractmethod
    def handle_message(self, message: AgentMessage) -> None:
        """Process an incoming message."""

    @abstractmethod
    def execute_task(self, task: AgentTask) -> AgentResult:
        """Execute an agent task."""

    def _transition_state(self, target_state: AgentState) -> None:
        if self._state == AgentState.FAILED and target_state != AgentState.RECOVERING:
            raise AgentLifecycleError("Agent is in failed state and cannot transition except to recovering.")
        self._state = target_state
