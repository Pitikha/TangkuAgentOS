from __future__ import annotations

from threading import RLock
from typing import Any
from uuid import uuid4

from tangku_agentos.core_runtime.event_bus import EventBus
from tangku_agentos.memory_engine import MemoryEntry, MemoryManager, MemoryMetadata, MemoryRecord, MemoryType

from .models import ReasoningContext, ReasoningDecision, ReasoningMode, ReasoningSession, ReasoningStep, ReasoningTrace


class ReasoningManager:
    """Coordinate reasoning sessions, contexts, and decision-making."""

    def __init__(
        self,
        db_path: str | None = None,
        event_bus: EventBus | None = None,
        security_manager: Any | None = None,
        observability_manager: Any | None = None,
    ) -> None:
        self._contexts: dict[str, ReasoningContext] = {}
        self._sessions: dict[str, ReasoningSession] = {}
        self._traces: dict[str, ReasoningTrace] = {}
        self._decisions: dict[str, list[ReasoningDecision]] = {}
        self._lock = RLock()
        self._memory: MemoryManager = MemoryManager(db_path) if db_path else MemoryManager()
        self._event_bus = event_bus or EventBus()
        self._security_manager = security_manager
        self._observability_manager = observability_manager
        self._hydrate_from_memory()

    def create_context(
        self, context_id: str, subject_id: str, *, mode: ReasoningMode = ReasoningMode.SEQUENTIAL, metadata: dict[str, object] | None = None
    ) -> ReasoningContext:
        self._ensure_permission("reasoning.create")
        context = ReasoningContext(context_id=context_id, subject_id=subject_id, mode=mode, metadata=dict(metadata or {}))
        with self._lock:
            self._contexts[context_id] = context
        self._persist_context(context)
        self._emit_reasoning_event("reasoning_started", {"context_id": context_id, "subject_id": subject_id})
        self._audit("reasoning.context_created", context_id, {"subject_id": subject_id})
        return context

    def create_session(self, context_id: str, *, metadata: dict[str, object] | None = None) -> ReasoningSession:
        self._ensure_permission("reasoning.create")
        session = ReasoningSession(session_id=str(uuid4()), context_id=context_id, metadata=dict(metadata or {}))
        with self._lock:
            self._sessions[session.session_id] = session
            if session.session_id not in self._traces:
                self._traces[session.session_id] = ReasoningTrace(trace_id=session.session_id, steps=(), metadata={})
        self._persist_session(session)
        self._emit_reasoning_event("reasoning_started", {"session_id": session.session_id, "context_id": context_id})
        self._audit("reasoning.session_created", session.session_id, {"context_id": context_id})
        return session

    def create_reasoning_session(self, context_id: str, *, metadata: dict[str, object] | None = None) -> ReasoningSession:
        return self.create_session(context_id, metadata=metadata)

    def get_session(self, session_id: str) -> ReasoningSession | None:
        with self._lock:
            return self._sessions.get(session_id)

    def list_sessions(self) -> list[ReasoningSession]:
        with self._lock:
            return list(self._sessions.values())

    def reason(
        self, session_id: str, query: str, available_tools: list[str] | None = None, context_data: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        self._ensure_permission("reasoning.execute")
        with self._lock:
            session = self._sessions.get(session_id)
            if session is None:
                return {"error": "Session not found"}

            available_tools = available_tools or []
            selection = available_tools[0] if available_tools else None
            decision_id = str(uuid4())
            assumptions = [f"Query: {query}", "We should use the most relevant available tool when possible"]
            observations = [f"Available tools: {', '.join(available_tools) if available_tools else 'none'}"]
            conclusion = f"Selected {selection or 'no tool'} for the requested reasoning task"
            decision = ReasoningDecision(
                decision_id=decision_id,
                trace_id=session_id,
                decision_type="tool_selection",
                selected=selection or "none",
                alternatives=available_tools[1:] if len(available_tools) > 1 else [],
                confidence=0.95,
                reasoning=conclusion,
                metadata={"query": query, "context": context_data or {}, "assumptions": assumptions, "observations": observations, "conclusion": conclusion},
            )

            if session_id not in self._decisions:
                self._decisions[session_id] = []
            self._decisions[session_id].append(decision)

            step = ReasoningStep(step_id=str(uuid4()), content=query, metadata={"decision": decision_id})
            trace = self._traces.get(session_id)
            if trace is None:
                trace = ReasoningTrace(trace_id=session_id, steps=(), metadata={})
            updated_trace = ReasoningTrace(
                trace_id=trace.trace_id,
                steps=tuple(list(trace.steps) + [step]),
                metadata={
                    **trace.metadata,
                    "assumptions": assumptions,
                    "observations": observations,
                    "decisions": [decision.decision_id],
                    "alternatives": decision.alternatives,
                    "conclusion": conclusion,
                },
            )
            self._traces[session_id] = updated_trace
            self._persist_trace(updated_trace)

        self._persist_decision(decision)
        self._emit_reasoning_event("decision_created", {"session_id": session_id, "decision_id": decision_id, "selected_tool": selection})
        self._emit_reasoning_event("reasoning_completed", {"session_id": session_id, "decision_id": decision_id, "selected_tool": selection})
        self._audit("reasoning.decision_created", session_id, {"decision_id": decision_id, "selected": selection})
        return {"selected_tool": selection, "decision_id": decision_id, "reasoning": {"assumptions": assumptions, "observations": observations, "conclusion": conclusion}}

    def decide(
        self,
        session_id: str,
        task: str,
        available_tools: list[str] | None = None,
        available_providers: list[str] | None = None,
        available_models: list[str] | None = None,
        context_data: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        if available_providers:
            return self.decide_provider(session_id, task, available_providers=available_providers, context_data=context_data)
        if available_models:
            return self.select_model(session_id, available_providers[0] if available_providers else "default", task, available_models)
        return self.reason(session_id, task, available_tools=available_tools, context_data=context_data)

    def decide_provider(
        self, session_id: str, task: str, available_providers: list[str] | None = None, context_data: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        self._ensure_permission("reasoning.execute")
        available_providers = available_providers or []
        provider = available_providers[0] if available_providers else "default"
        decision_id = str(uuid4())
        decision = ReasoningDecision(
            decision_id=decision_id,
            trace_id=session_id,
            decision_type="provider_routing",
            selected=provider,
            alternatives=available_providers[1:] if len(available_providers) > 1 else [],
            confidence=0.90,
            reasoning=f"Selected provider for {task}",
            metadata={"task": task, "context": context_data or {}},
        )
        with self._lock:
            if session_id not in self._decisions:
                self._decisions[session_id] = []
            self._decisions[session_id].append(decision)
        self._persist_decision(decision)
        self._emit_reasoning_event("decision_created", {"session_id": session_id, "decision_id": decision_id, "provider": provider})
        self._audit("reasoning.provider_decision", session_id, {"provider": provider})
        return {"provider": provider, "decision_id": decision_id}

    def select_model(
        self, session_id: str, provider: str, task_type: str, available_models: list[str] | None = None
    ) -> dict[str, Any]:
        self._ensure_permission("reasoning.execute")
        available_models = available_models or []
        model = available_models[0] if available_models else "default"
        decision_id = str(uuid4())
        decision = ReasoningDecision(
            decision_id=decision_id,
            trace_id=session_id,
            decision_type="model_selection",
            selected=model,
            alternatives=available_models[1:] if len(available_models) > 1 else [],
            confidence=0.88,
            reasoning=f"Selected {model} for {task_type}",
            metadata={"provider": provider, "task_type": task_type},
        )
        with self._lock:
            if session_id not in self._decisions:
                self._decisions[session_id] = []
            self._decisions[session_id].append(decision)
        self._persist_decision(decision)
        self._emit_reasoning_event("decision_created", {"session_id": session_id, "decision_id": decision_id, "model": model})
        self._audit("reasoning.model_decision", session_id, {"model": model})
        return {"model": model, "decision_id": decision_id}

    def explain(self, session_id: str, query: str, context_data: dict[str, Any] | None = None) -> dict[str, Any]:
        self._ensure_permission("reasoning.execute")
        explanation = {
            "session_id": session_id,
            "query": query,
            "context": context_data or {},
            "summary": "Reasoning is guided by the current context, memory, and available tools.",
        }
        self._emit_reasoning_event("reasoning_updated", {"session_id": session_id, "summary": explanation["summary"]})
        return explanation

    def evaluate(self, session_id: str, decision: dict[str, Any], outcome: dict[str, Any]) -> dict[str, Any]:
        self._ensure_permission("reasoning.execute")
        score = 0.95 if outcome.get("success") else 0.5
        self._emit_reasoning_event("reasoning_completed", {"session_id": session_id, "score": score})
        self._audit("reasoning.evaluated", session_id, {"outcome": outcome, "score": score})
        return {"score": score, "metadata": {"decision": decision, "outcome": outcome}}

    def get_reasoning_trace(self, session_id: str) -> ReasoningTrace:
        with self._lock:
            trace = self._traces.get(session_id)
            if trace is None:
                trace = ReasoningTrace(trace_id=session_id, steps=(), metadata={})
                self._traces[session_id] = trace
            return trace

    def restore_session(self, session_id: str) -> ReasoningSession | None:
        self._ensure_permission("reasoning.update")
        with self._lock:
            session = self._sessions.get(session_id)
            if session is None:
                return None
            restored_session = ReasoningSession(
                session_id=session.session_id,
                context_id=session.context_id,
                metadata={k: v for k, v in session.metadata.items() if k != "archived"},
            )
            self._sessions[session_id] = restored_session
        self._persist_session(restored_session)
        self._emit_reasoning_event("reasoning_restored", {"session_id": session_id})
        self._audit("reasoning.session_restored", session_id, {})
        return restored_session

    def archive_session(self, session_id: str) -> None:
        self._ensure_permission("reasoning.update")
        with self._lock:
            session = self._sessions.get(session_id)
            if session is None:
                return
            archived_session = ReasoningSession(
                session_id=session.session_id, context_id=session.context_id, metadata={**session.metadata, "archived": True}
            )
            self._sessions[session_id] = archived_session
        self._persist_session(archived_session)
        self._emit_reasoning_event("reasoning_updated", {"session_id": session_id, "archived": True})
        self._audit("reasoning.session_archived", session_id, {})

    def _persist_context(self, context: ReasoningContext) -> None:
        payload = {
            "context_id": context.context_id,
            "subject_id": context.subject_id,
            "mode": context.mode.value,
            "metadata": context.metadata,
        }
        metadata = MemoryMetadata(namespace="reasoning", created_by="ReasoningManager", tags=["context", context.context_id])
        record = MemoryRecord(
            record_id=context.context_id,
            entries=[MemoryEntry(entry_id=str(uuid4()), type=MemoryType.WORKING, content={"kind": "reasoning_context", "data": payload}, metadata=metadata)],
            namespace="reasoning",
            metadata=metadata,
        )
        self._memory.store(context.context_id, record)

    def _persist_session(self, session: ReasoningSession) -> None:
        payload = {
            "session_id": session.session_id,
            "context_id": session.context_id,
            "metadata": session.metadata,
        }
        metadata = MemoryMetadata(namespace="reasoning", created_by="ReasoningManager", tags=["session", session.session_id])
        record = MemoryRecord(
            record_id=session.session_id,
            entries=[MemoryEntry(entry_id=str(uuid4()), type=MemoryType.WORKING, content={"kind": "reasoning_session", "data": payload}, metadata=metadata)],
            namespace="reasoning",
            metadata=metadata,
        )
        self._memory.store(session.session_id, record)

    def _persist_decision(self, decision: ReasoningDecision) -> None:
        payload = {
            "decision_id": decision.decision_id,
            "trace_id": decision.trace_id,
            "decision_type": decision.decision_type,
            "selected": decision.selected,
            "alternatives": decision.alternatives,
            "confidence": decision.confidence,
            "reasoning": decision.reasoning,
            "metadata": decision.metadata,
        }
        metadata = MemoryMetadata(namespace="reasoning", created_by="ReasoningManager", tags=["decision", decision.trace_id, decision.decision_type])
        record = MemoryRecord(
            record_id=decision.decision_id,
            entries=[MemoryEntry(entry_id=str(uuid4()), type=MemoryType.WORKING, content={"kind": "reasoning_decision", "data": payload}, metadata=metadata)],
            namespace="reasoning",
            metadata=metadata,
        )
        self._memory.store(decision.decision_id, record)

    def _persist_trace(self, trace: ReasoningTrace) -> None:
        payload = {
            "trace_id": trace.trace_id,
            "steps": [{"step_id": s.step_id, "content": s.content, "metadata": s.metadata} for s in trace.steps],
            "metadata": trace.metadata,
        }
        metadata = MemoryMetadata(namespace="reasoning", created_by="ReasoningManager", tags=["trace", trace.trace_id])
        record = MemoryRecord(
            record_id=trace.trace_id,
            entries=[MemoryEntry(entry_id=str(uuid4()), type=MemoryType.WORKING, content={"kind": "reasoning_trace", "data": payload}, metadata=metadata)],
            namespace="reasoning",
            metadata=metadata,
        )
        self._memory.store(trace.trace_id, record)

    def _hydrate_from_memory(self) -> None:
        records = self._memory.list_with_filter("reasoning")
        for record in records:
            try:
                payload = self._extract_payload(record)
                if not payload:
                    continue
                kind = payload.get("kind") or record.metadata.attributes.get("kind")
                if kind == "reasoning_context":
                    context = ReasoningContext(
                        context_id=payload["context_id"],
                        subject_id=payload["subject_id"],
                        mode=ReasoningMode(payload.get("mode", "sequential")),
                        metadata=payload.get("metadata", {}),
                    )
                    with self._lock:
                        self._contexts[context.context_id] = context
                elif kind == "reasoning_session":
                    session = ReasoningSession(
                        session_id=payload["session_id"], context_id=payload["context_id"], metadata=payload.get("metadata", {})
                    )
                    with self._lock:
                        self._sessions[session.session_id] = session
            except Exception:
                pass

    def _extract_payload(self, record: MemoryRecord) -> dict[str, Any]:
        for entry in record.entries:
            if isinstance(entry.content, dict) and entry.content.get("data") is not None:
                return entry.content.get("data", {})
        return {}

    def _emit_reasoning_event(self, event_name: str, payload: dict[str, Any]) -> None:
        aliases = {
            "reasoning_started": "reasoning.started",
            "reasoning_completed": "reasoning.completed",
            "reasoning_updated": "reasoning.updated",
            "decision_created": "reasoning.decision_created",
            "reasoning_restored": "reasoning.restored",
        }
        self._emit_event(event_name, payload)
        self._emit_event(aliases.get(event_name, event_name), payload)

    def _emit_event(self, event_name: str, payload: dict[str, Any]) -> None:
        try:
            self._event_bus.publish(event_name, payload)
        except Exception:
            pass
        try:
            if self._observability_manager:
                self._observability_manager.event_recorder.record({"event": event_name, "payload": payload})
        except Exception:
            pass

    def _audit(self, event: str, identity: str, metadata: dict[str, Any]) -> None:
        try:
            if self._security_manager:
                audit_mgr = self._security_manager.get_audit_manager()
                audit_mgr.record_event(event, identity, self._sanitize_payload(metadata))
        except Exception:
            pass

    def _ensure_permission(self, permission_id: str) -> None:
        try:
            if self._security_manager:
                perm_mgr = self._security_manager.get_permission_manager()
                if not perm_mgr.has_permission("system", permission_id):
                    raise PermissionError(f"Permission denied: {permission_id}")
        except PermissionError:
            raise
        except Exception:
            pass

    def _sanitize_payload(self, metadata: dict[str, Any]) -> dict[str, Any]:
        sanitized = {}
        for key, value in metadata.items():
            if key.lower() in {"password", "token", "secret", "api_key"}:
                sanitized[key] = "[redacted]"
            elif isinstance(value, dict):
                sanitized[key] = self._sanitize_payload(value)
            else:
                sanitized[key] = value
        return sanitized
