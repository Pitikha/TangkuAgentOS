"""
AI Cognitive System - Cognitive Loop

This module implements the continuous thinking cycle for cognitive agents.
The cognitive loop is the default execution cycle for every intelligent agent.
"""

from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from typing import Any, Callable, Dict, List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from tangku_agentos.cognitive_system.core.cognitive_state import CognitiveState, CognitiveStage
    from tangku_agentos.cognitive_system.core.cognitive_config import CognitiveConfig

logger = logging.getLogger(__name__)


class LoopMode(Enum):
    CONTINUOUS = auto()
    SINGLE = auto()
    STEP = auto()
    PAUSED = auto()
    STOPPED = auto()


class LoopStatus(Enum):
    IDLE = auto()
    RUNNING = auto()
    PAUSED = auto()
    STOPPED = auto()
    ERROR = auto()
    COMPLETED = auto()


@dataclass
class LoopMetrics:
    loop_count: int = 0
    stage_times: Dict[str, float] = field(default_factory=dict)
    total_time: float = 0.0
    last_loop_time: float = 0.0
    last_stage_time: float = 0.0
    input_count: int = 0
    output_count: int = 0
    error_count: int = 0
    last_error: Optional[str] = None
    last_error_time: Optional[datetime] = None

    def record_loop_start(self) -> None:
        self.loop_count += 1

    def record_loop_end(self, duration: float) -> None:
        self.total_time += duration
        self.last_loop_time = duration

    def record_stage_time(self, stage: str, duration: float) -> None:
        if stage not in self.stage_times:
            self.stage_times[stage] = 0.0
        self.stage_times[stage] += duration
        self.last_stage_time = duration

    def record_input(self) -> None:
        self.input_count += 1

    def record_output(self) -> None:
        self.output_count += 1

    def record_error(self, error: str) -> None:
        self.error_count += 1
        self.last_error = error
        self.last_error_time = datetime.utcnow()

    def get_metrics(self) -> Dict[str, Any]:
        return {
            "loop_count": self.loop_count,
            "stage_times": self.stage_times.copy(),
            "total_time": self.total_time,
            "last_loop_time": self.last_loop_time,
            "last_stage_time": self.last_stage_time,
            "input_count": self.input_count,
            "output_count": self.output_count,
            "error_count": self.error_count,
            "last_error": self.last_error,
            "last_error_time": self.last_error_time.isoformat() if self.last_error_time else None,
        }

    def reset(self) -> None:
        self.loop_count = 0
        self.stage_times.clear()
        self.total_time = 0.0
        self.last_loop_time = 0.0
        self.last_stage_time = 0.0
        self.input_count = 0
        self.output_count = 0
        self.error_count = 0
        self.last_error = None
        self.last_error_time = None


class CognitiveLoop:
    """The continuous thinking cycle for cognitive agents."""

    def __init__(
        self,
        state: Optional["CognitiveState"] = None,
        config: Optional["CognitiveConfig"] = None,
    ):
        self._state = state
        self._config = config
        self._mode = LoopMode.SINGLE
        self._status = LoopStatus.IDLE
        self._running = False
        self._paused = False
        self._stopped = True
        self._metrics = LoopMetrics()
        self._stage_handlers: Dict[str, Callable[[], Any]] = {}
        self._loop_task: Optional[asyncio.Task] = None
        self._lock = asyncio.Lock()
        self._input_queue: asyncio.Queue = asyncio.Queue()
        self._output_queue: asyncio.Queue = asyncio.Queue()
        logger.info("CognitiveLoop initialized")

    @property
    def state(self) -> "CognitiveState":
        if self._state is None:
            from tangku_agentos.cognitive_system.core.cognitive_state import CognitiveState
            self._state = CognitiveState(self._config)
        return self._state

    @property
    def config(self) -> Optional["CognitiveConfig"]:
        return self._config

    @property
    def mode(self) -> LoopMode:
        return self._mode

    @property
    def status(self) -> LoopStatus:
        return self._status

    @property
    def is_running(self) -> bool:
        return self._running and not self._paused

    @property
    def metrics(self) -> LoopMetrics:
        return self._metrics

    def register_stage_handler(self, stage: str, handler: Callable[[], Any]) -> None:
        self._stage_handlers[stage] = handler

    async def initialize(self) -> None:
        if self._config:
            self._state.config = self._config
        await self._state.initialize()
        self._status = LoopStatus.IDLE
        self._stopped = False
        self._register_default_handlers()
        logger.info("CognitiveLoop initialized")

    def _register_default_handlers(self) -> None:
        for stage in ["PERCEIVE", "UNDERSTAND_CONTEXT", "RETRIEVE_MEMORY", "RETRIEVE_KNOWLEDGE",
                      "REASON", "PLAN", "EVALUATE_OPTIONS", "SELECT_TOOLS", "EXECUTE",
                      "OBSERVE_RESULTS", "REFLECT", "LEARN", "UPDATE_MEMORY", "CONTINUE"]:
            if stage not in self._stage_handlers:
                self._stage_handlers[stage] = self._default_stage_handler

    async def _default_stage_handler(self) -> Any:
        stage = self.state.stage.name
        logger.debug(f"Default handler for stage: {stage}")
        return {"stage": stage, "status": "completed"}

    async def start(self, mode: LoopMode = LoopMode.SINGLE) -> None:
        async with self._lock:
            if self._running:
                return
            self._mode = mode
            self._running = True
            self._paused = False
            self._stopped = False
            self._status = LoopStatus.RUNNING
            if mode == LoopMode.CONTINUOUS:
                self._loop_task = asyncio.create_task(self._loop_continuous())
            logger.info(f"CognitiveLoop started in {mode.name} mode")

    async def stop(self) -> None:
        async with self._lock:
            if not self._running:
                return
            self._running = False
            self._stopped = True
            self._status = LoopStatus.STOPPED
            if self._loop_task:
                self._loop_task.cancel()
                try:
                    await self._loop_task
                except asyncio.CancelledError:
                    pass
                self._loop_task = None
            logger.info("CognitiveLoop stopped")

    async def pause(self) -> None:
        async with self._lock:
            if not self._running:
                return
            self._paused = True
            self._status = LoopStatus.PAUSED
            logger.info("CognitiveLoop paused")

    async def resume(self) -> None:
        async with self._lock:
            if not self._paused:
                return
            self._paused = False
            self._status = LoopStatus.RUNNING
            logger.info("CognitiveLoop resumed")

    async def _loop_continuous(self) -> None:
        try:
            while self._running and not self._stopped:
                if self._paused:
                    await asyncio.sleep(0.1)
                    continue
                try:
                    input_data = await asyncio.wait_for(self._input_queue.get(), timeout=1.0)
                    self._metrics.record_input()
                    output = await self._process_input(input_data)
                    await self._output_queue.put(output)
                    self._metrics.record_output()
                except asyncio.TimeoutError:
                    continue
        except asyncio.CancelledError:
            pass

    async def process(self, input_data: Any, timeout: Optional[float] = None) -> Any:
        async with self._lock:
            if not self._running:
                await self.start(LoopMode.SINGLE)
            self._state.context.current_input = input_data
            self._metrics.record_input()
            try:
                output = await asyncio.wait_for(self._process_input(input_data), timeout=timeout)
                self._metrics.record_output()
                return output
            except asyncio.TimeoutError:
                error = f"Cognitive loop timeout after {timeout} seconds"
                self._metrics.record_error(error)
                raise
            except Exception as e:
                self._metrics.record_error(str(e))
                raise

    async def _process_input(self, input_data: Any) -> Any:
        loop_start_time = time.time()
        self._metrics.record_loop_start()
        try:
            for stage in self._get_loop_sequence():
                stage_start_time = time.time()
                await self._state.set_stage(stage)
                try:
                    handler = self._stage_handlers.get(stage.name, self._default_stage_handler)
                    result = await handler()
                    if stage.name == "PERCEIVE":
                        self._state.context.current_input = result
                    elif stage.name == "EXECUTE":
                        self._state.context.current_output = result
                except Exception as e:
                    self._metrics.record_error(str(e))
                    raise
                stage_duration = time.time() - stage_start_time
                self._metrics.record_stage_time(stage.name, stage_duration)
            output = self._state.context.current_output
            loop_duration = time.time() - loop_start_time
            self._metrics.record_loop_end(loop_duration)
            return output
        except Exception as e:
            self._metrics.record_error(str(e))
            self._status = LoopStatus.ERROR
            raise

    def _get_loop_sequence(self) -> List[Any]:
        from tangku_agentos.cognitive_system.core.cognitive_state import CognitiveStage
        return [
            CognitiveStage.PERCEIVE,
            CognitiveStage.UNDERSTAND_CONTEXT,
            CognitiveStage.RETRIEVE_MEMORY,
            CognitiveStage.RETRIEVE_KNOWLEDGE,
            CognitiveStage.REASON,
            CognitiveStage.PLAN,
            CognitiveStage.EVALUATE_OPTIONS,
            CognitiveStage.SELECT_TOOLS,
            CognitiveStage.EXECUTE,
            CognitiveStage.OBSERVE_RESULTS,
            CognitiveStage.REFLECT,
            CognitiveStage.LEARN,
            CognitiveStage.UPDATE_MEMORY,
            CognitiveStage.CONTINUE,
        ]

    async def step(self) -> Any:
        if not self._running:
            await self.start(LoopMode.STEP)
        if self._paused:
            return None
        current_stage = self._state.stage
        stage_start_time = time.time()
        try:
            handler = self._stage_handlers.get(current_stage.name, self._default_stage_handler)
            result = await handler()
            stage_duration = time.time() - stage_start_time
            self._metrics.record_stage_time(current_stage.name, stage_duration)
            return result
        except Exception as e:
            self._metrics.record_error(str(e))
            raise

    async def enqueue_input(self, input_data: Any) -> None:
        await self._input_queue.put(input_data)

    async def dequeue_output(self) -> Any:
        return await self._output_queue.get()

    def get_status_info(self) -> Dict[str, Any]:
        return {
            "mode": self._mode.name,
            "status": self._status.name,
            "running": self._running,
            "paused": self._paused,
            "stopped": self._stopped,
            "metrics": self._metrics.get_metrics(),
        }

    def reset(self) -> None:
        self._status = LoopStatus.IDLE
        self._running = False
        self._paused = False
        self._stopped = True
        self._metrics.reset()
        self._state.reset()
        logger.info("CognitiveLoop reset")

    def __repr__(self) -> str:
        return f"CognitiveLoop(mode={self._mode.name}, status={self._status.name}, loops={self._metrics.loop_count})"
